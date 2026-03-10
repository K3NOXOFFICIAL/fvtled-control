"""BLE communication module for FVTLED devices."""
from __future__ import annotations

import logging
from typing import Callable

from bleak import BleakClient, BleakError

from .const import (
    CHAR_UUID_NOTIFY,
    CHAR_UUID_NOTIFY_ALT,
    CHAR_UUID_WRITE,
    CHAR_UUID_WRITE_ALT,
    CMD_COLOR_PREFIX,
    CMD_COLOR_SUFFIX,
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CMD_STATUS_REQUEST,
    CONNECTION_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


def _build_rgb_command(red: int, green: int, blue: int) -> bytes:
    """Build the BLE command bytes for setting an RGB color."""
    payload = bytes([CMD_COLOR_PREFIX, red & 0xFF, green & 0xFF, blue & 0xFF]) + CMD_COLOR_SUFFIX
    checksum = sum(payload) & 0xFF
    return payload + bytes([checksum])


def _build_power_command(on: bool) -> bytes:
    """Build the BLE command bytes for power on/off."""
    payload = CMD_POWER_ON if on else CMD_POWER_OFF
    checksum = sum(payload) & 0xFF
    return payload + bytes([checksum])


class FVTLEDBLEDevice:
    """Represents a BLE connection to an FVTLED device."""

    def __init__(self, address: str) -> None:
        """Initialize with the device Bluetooth address."""
        self._address = address
        self._client: BleakClient | None = None
        self._write_char: str | None = None
        self._notify_char: str | None = None
        self._state_callbacks: list[Callable[[dict], None]] = []
        self._is_on: bool = False
        self._rgb: tuple[int, int, int] = (255, 255, 255)

    @property
    def address(self) -> str:
        """Return the device Bluetooth address."""
        return self._address

    @property
    def is_on(self) -> bool:
        """Return whether the light is currently on."""
        return self._is_on

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the current RGB color."""
        return self._rgb

    def register_callback(self, callback: Callable[[dict], None]) -> None:
        """Register a callback to be called on state changes."""
        self._state_callbacks.append(callback)

    def _notify_callbacks(self) -> None:
        """Call all registered state-change callbacks."""
        state = {"is_on": self._is_on, "rgb": self._rgb}
        for cb in self._state_callbacks:
            cb(state)

    async def connect(self) -> bool:
        """Establish a BLE connection to the device.

        Returns True if the connection succeeds, False otherwise.
        """
        try:
            self._client = BleakClient(self._address, timeout=CONNECTION_TIMEOUT)
            await self._client.connect()
            await self._resolve_characteristics()
            if self._notify_char:
                await self._client.start_notify(self._notify_char, self._on_notification)
            _LOGGER.debug("Connected to FVTLED device %s", self._address)
            return True
        except BleakError as err:
            _LOGGER.error("Failed to connect to %s: %s", self._address, err)
            self._client = None
            return False

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        if self._client and self._client.is_connected:
            try:
                await self._client.disconnect()
            except BleakError as err:
                _LOGGER.debug("Error during disconnect from %s: %s", self._address, err)
        self._client = None

    async def _resolve_characteristics(self) -> None:
        """Detect the correct write and notify characteristic UUIDs."""
        if self._client is None:
            return
        services = self._client.services
        # Prefer the primary service (0xFFFF), fall back to secondary (0xFE00)
        for write_uuid, notify_uuid in [
            (CHAR_UUID_WRITE, CHAR_UUID_NOTIFY),
            (CHAR_UUID_WRITE_ALT, CHAR_UUID_NOTIFY_ALT),
        ]:
            if services.get_characteristic(write_uuid) is not None:
                self._write_char = write_uuid
                self._notify_char = notify_uuid
                _LOGGER.debug(
                    "Using write=%s notify=%s for device %s",
                    write_uuid,
                    notify_uuid,
                    self._address,
                )
                return
        _LOGGER.warning("No known write characteristic found on device %s", self._address)

    def _on_notification(self, _sender: int, data: bytearray) -> None:
        """Handle an incoming BLE notification from the device.

        The FVTLED status notification payload is at least 7 bytes:
          byte 2  – power state (0x23 = on, 0x24 = off)
          bytes 6-8 – RGB values (present when payload length >= 9)
        """
        _LOGGER.debug("Notification from %s: %s", self._address, data.hex())
        if len(data) >= 7:
            self._is_on = data[2] == 0x23
        if len(data) >= 9:
            self._rgb = (int(data[6]), int(data[7]), int(data[8]))
        if len(data) >= 7:
            self._notify_callbacks()

    async def _write(self, command: bytes) -> bool:
        """Write a command to the device's write characteristic.

        Returns True on success, False on failure.
        """
        if not self._client or not self._client.is_connected:
            _LOGGER.warning("Cannot write – not connected to %s", self._address)
            return False
        if not self._write_char:
            _LOGGER.warning("Cannot write – no write characteristic resolved for %s", self._address)
            return False
        try:
            await self._client.write_gatt_char(self._write_char, command, response=False)
            return True
        except BleakError as err:
            _LOGGER.error("Write failed on %s: %s", self._address, err)
            return False

    async def turn_on(self) -> bool:
        """Send the power-on command.

        Returns True on success, False on failure.
        """
        success = await self._write(_build_power_command(True))
        if success:
            self._is_on = True
            self._notify_callbacks()
        return success

    async def turn_off(self) -> bool:
        """Send the power-off command.

        Returns True on success, False on failure.
        """
        success = await self._write(_build_power_command(False))
        if success:
            self._is_on = False
            self._notify_callbacks()
        return success

    async def set_rgb(self, red: int, green: int, blue: int) -> bool:
        """Send an RGB color command.

        Returns True on success, False on failure.
        """
        command = _build_rgb_command(red, green, blue)
        success = await self._write(command)
        if success:
            self._rgb = (red, green, blue)
            self._notify_callbacks()
        return success

    async def request_status(self) -> bool:
        """Request the current device status.

        Returns True on success, False on failure.
        """
        return await self._write(CMD_STATUS_REQUEST)

    async def __aenter__(self) -> "FVTLEDBLEDevice":
        """Support use as an async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Disconnect when exiting the async context manager."""
        await self.disconnect()

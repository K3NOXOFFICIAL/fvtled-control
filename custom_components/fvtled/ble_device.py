"""BLE protocol implementation for FVTLED ARZ-2100 RGB controller."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice

from .const import (
    BLE_CHAR_NOTIFY,
    BLE_CHAR_NOTIFY_2,
    BLE_CHAR_WRITE,
    BLE_CHAR_WRITE_2,
    CMD_COLOR_PREFIX,
    CMD_COLOR_SUFFIX,
    CMD_GET_STATE,
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CONNECT_TIMEOUT,
    NOTIFY_RESPONSE_DELAY,
)

_LOGGER = logging.getLogger(__name__)


def _build_color_command(red: int, green: int, blue: int) -> bytes:
    """Build the RGB color set command packet."""
    return bytes([CMD_COLOR_PREFIX, red, green, blue]) + CMD_COLOR_SUFFIX


def _build_brightness_command(brightness: int) -> bytes:
    """Build a warm-white brightness command (0-255)."""
    return bytes([0x56, 0x00, 0x00, 0x00, brightness, 0x0F, 0xAA])


def _checksum(data: bytes) -> int:
    """Simple additive checksum used by some device responses."""
    return sum(data) & 0xFF


class FvtledBleDevice:
    """Manages BLE connection and protocol for FVTLED ARZ-2100."""

    def __init__(self, ble_device: BLEDevice) -> None:
        """Initialise with a discovered BLE device."""
        self._ble_device = ble_device
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()

        # Cached state
        self.is_on: bool = False
        self.red: int = 255
        self.green: int = 255
        self.blue: int = 255
        self.brightness: int = 255

    @property
    def address(self) -> str:
        """Return BLE MAC address."""
        return self._ble_device.address

    @property
    def name(self) -> str:
        """Return BLE device name."""
        return self._ble_device.name or self._ble_device.address

    async def _ensure_connected(self) -> BleakClient:
        """Ensure we have a live connection, reconnecting if necessary."""
        if self._client and self._client.is_connected:
            return self._client
        _LOGGER.debug("Connecting to %s", self.address)
        client = BleakClient(
            self._ble_device, timeout=CONNECT_TIMEOUT, disconnected_callback=self._on_disconnect
        )
        await client.connect()
        self._client = client
        _LOGGER.debug("Connected to %s", self.address)
        return client

    def _on_disconnect(self, client: BleakClient) -> None:
        """Handle unexpected disconnection."""
        _LOGGER.warning("Disconnected from %s", self.address)
        self._client = None

    async def _write(self, data: bytes) -> None:
        """Write bytes to the primary write characteristic."""
        client = await self._ensure_connected()
        # Try the primary write characteristic; fall back to secondary.
        for char_uuid in (BLE_CHAR_WRITE, BLE_CHAR_WRITE_2):
            try:
                await client.write_gatt_char(char_uuid, data, response=True)
                _LOGGER.debug("Wrote %s to %s", data.hex(), char_uuid)
                return
            except (BleakError, KeyError):
                _LOGGER.debug("Characteristic %s not available, trying next", char_uuid)
        raise BleakError(f"No writable characteristic found on {self.address}")

    async def async_turn_on(self) -> None:
        """Send power-on command."""
        async with self._lock:
            await self._write(CMD_POWER_ON)
            self.is_on = True

    async def async_turn_off(self) -> None:
        """Send power-off command."""
        async with self._lock:
            await self._write(CMD_POWER_OFF)
            self.is_on = False

    async def async_set_color(self, red: int, green: int, blue: int) -> None:
        """Set RGB color (0-255 each channel)."""
        async with self._lock:
            cmd = _build_color_command(red, green, blue)
            await self._write(cmd)
            self.red = red
            self.green = green
            self.blue = blue
            self.is_on = True

    async def async_set_brightness(self, brightness: int) -> None:
        """Set warm-white brightness (0-255)."""
        async with self._lock:
            cmd = _build_brightness_command(brightness)
            await self._write(cmd)
            self.brightness = brightness
            self.is_on = brightness > 0

    async def async_update(self) -> None:
        """Query device state and update cached values."""
        async with self._lock:
            try:
                client = await self._ensure_connected()
                await client.write_gatt_char(BLE_CHAR_WRITE, CMD_GET_STATE, response=True)
                # Allow time for notify response
                await asyncio.sleep(NOTIFY_RESPONSE_DELAY)
                # State is updated via the notification callback registered in
                # async_start_notify; if not available we keep cached values.
            except BleakError as err:
                _LOGGER.warning("Failed to update state from %s: %s", self.address, err)

    def _handle_notify(self, _sender: Any, data: bytes) -> None:
        """Handle BLE notification with device state response."""
        _LOGGER.debug("Notify from %s: %s", self.address, data.hex())
        # Response format (Magic Home-like): 0x81 <mode> <power> R G B W ...
        if len(data) >= 7 and data[0] == 0x81:
            self.is_on = data[2] == 0x23
            self.red = data[3]
            self.green = data[4] if len(data) > 4 else 0
            self.blue = data[5] if len(data) > 5 else 0

    async def async_start_notify(self) -> None:
        """Subscribe to BLE notifications for state updates."""
        try:
            client = await self._ensure_connected()
            for char_uuid in (BLE_CHAR_NOTIFY, BLE_CHAR_NOTIFY_2):
                try:
                    await client.start_notify(char_uuid, self._handle_notify)
                    _LOGGER.debug("Subscribed to notifications on %s", char_uuid)
                    return
                except (BleakError, KeyError):
                    _LOGGER.debug("Notify characteristic %s not available", char_uuid)
        except BleakError as err:
            _LOGGER.warning("Could not subscribe to notifications: %s", err)

    async def async_disconnect(self) -> None:
        """Cleanly disconnect from the device."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            self._client = None

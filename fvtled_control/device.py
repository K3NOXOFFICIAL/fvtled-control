"""FVTLED BLE device controller."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice

from .commands import (
    build_brightness_command,
    build_color_command,
    build_power_off_command,
    build_power_on_command,
    build_status_query_command,
)
from .const import (
    BLE_NOTIFY_CHARACTERISTIC_UUID,
    BLE_STATUS_NOTIFY_CHARACTERISTIC_UUID,
    BLE_STATUS_WRITE_CHARACTERISTIC_UUID,
    BLE_WRITE_CHARACTERISTIC_UUID,
    STATUS_BLUE_INDEX,
    STATUS_BRIGHTNESS_INDEX,
    STATUS_GREEN_INDEX,
    STATUS_POWER_INDEX,
    STATUS_POWER_ON_VALUE,
    STATUS_RED_INDEX,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceState:
    """Snapshot of the device's current state."""

    is_on: bool
    red: int
    green: int
    blue: int
    brightness: int

    @property
    def rgb(self) -> tuple[int, int, int]:
        """Return (red, green, blue) tuple."""
        return (self.red, self.green, self.blue)


def _parse_status(data: bytes) -> DeviceState | None:
    """Parse a raw status response into a :class:`DeviceState`.

    Returns ``None`` when the response is too short to be valid.
    """
    required = max(
        STATUS_POWER_INDEX,
        STATUS_RED_INDEX,
        STATUS_GREEN_INDEX,
        STATUS_BLUE_INDEX,
        STATUS_BRIGHTNESS_INDEX,
    ) + 1
    if len(data) < required:
        _LOGGER.warning(
            "Status response too short: expected at least %d bytes, got %d",
            required,
            len(data),
        )
        return None
    return DeviceState(
        is_on=data[STATUS_POWER_INDEX] == STATUS_POWER_ON_VALUE,
        red=data[STATUS_RED_INDEX],
        green=data[STATUS_GREEN_INDEX],
        blue=data[STATUS_BLUE_INDEX],
        brightness=data[STATUS_BRIGHTNESS_INDEX],
    )


class FVTLEDDevice:
    """Async controller for an FVTLED ARZ-2100 RGB device over BLE.

    Usage example::

        async with FVTLEDDevice("AA:BB:CC:DD:EE:FF") as device:
            await device.turn_on()
            await device.set_color(255, 0, 0)
            state = await device.get_state()
            print(state)
    """

    def __init__(
        self,
        address_or_ble_device: str | BLEDevice,
        *,
        connection_timeout: float = 20.0,
    ) -> None:
        """Initialise the controller.

        Args:
            address_or_ble_device: Bluetooth address string (e.g.
                ``"AA:BB:CC:DD:EE:FF"``) or a :class:`bleak.backends.device.BLEDevice`
                returned by :func:`fvtled_control.scanner.scan`.
            connection_timeout: Maximum time in seconds to wait for the BLE
                connection to be established.
        """
        self._address_or_device = address_or_ble_device
        self._connection_timeout = connection_timeout
        self._client: BleakClient | None = None
        self._state: DeviceState | None = None
        self._notify_callbacks: list[Callable[[DeviceState], None]] = []

    # ------------------------------------------------------------------
    # Context manager helpers
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "FVTLEDDevice":
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Return True when the BLE connection is active."""
        return self._client is not None and self._client.is_connected

    async def connect(self) -> None:
        """Establish the BLE connection and subscribe to notifications."""
        if self.is_connected:
            return
        _LOGGER.debug("Connecting to %s", self._address_or_device)
        self._client = BleakClient(
            self._address_or_device,
            timeout=self._connection_timeout,
        )
        await self._client.connect()
        _LOGGER.info("Connected to %s", self._address_or_device)
        await self._subscribe_notifications()

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            _LOGGER.info("Disconnected from %s", self._address_or_device)
        self._client = None

    # ------------------------------------------------------------------
    # Notification subscription
    # ------------------------------------------------------------------

    def add_state_callback(self, callback: Callable[[DeviceState], None]) -> None:
        """Register a callback that is called whenever the device state changes.

        The callback receives a :class:`DeviceState` instance.
        """
        self._notify_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable[[DeviceState], None]) -> None:
        """Remove a previously registered state callback."""
        self._notify_callbacks.remove(callback)

    def _handle_notification(self, _handle: int, data: bytes) -> None:
        """Process an incoming BLE notification."""
        state = _parse_status(data)
        if state is not None:
            self._state = state
            for cb in self._notify_callbacks:
                cb(state)

    async def _subscribe_notifications(self) -> None:
        """Subscribe to status notifications from the device."""
        assert self._client is not None
        for uuid in (
            BLE_NOTIFY_CHARACTERISTIC_UUID,
            BLE_STATUS_NOTIFY_CHARACTERISTIC_UUID,
        ):
            try:
                await self._client.start_notify(uuid, self._handle_notification)
                _LOGGER.debug("Subscribed to notifications on %s", uuid)
            except BleakError:
                _LOGGER.debug("Characteristic %s not available for notify", uuid)

    # ------------------------------------------------------------------
    # Control commands
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> BleakClient:
        if not self.is_connected or self._client is None:
            raise RuntimeError(
                "Device is not connected. Call connect() or use the async context manager."
            )
        return self._client

    async def _write(self, data: bytes) -> None:
        """Write *data* to the primary write characteristic."""
        client = self._ensure_connected()
        await client.write_gatt_char(
            BLE_WRITE_CHARACTERISTIC_UUID,
            data,
            response=False,
        )

    async def _write_status(self, data: bytes) -> None:
        """Write *data* to the status-service write characteristic."""
        client = self._ensure_connected()
        await client.write_gatt_char(
            BLE_STATUS_WRITE_CHARACTERISTIC_UUID,
            data,
            response=False,
        )

    async def turn_on(self) -> None:
        """Power the device on."""
        _LOGGER.debug("Sending power-on command")
        await self._write(build_power_on_command())

    async def turn_off(self) -> None:
        """Power the device off."""
        _LOGGER.debug("Sending power-off command")
        await self._write(build_power_off_command())

    async def set_color(self, red: int, green: int, blue: int) -> None:
        """Set the RGB color of the LED strip.

        Args:
            red: Red channel value (0–255).
            green: Green channel value (0–255).
            blue: Blue channel value (0–255).
        """
        _LOGGER.debug("Setting color to R=%d G=%d B=%d", red, green, blue)
        await self._write(build_color_command(red, green, blue))

    async def set_brightness(self, brightness: int) -> None:
        """Set the brightness via the white/warm-white channel.

        For pure RGB color control scale the RGB values instead.

        Args:
            brightness: Brightness value (0–255).
        """
        _LOGGER.debug("Setting brightness to %d", brightness)
        await self._write(build_brightness_command(brightness))

    async def get_state(self) -> DeviceState:
        """Query the device and return the current :class:`DeviceState`.

        Returns:
            A :class:`DeviceState` reflecting the latest device status.

        Raises:
            RuntimeError: If the status response cannot be parsed.
        """
        client = self._ensure_connected()
        query = build_status_query_command()
        await client.write_gatt_char(
            BLE_WRITE_CHARACTERISTIC_UUID,
            query,
            response=False,
        )
        # Allow a short time for the notification to arrive
        await asyncio.sleep(0.3)
        if self._state is None:
            # Fallback: attempt a direct read
            try:
                raw = await client.read_gatt_char(BLE_NOTIFY_CHARACTERISTIC_UUID)
                self._state = _parse_status(raw)
            except BleakError:
                pass
        if self._state is None:
            raise RuntimeError("Failed to retrieve device state.")
        return self._state

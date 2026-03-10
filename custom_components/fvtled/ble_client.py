"""Low-level BLE communication for the FVTLED ARZ-2100."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice

try:
    from bleak_retry_connector import establish_connection
    _HAS_RETRY_CONNECTOR = True
except ImportError:
    _HAS_RETRY_CONNECTOR = False

from .const import (
    NOTIFY_CHARACTERISTIC_UUID,
    POWER_OFF_PAYLOAD,
    POWER_ON_PAYLOAD,
    WRITE_CHARACTERISTIC_UUID,
)

_LOGGER = logging.getLogger(__name__)


def _build_rgb_command(r: int, g: int, b: int) -> bytes:
    """Build a 7E-framed RGB colour command.

    Frame layout (9 bytes):
      7E  07  05  03  RR  GG  BB  00  EF
    """
    return bytes([0x7E, 0x07, 0x05, 0x03, r & 0xFF, g & 0xFF, b & 0xFF, 0x00, 0xEF])


def _build_brightness_command(brightness: int) -> bytes:
    """Build a 7E-framed brightness command (0-255).

    Frame layout (9 bytes):
      7E  04  01  <brightness>  00  00  00  00  EF
    """
    return bytes(
        [0x7E, 0x04, 0x01, brightness & 0xFF, 0x00, 0x00, 0x00, 0x00, 0xEF]
    )


class FVTLEDBLEClient:
    """Handle BLE connection and commands for the FVTLED ARZ-2100."""

    def __init__(self, ble_device: BLEDevice) -> None:
        """Initialise the BLE client."""
        self._ble_device = ble_device
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._is_on: bool = False

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    async def _ensure_connected(self) -> BleakClient:
        """Return a connected BleakClient, creating one if necessary."""
        if self._client and self._client.is_connected:
            return self._client

        _LOGGER.debug("Connecting to FVTLED %s", self._ble_device.address)

        if _HAS_RETRY_CONNECTOR:
            client = await establish_connection(
                BleakClient,
                self._ble_device,
                self._ble_device.name or self._ble_device.address,
            )
        else:
            client = BleakClient(self._ble_device)
            await client.connect()

        self._client = client
        _LOGGER.debug("Connected to FVTLED %s", self._ble_device.address)
        return client

    async def async_stop(self) -> None:
        """Disconnect from the device."""
        async with self._lock:
            if self._client and self._client.is_connected:
                await self._client.disconnect()
                self._client = None
                _LOGGER.debug("Disconnected from FVTLED %s", self._ble_device.address)

    # ------------------------------------------------------------------
    # Command helpers
    # ------------------------------------------------------------------

    async def _send_command(self, payload: bytes) -> None:
        """Write *payload* to the write characteristic."""
        async with self._lock:
            client = await self._ensure_connected()
            _LOGGER.debug(
                "Sending command to %s: %s",
                self._ble_device.address,
                payload.hex(" ").upper(),
            )
            await client.write_gatt_char(
                WRITE_CHARACTERISTIC_UUID, bytearray(payload), response=False
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_turn_on(self) -> None:
        """Turn the LED strip on."""
        await self._send_command(POWER_ON_PAYLOAD)
        self._is_on = True

    async def async_turn_off(self) -> None:
        """Turn the LED strip off."""
        await self._send_command(POWER_OFF_PAYLOAD)
        self._is_on = False

    async def async_set_rgb(self, r: int, g: int, b: int) -> None:
        """Set the LED strip colour (RGB, each 0-255)."""
        await self._send_command(_build_rgb_command(r, g, b))

    async def async_set_brightness(self, brightness: int) -> None:
        """Set the LED strip brightness (0-255)."""
        await self._send_command(_build_brightness_command(brightness))

    async def async_update(self) -> bool:
        """Query device state; returns True if the device is on.

        Because the ARZ-2100 does not expose a readable state characteristic
        in its documented protocol, we rely on our locally tracked state.
        A connection attempt (via _ensure_connected) still validates that
        the device is reachable.
        """
        try:
            async with self._lock:
                await self._ensure_connected()
        except BleakError as err:
            _LOGGER.warning(
                "Could not connect to FVTLED %s: %s", self._ble_device.address, err
            )
            raise
        return self._is_on

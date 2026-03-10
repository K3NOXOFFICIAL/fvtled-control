"""BLE device coordinator for FVTLED ARZ-2100."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from bleak import BleakError
from bleak.backends.device import BLEDevice

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble_client import FVTLEDBLEClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)


class FVTLEDCoordinator(DataUpdateCoordinator[bool]):
    """Coordinator that fetches state from the FVTLED ARZ-2100 via BLE."""

    def __init__(self, hass: HomeAssistant, ble_device: BLEDevice) -> None:
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.ble_client = FVTLEDBLEClient(ble_device)

    # ------------------------------------------------------------------
    # Public helpers (called by the light entity)
    # ------------------------------------------------------------------

    async def async_turn_on(self) -> None:
        """Turn the light on."""
        await self.ble_client.async_turn_on()
        self.async_set_updated_data(True)

    async def async_turn_off(self) -> None:
        """Turn the light off."""
        await self.ble_client.async_turn_off()
        self.async_set_updated_data(False)

    async def async_set_rgb(self, r: int, g: int, b: int) -> None:
        """Set RGB colour."""
        await self.ble_client.async_set_rgb(r, g, b)

    async def async_set_brightness(self, brightness: int) -> None:
        """Set brightness (0-255)."""
        await self.ble_client.async_set_brightness(brightness)

    async def async_stop(self) -> None:
        """Stop the BLE client (disconnect)."""
        await self.ble_client.async_stop()

    # ------------------------------------------------------------------
    # DataUpdateCoordinator implementation
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> bool:
        """Poll the device state."""
        try:
            return await self.ble_client.async_update()
        except BleakError as err:
            raise UpdateFailed(f"BLE error while polling FVTLED: {err}") from err

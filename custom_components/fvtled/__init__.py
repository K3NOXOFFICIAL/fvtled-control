"""The FVTLED integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .bluetooth import FVTLEDBLEDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FVTLED from a config entry."""
    address: str = entry.data["address"]

    device = FVTLEDBLEDevice(address)
    connected = await device.connect()
    if not connected:
        _LOGGER.warning(
            "Could not connect to FVTLED device %s during setup; "
            "will retry when available",
            address,
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        device: FVTLEDBLEDevice = hass.data[DOMAIN].pop(entry.entry_id)
        await device.disconnect()
    return unload_ok

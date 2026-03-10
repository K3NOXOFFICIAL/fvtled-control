"""FVTLED ARZ-2100 BLE – Home Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_ADDRESS, DOMAIN
from .coordinator import FVTLEDCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["light"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FVTLED from a config entry."""
    address: str = entry.data[CONF_ADDRESS]

    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable=True
    )
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find FVTLED ARZ-2100 with address {address}"
        )

    coordinator = FVTLEDCoordinator(hass, ble_device)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: FVTLEDCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_stop()
    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

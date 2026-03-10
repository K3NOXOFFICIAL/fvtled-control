"""The FVTLED BLE Controller integration."""
from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .ble_device import FvtledBleDevice
from .const import CONF_ADDRESS, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FVTLED BLE Controller from a config entry."""
    address: str = entry.data[CONF_ADDRESS]

    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find FVTLED device with address {address}. "
            "Make sure the device is powered on and in range."
        )

    fvtled = FvtledBleDevice(ble_device)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = fvtled

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        fvtled: FvtledBleDevice = hass.data[DOMAIN].pop(entry.entry_id)
        await fvtled.async_disconnect()
    return unload_ok

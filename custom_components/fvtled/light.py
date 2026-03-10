"""Light platform for the FVTLED BLE Controller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ble_device import FvtledBleDevice
from .const import CONF_ADDRESS, CONF_NAME, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FVTLED light from a config entry."""
    fvtled: FvtledBleDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FvtledLight(fvtled, entry)])


class FvtledLight(LightEntity):
    """Representation of an FVTLED ARZ-2100 BLE RGB light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature(0)

    def __init__(self, device: FvtledBleDevice, entry: ConfigEntry) -> None:
        """Initialise the light entity."""
        self._device = device
        self._entry = entry

        name = entry.data.get(CONF_NAME) or device.name or DEFAULT_NAME
        address = entry.data[CONF_ADDRESS]

        self._attr_unique_id = address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="FVTLED",
            model="ARZ-2100",
        )

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return self._device.is_on

    @property
    def brightness(self) -> int:
        """Return current brightness (0-255)."""
        return self._device.brightness

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return current RGB color."""
        return (self._device.red, self._device.green, self._device.blue)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, optionally setting color or brightness."""
        rgb: tuple[int, int, int] | None = kwargs.get(ATTR_RGB_COLOR)
        brightness: int | None = kwargs.get(ATTR_BRIGHTNESS)

        if rgb is not None and brightness is not None:
            # Scale the requested RGB by the requested brightness
            scale = brightness / 255.0
            scaled = tuple(round(c * scale) for c in rgb)
            await self._device.async_set_color(*scaled)
        elif rgb is not None:
            await self._device.async_set_color(*rgb)
        elif brightness is not None:
            # Scale the current RGB values by the new brightness
            scale = brightness / 255.0
            scaled = tuple(round(c * scale) for c in self.rgb_color)
            await self._device.async_set_color(*scaled)
            self._device.brightness = brightness
        else:
            await self._device.async_turn_on()

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._device.async_turn_off()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the latest state from the device."""
        await self._device.async_update()

    async def async_added_to_hass(self) -> None:
        """Subscribe to BLE notifications when entity is added."""
        await self._device.async_start_notify()

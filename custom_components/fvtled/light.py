"""FVTLED light entity."""
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .bluetooth import FVTLEDBLEDevice
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the FVTLED light from a config entry."""
    device: FVTLEDBLEDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FVTLEDLight(device, entry)])


class FVTLEDLight(LightEntity):
    """Representation of an FVTLED RGB light controlled over BLE."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device: FVTLEDBLEDevice, entry: ConfigEntry) -> None:
        """Initialize the light entity."""
        self._device = device
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            name=entry.data.get("name", device.address),
            manufacturer="FVTLED",
            model="ARZ-2100",
        )
        device.register_callback(self._handle_state_update)

    @callback
    def _handle_state_update(self, state: dict) -> None:
        """Handle state updates pushed by the BLE device."""
        self._attr_is_on = state["is_on"]
        self._attr_rgb_color = state["rgb"]
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, optionally setting color/brightness."""
        rgb: tuple[int, int, int] | None = kwargs.get(ATTR_RGB_COLOR)
        brightness: int | None = kwargs.get(ATTR_BRIGHTNESS)

        if rgb is not None:
            r, g, b = rgb
            if brightness is not None:
                scale = brightness / 255
                r = round(r * scale)
                g = round(g * scale)
                b = round(b * scale)
            await self._device.set_rgb(r, g, b)
        elif brightness is not None:
            # Scale the current color by the new brightness
            current = self._device.rgb_color
            scale = brightness / 255
            await self._device.set_rgb(
                round(current[0] * scale),
                round(current[1] * scale),
                round(current[2] * scale),
            )

        await self._device.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._device.turn_off()

    @property
    def is_on(self) -> bool | None:
        """Return True if the light is on."""
        return self._device.is_on

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the current RGB color."""
        return self._device.rgb_color

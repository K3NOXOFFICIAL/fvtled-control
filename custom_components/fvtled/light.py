"""Light platform for FVTLED ARZ-2100 BLE integration."""
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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ADDRESS, CONF_NAME, DOMAIN
from .coordinator import FVTLEDCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FVTLED light from a config entry."""
    coordinator: FVTLEDCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FVTLEDLight(coordinator, entry)])


class FVTLEDLight(CoordinatorEntity[FVTLEDCoordinator], LightEntity):
    """Representation of an FVTLED ARZ-2100 light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        coordinator: FVTLEDCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the light entity."""
        super().__init__(coordinator)
        self._entry = entry

        address: str = entry.data[CONF_ADDRESS]
        device_name: str = entry.data.get(CONF_NAME, address)

        self._attr_unique_id = address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=device_name,
            manufacturer="FVTLED",
            model="ARZ-2100",
        )

        # Local state cache
        self._brightness: int = 255
        self._rgb_color: tuple[int, int, int] = (255, 255, 255)

    # ------------------------------------------------------------------
    # State properties
    # ------------------------------------------------------------------

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return bool(self.coordinator.data)

    @property
    def brightness(self) -> int:
        """Return the current brightness (0-255)."""
        return self._brightness

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the current RGB colour."""
        return self._rgb_color

    # ------------------------------------------------------------------
    # Control methods
    # ------------------------------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, optionally setting colour and brightness."""
        await self.coordinator.async_turn_on()

        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            self._rgb_color = (r, g, b)
            await self.coordinator.async_set_rgb(r, g, b)

        if ATTR_BRIGHTNESS in kwargs:
            brightness: int = kwargs[ATTR_BRIGHTNESS]
            self._brightness = brightness
            await self.coordinator.async_set_brightness(brightness)

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.async_turn_off()
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

"""Light platform for FVTLED ARZ-2100 integration."""
import logging
from typing import Any, Optional

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_MANUFACTURER, DEVICE_MODEL, DOMAIN
from .protocol import FVTLEDARZ2100Protocol

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FVTLED ARZ-2100 light from config entry."""
    host = entry.data[CONF_HOST]
    name = entry.data.get(CONF_NAME, f"FVTLED ARZ-2100 {host}")

    protocol = FVTLEDARZ2100Protocol(host)

    async_add_entities([FVTLEDARZ2100Light(protocol, name, entry.entry_id)], update_before_add=True)


class FVTLEDARZ2100Light(LightEntity):
    """Representation of a FVTLED ARZ-2100 RGB light."""

    def __init__(self, protocol: FVTLEDARZ2100Protocol, name: str, unique_id: str):
        """Initialize the light."""
        self._protocol = protocol
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGBW}

        # State variables
        self._attr_is_on = False
        self._attr_brightness = 255
        self._attr_rgbw_color = (255, 255, 255, 0)
        self._attr_available = True

        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unique_id)},
            "name": name,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL,
            "sw_version": "Firmware WF.52 (ZG-BL-3KEY)",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self._attr_brightness)
        rgbw = kwargs.get(ATTR_RGBW_COLOR)
        rgb = kwargs.get(ATTR_RGB_COLOR)

        # Handle color change
        if rgbw is not None:
            red, green, blue, white = rgbw
        elif rgb is not None:
            red, green, blue = rgb
            white = self._attr_rgbw_color[3]
        else:
            red, green, blue, white = self._attr_rgbw_color

        # First turn on the device
        if not self._attr_is_on:
            success = await self._protocol.async_turn_on()
            if not success:
                _LOGGER.error("Failed to turn on light")
                return

        # Set color and brightness
        success = await self._protocol.async_set_color(red, green, blue, white, brightness)
        if success:
            self._attr_is_on = True
            self._attr_brightness = brightness
            self._attr_rgbw_color = (red, green, blue, white)
        else:
            _LOGGER.error("Failed to set color")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        success = await self._protocol.async_turn_off()
        if success:
            self._attr_is_on = False
        else:
            _LOGGER.error("Failed to turn off light")

    async def async_update(self) -> None:
        """Fetch new state data for the light."""
        status = await self._protocol.async_get_status()
        if status:
            self._attr_available = True
            self._attr_is_on = status["power"]
            self._attr_brightness = status["brightness"]
            self._attr_rgbw_color = (
                status["red"],
                status["green"],
                status["blue"],
                status["white"],
            )
            _LOGGER.debug(
                "Updated state: power=%s, brightness=%s, rgbw=%s",
                self._attr_is_on,
                self._attr_brightness,
                self._attr_rgbw_color,
            )
        else:
            self._attr_available = False
            _LOGGER.warning("Failed to update device status")

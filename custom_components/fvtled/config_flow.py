"""Config flow for FVTLED ARZ-2100 BLE integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import CONF_NAME, DOMAIN, LOCAL_NAME_STARTS

_LOGGER = logging.getLogger(__name__)


def _is_fvtled_device(service_info: BluetoothServiceInfoBleak) -> bool:
    """Return True if the advertisement looks like an FVTLED ARZ-2100."""
    name = service_info.name or ""
    return any(name.upper().startswith(prefix) for prefix in LOCAL_NAME_STARTS)


class FVTLEDConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FVTLED ARZ-2100."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the config flow."""
        self._discovered_devices: dict[str, str] = {}  # address -> name
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    # ------------------------------------------------------------------
    # Bluetooth discovery (auto)
    # ------------------------------------------------------------------

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": discovery_info.name or discovery_info.address,
        }
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered device."""
        assert self._discovery_info is not None
        info = self._discovery_info

        if user_input is not None:
            return self.async_create_entry(
                title=info.name or info.address,
                data={
                    CONF_ADDRESS: info.address,
                    CONF_NAME: info.name or info.address,
                },
            )

        self._set_confirm_only()
        placeholders = {"name": info.name or info.address, "address": info.address}
        return self.async_show_form(
            step_id="confirm",
            description_placeholders=placeholders,
        )

    # ------------------------------------------------------------------
    # Manual setup (user-initiated)
    # ------------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial (user) step."""
        errors: dict[str, str] = {}

        # Collect visible FVTLED devices
        current_addresses = self._async_current_ids()
        for service_info in async_discovered_service_info(self.hass, connectable=True):
            if service_info.address not in current_addresses and _is_fvtled_device(
                service_info
            ):
                self._discovered_devices[service_info.address] = (
                    service_info.name or service_info.address
                )

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices.get(address, address),
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: self._discovered_devices.get(address, address),
                },
            )

        if self._discovered_devices:
            schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            addr: f"{name} ({addr})"
                            for addr, name in self._discovered_devices.items()
                        }
                    )
                }
            )
        else:
            schema = vol.Schema(
                {vol.Required(CONF_ADDRESS): str}
            )
            if not user_input:
                errors["base"] = "no_devices_found"

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

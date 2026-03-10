"""Config flow for the FVTLED BLE Controller integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import (
    BLE_SERVICE_UUID_ADVERTISEMENT,
    BLE_SERVICE_UUID_PRIMARY,
    BLE_SERVICE_UUID_SECONDARY,
    CONF_ADDRESS,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_FVTLED_SERVICE_UUIDS = {
    BLE_SERVICE_UUID_PRIMARY,
    BLE_SERVICE_UUID_SECONDARY,
    BLE_SERVICE_UUID_ADVERTISEMENT,
}


def _is_fvtled_device(service_info: BluetoothServiceInfo) -> bool:
    """Return True if the advertisement looks like an FVTLED device."""
    for uuid in service_info.service_uuids:
        if uuid.lower() in _FVTLED_SERVICE_UUIDS:
            return True
    # Fall back to name pattern used by firmware (e.g. IOTWFE1B)
    name = service_info.name or ""
    return name.startswith("IOT") or name.startswith("FVTLED")


class FvtledConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FVTLED BLE Controller."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the config flow."""
        self._discovered_devices: dict[str, BluetoothServiceInfo] = {}
        self._discovery_info: BluetoothServiceInfo | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> ConfigFlowResult:
        """Handle a device discovered via Bluetooth."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        if not _is_fvtled_device(discovery_info):
            return self.async_abort(reason="not_supported")

        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": discovery_info.name or discovery_info.address,
        }
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm BLE discovery."""
        assert self._discovery_info is not None
        info = self._discovery_info

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME) or info.name or DEFAULT_NAME,
                data={
                    CONF_ADDRESS: info.address,
                    CONF_NAME: user_input.get(CONF_NAME) or info.name or DEFAULT_NAME,
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": info.name or info.address,
                "address": info.address,
            },
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=info.name or DEFAULT_NAME,
                    ): str,
                }
            ),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, address, connectable=True
            )
            if not ble_device:
                errors["base"] = "device_not_found"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or ble_device.name or DEFAULT_NAME,
                    data={
                        CONF_ADDRESS: address,
                        CONF_NAME: user_input.get(CONF_NAME) or ble_device.name or DEFAULT_NAME,
                    },
                )

        # Collect nearby FVTLED devices to show in a dropdown
        current_addresses = self._async_current_ids()
        self._discovered_devices = {
            service_info.address: service_info
            for service_info in async_discovered_service_info(self.hass, connectable=True)
            if service_info.address not in current_addresses and _is_fvtled_device(service_info)
        }

        address_options = {
            address: f"{info.name or address} ({address})"
            for address, info in self._discovered_devices.items()
        }

        if address_options:
            schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(address_options),
                    vol.Optional(CONF_NAME): str,
                }
            )
        else:
            schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                    vol.Optional(CONF_NAME): str,
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "discovered": str(len(address_options)),
            },
        )

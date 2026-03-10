"""Config flow for the FVTLED integration.

This module implements the Home Assistant config flow that allows users to
discover nearby FVTLED BLE devices and add them to their Home Assistant
installation.
"""
from __future__ import annotations

import logging
from typing import Any

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.data_entry_flow import FlowResult

from .const import BLE_ADV_SERVICE_UUID, BLE_DEVICE_NAME_PREFIX, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FVTLEDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for FVTLED BLE devices.

    The flow presents the user with a list of discovered FVTLED devices
    (identified by their BLE advertisement service UUID and name prefix),
    lets them choose one, and creates a config entry for it.
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, BLEDevice] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle a device discovered via the Bluetooth integration.

        Home Assistant calls this step automatically when a device matching
        the service UUIDs declared in *manifest.json* is seen.
        """
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "name": discovery_info.name or discovery_info.address
        }
        return await self.async_step_confirm()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a manual configuration initiated by the user.

        Scans for nearby FVTLED BLE devices and shows a selection list.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input["device"]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            device = self._discovered_devices.get(address)
            name = (device.name if device else None) or address
            return self.async_create_entry(
                title=name,
                data={"address": address, "name": name},
            )

        # Discover devices via the Home Assistant Bluetooth integration
        discovered: dict[str, str] = {}
        for info in async_discovered_service_info(self.hass):
            if _is_fvtled_device(info):
                if not self._already_configured(info.address):
                    discovered[info.address] = f"{info.name} ({info.address})"
                    self._discovered_devices[info.address] = info.device

        if not discovered:
            return self.async_abort(reason="no_devices_found")

        schema = vol.Schema(
            {vol.Required("device"): vol.In(discovered)}
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask the user to confirm adding the auto-discovered device."""
        if user_input is not None or self.source == config_entries.SOURCE_BLUETOOTH:
            unique_id = self.unique_id
            if unique_id is None:
                return self.async_abort(reason="unknown")

            # Resolve name from context if available
            name = self.context.get("title_placeholders", {}).get("name", unique_id)

            if user_input is not None:
                return self.async_create_entry(
                    title=name,
                    data={"address": unique_id, "name": name},
                )

            return self.async_show_form(
                step_id="confirm",
                description_placeholders={"name": name},
            )

        return self.async_show_form(step_id="confirm")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _already_configured(self, address: str) -> bool:
        """Return True if the given address is already configured."""
        return any(
            entry.data.get("address") == address
            for entry in self._async_current_entries()
        )


def _is_fvtled_device(info: BluetoothServiceInfoBleak) -> bool:
    """Return True if the Bluetooth advertisement belongs to an FVTLED device.

    Detection criteria:
    - The device name starts with the known FVTLED prefix (``IOTWF``), *or*
    - The advertisement includes the FVTLED service UUID (``0x5A01``).
    """
    name: str = info.name or ""
    if name.startswith(BLE_DEVICE_NAME_PREFIX):
        return True
    if BLE_ADV_SERVICE_UUID in (info.service_uuids or []):
        return True
    return False

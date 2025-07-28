"""Config flow for Philips Hue Bluetooth integration."""

from __future__ import annotations

import logging
from typing import Any

from bleak import BleakClient
from bleak.backends.device import BLEDevice
import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import AbortFlow

from .const import DOMAIN, PLUG_SERVICE

_LOGGER = logging.getLogger(__name__)


def _is_supported(discovery_info: BluetoothServiceInfo) -> bool:
    """Check if device is supported."""
    return PLUG_SERVICE in discovery_info.service_uuids


def _get_name(discovery_info: BluetoothServiceInfo) -> str:
    """Get device name from discovery info."""
    return discovery_info.name or "Philips Hue Smart Plug"


class PhilipsHueConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Philips Hue Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.devices: dict[str, str] = {}
        self.address: str | None = None

    async def async_test_connection(self, address: str) -> None:
        """Try to connect to device and test communication."""
        from homeassistant.components import bluetooth

        device = bluetooth.async_ble_device_from_address(
            self.hass, address, connectable=True
        )
        if not device:
            raise AbortFlow("cannot_connect")

        client = BleakClient(device)
        try:
            await client.connect()
            # Try to read a characteristic to verify the device works
            services = await client.get_services()
            if not any(str(service.uuid) == PLUG_SERVICE for service in services):
                raise AbortFlow("unsupported_device")
        except Exception as exception:
            _LOGGER.debug("Failed to connect to device %s: %s", address, exception)
            raise AbortFlow("cannot_connect") from exception
        finally:
            if client.is_connected:
                await client.disconnect()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug("Discovered device: %s", discovery_info)
        if not _is_supported(discovery_info):
            return self.async_abort(reason="not_supported")

        self.address = discovery_info.address
        self.devices = {discovery_info.address: _get_name(discovery_info)}
        await self.async_set_unique_id(self.address)
        self._abort_if_unique_id_configured()
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        assert self.address
        title = self.devices[self.address]

        if user_input is not None:
            try:
                await self.async_test_connection(self.address)
                return self.async_create_entry(
                    title=title, data={CONF_ADDRESS: self.address}
                )
            except AbortFlow:
                return self.async_abort(reason="cannot_connect")

        self.context["title_placeholders"] = {"name": title}
        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self.address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(self.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            try:
                await self.async_test_connection(self.address)
                return self.async_create_entry(
                    title=self.devices.get(self.address, "Philips Hue Smart Plug"),
                    data={CONF_ADDRESS: self.address},
                )
            except AbortFlow:
                return self.async_abort(reason="cannot_connect")

        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address
            if address in current_addresses or not _is_supported(discovery_info):
                continue

            self.devices[address] = _get_name(discovery_info)

        if not self.devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(self.devices),
                },
            ),
        )

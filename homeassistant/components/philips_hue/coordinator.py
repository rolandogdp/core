"""Provides the DataUpdateCoordinator for Philips Hue Bluetooth devices."""

from __future__ import annotations

from datetime import timedelta
import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import PLUG_STATE

SCAN_INTERVAL = timedelta(seconds=30)
LOGGER = logging.getLogger(__name__)

type PhilipsHueConfigEntry = ConfigEntry[PhilipsHueCoordinator]


class DeviceUnavailable(HomeAssistantError):
    """Raised if device can't be found."""


class PhilipsHueCoordinator(DataUpdateCoordinator[dict[str, bool]]):
    """Class to manage fetching data from Philips Hue Bluetooth devices."""

    config_entry: PhilipsHueConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: PhilipsHueConfigEntry,
        logger: logging.Logger,
        device_info: DeviceInfo,
        address: str,
    ) -> None:
        """Initialize global data updater."""
        super().__init__(
            hass=hass,
            logger=logger,
            config_entry=config_entry,
            name="Philips Hue Bluetooth Data Update Coordinator",
            update_interval=SCAN_INTERVAL,
        )
        self.address = address
        self.device_info = device_info
        self._client: BleakClient | None = None

    def _get_device(self) -> BLEDevice:
        """Get the Bluetooth device."""
        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if not device:
            raise DeviceUnavailable(f"Device {self.address} is not available")
        return device

    async def _get_client(self) -> BleakClient:
        """Get a connected BleakClient."""
        if self._client is None or not self._client.is_connected:
            device = self._get_device()
            self._client = BleakClient(device)
            await self._client.connect()
        return self._client

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and any connection."""
        await super().async_shutdown()
        if self._client and self._client.is_connected:
            await self._client.disconnect()

    async def _async_update_data(self) -> dict[str, bool]:
        """Poll the device for current state."""
        try:
            client = await self._get_client()
            status_bytes = await client.read_gatt_char(PLUG_STATE)
            is_on = status_bytes == b"\x01"
        except Exception as exception:
            if self._client and self._client.is_connected:
                await self._client.disconnect()
                self._client = None
            raise UpdateFailed(
                f"Unable to update data for {self.address} due to {exception}"
            ) from exception
        else:
            return {"switch": is_on}

    async def async_turn_on(self) -> None:
        """Turn the device on."""
        try:
            client = await self._get_client()
            await client.write_gatt_char(PLUG_STATE, b"\x01")
            # Update local state immediately
            if self.data:
                self.data["switch"] = True
                self.async_update_listeners()
        except Exception as exception:
            if self._client and self._client.is_connected:
                await self._client.disconnect()
                self._client = None
            raise HomeAssistantError(
                f"Unable to turn on device {self.address} due to {exception}"
            ) from exception

    async def async_turn_off(self) -> None:
        """Turn the device off."""
        try:
            client = await self._get_client()
            await client.write_gatt_char(PLUG_STATE, b"\x00")
            # Update local state immediately
            if self.data:
                self.data["switch"] = False
                self.async_update_listeners()
        except Exception as exception:
            if self._client and self._client.is_connected:
                await self._client.disconnect()
                self._client = None
            raise HomeAssistantError(
                f"Unable to turn off device {self.address} due to {exception}"
            ) from exception

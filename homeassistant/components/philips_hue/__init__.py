"""The Philips Hue Bluetooth integration."""

from __future__ import annotations

import logging

from bleak.backends.device import BLEDevice

from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import DeviceUnavailable, PhilipsHueConfigEntry, PhilipsHueCoordinator

PLATFORMS: list[Platform] = [Platform.SWITCH]
LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: PhilipsHueConfigEntry) -> bool:
    """Set up Philips Hue Bluetooth from a config entry."""
    address = entry.data[CONF_ADDRESS]

    # Verify device is available
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address, connectable=True
    )
    if not ble_device:
        raise ConfigEntryNotReady(f"Device {address} is not available")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, address)},
        connections={(dr.CONNECTION_BLUETOOTH, address)},
        name=entry.title,
        manufacturer="Philips",
        model="Hue Smart Plug",
    )

    coordinator = PhilipsHueCoordinator(
        hass, entry, LOGGER, device_info, address
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except (DeviceUnavailable, Exception) as exception:
        await coordinator.async_shutdown()
        raise ConfigEntryNotReady(
            f"Unable to connect to device {address} due to {exception}"
        ) from exception

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PhilipsHueConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_shutdown()

    return unload_ok

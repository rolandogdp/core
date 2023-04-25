"""File for the Philips Hue Bluetooth Plug Switch High level interface."""
import logging
import typing

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .philips_plug import PhilipsHuePlug

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    mac = config[CONF_ADDRESS] or config["unique_id"]

    # # Setup connection with devices/cloud
    # hub = awesomelights.Hub(host, username, password)

    # # Verify that passed in configuration works
    # if not hub.is_valid_login():
    #     _LOGGER.error("Could not connect to AwesomeLight hub")
    #     return

    # Add devices
    add_entities([PhilipsSmartPlug(mac)])


class PhilipsSmartPlug(SwitchEntity):
    """Philips Hue Bluetooth Plug High level interface."""

    _attr_has_entity_name = True

    def __init__(self, mac, name="Default Name") -> None:
        """Init function."""
        self._is_on = False
        self._mac = mac
        self._name = name
        # self._attr_device_info = ...  # For automatic device registration
        # self._attr_unique_id = ...
        self._device: PhilipsHuePlug = PhilipsHuePlug(mac, name=name)

    @property
    def is_on(self) -> bool:
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self, **kwargs: typing.Any) -> None:
        """Turn the entity on."""
        self._device.turn_on()

    async def async_turn_off(self, **kwargs: typing.Any) -> None:
        """Turn the entity off."""
        self._device.turn_off()

    async def async_toggle(self, **kwargs: typing.Any) -> None:
        """Toggle the entity."""
        if self._is_on:
            await self.async_turn_off()
        elif not self._is_on:
            await self.async_turn_on()

    async def async_update(self) -> None:
        """Fetch data."""
        self._is_on = await self._device.get_status()

    async def pair(self):
        """Pairs to the device."""
        await self._device.pair()
        return True

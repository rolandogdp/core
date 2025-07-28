"""Switch platform for Philips Hue Bluetooth devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PhilipsHueConfigEntry, PhilipsHueCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsHueConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Philips Hue Bluetooth switch based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([PhilipsHueSwitchEntity(coordinator, entry)])


class PhilipsHueSwitchEntity(CoordinatorEntity[PhilipsHueCoordinator], SwitchEntity):
    """Representation of a Philips Hue Bluetooth smart plug."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: PhilipsHueCoordinator,
        entry: PhilipsHueConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_switch"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("switch")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.async_turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.async_turn_off()

"""Test the Philips Hue Bluetooth switch platform."""

from unittest.mock import AsyncMock, Mock

import pytest

from homeassistant.components.philips_hue.const import DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, CONF_ADDRESS, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry


async def test_switch_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_bleak_client,
    enable_bluetooth,
) -> None:
    """Test switch setup and basic functionality."""
    mock_config_entry.add_to_hass(hass)
    
    # Mock the device lookup
    enable_bluetooth.return_value = Mock()
    
    # Mock coordinator data
    mock_bleak_client.read_gatt_char.return_value = b"\x00"  # Device is off
    
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Verify entity is created
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)
    assert len(entities) == 1
    
    entity = entities[0]
    assert entity.domain == SWITCH_DOMAIN
    assert entity.unique_id == f"{mock_config_entry.unique_id}_switch"
    
    # Check initial state
    state = hass.states.get(entity.entity_id)
    assert state.state == "off"


async def test_switch_turn_on(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_bleak_client,
    enable_bluetooth,
) -> None:
    """Test turning the switch on."""
    mock_config_entry.add_to_hass(hass)
    enable_bluetooth.return_value = Mock()
    mock_bleak_client.read_gatt_char.return_value = b"\x00"  # Initially off
    
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Get the entity
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)
    entity_id = entities[0].entity_id
    
    # Turn on the switch
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    
    # Verify the write command was sent
    mock_bleak_client.write_gatt_char.assert_called_with(
        "932c32bd-0002-47a2-835a-a8d455b859dd", b"\x01"
    )


async def test_switch_turn_off(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_bleak_client,
    enable_bluetooth,
) -> None:
    """Test turning the switch off."""
    mock_config_entry.add_to_hass(hass)
    enable_bluetooth.return_value = Mock()
    mock_bleak_client.read_gatt_char.return_value = b"\x01"  # Initially on
    
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Get the entity
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)
    entity_id = entities[0].entity_id
    
    # Turn off the switch
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    
    # Verify the write command was sent
    mock_bleak_client.write_gatt_char.assert_called_with(
        "932c32bd-0002-47a2-835a-a8d455b859dd", b"\x00"
    )


async def test_device_unavailable(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    enable_bluetooth,
) -> None:
    """Test handling when device is unavailable."""
    mock_config_entry.add_to_hass(hass)
    
    # Mock device as unavailable
    enable_bluetooth.return_value = None
    
    # Setup should fail with ConfigEntryNotReady
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
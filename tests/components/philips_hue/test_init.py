"""Test the Philips Hue Bluetooth integration setup."""

from unittest.mock import Mock

import pytest

from homeassistant.components.philips_hue.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_setup_and_unload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_bleak_client,
    enable_bluetooth,
) -> None:
    """Test integration setup and unload."""
    mock_config_entry.add_to_hass(hass)
    enable_bluetooth.return_value = Mock()
    mock_bleak_client.read_gatt_char.return_value = b"\x00"
    
    # Setup should succeed
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    
    # Unload should succeed
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_device_unavailable(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    enable_bluetooth,
) -> None:
    """Test setup when device is unavailable."""
    mock_config_entry.add_to_hass(hass)
    enable_bluetooth.return_value = None  # Device unavailable
    
    # Setup should fail
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_connection_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_bleak_client,
    enable_bluetooth,
) -> None:
    """Test setup when connection fails."""
    mock_config_entry.add_to_hass(hass)
    enable_bluetooth.return_value = Mock()
    
    # Mock connection failure during first refresh
    mock_bleak_client.connect.side_effect = Exception("Connection failed")
    
    # Setup should fail
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
"""Common fixtures for the Philips Hue Bluetooth tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.components.philips_hue.const import DOMAIN
from homeassistant.const import CONF_ADDRESS

from tests.common import MockConfigEntry


TEST_ADDRESS = "00:11:22:33:44:55"


@pytest.fixture
def mock_config_entry():
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Philips Hue Smart Plug",
        domain=DOMAIN,
        data={CONF_ADDRESS: TEST_ADDRESS},
        unique_id=TEST_ADDRESS,
    )


@pytest.fixture
def mock_bleak_client():
    """Mock BleakClient."""
    client = Mock()
    client.is_connected = True
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.read_gatt_char = AsyncMock(return_value=b"\x00")
    client.write_gatt_char = AsyncMock()
    client.get_services = AsyncMock()
    
    # Mock services
    service = Mock()
    service.uuid = "932c32bd-0000-47a2-835a-a8d455b859dd"
    client.get_services.return_value = [service]
    
    return client


@pytest.fixture
def mock_bluetooth_device():
    """Mock Bluetooth device."""
    device = Mock()
    device.address = TEST_ADDRESS
    device.name = "Philips Hue Smart Plug"
    return device


@pytest.fixture(autouse=True)
def enable_bluetooth():
    """Auto-enable bluetooth."""
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_async_ble_device_from_address:
        mock_async_ble_device_from_address.return_value = Mock()
        yield mock_async_ble_device_from_address


@pytest.fixture(autouse=True)
def mock_bleak_client_class(mock_bleak_client):
    """Mock BleakClient class."""
    with patch("bleak.BleakClient", return_value=mock_bleak_client):
        yield mock_bleak_client


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.philips_hue.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry

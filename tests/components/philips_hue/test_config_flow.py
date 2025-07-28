"""Test the Philips Hue Bluetooth config flow."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfo
from homeassistant.components.philips_hue.const import DOMAIN, PLUG_SERVICE
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.bluetooth import inject_bluetooth_service_info

pytestmark = pytest.mark.usefixtures("mock_setup_entry")

TEST_ADDRESS = "00:11:22:33:44:55"
TEST_SERVICE_INFO = BluetoothServiceInfo(
    name="Philips Hue Smart Plug",
    address=TEST_ADDRESS,
    rssi=-40,
    manufacturer_data={},
    service_data={},
    service_uuids=[PLUG_SERVICE],
    source="local",
)

UNSUPPORTED_SERVICE_INFO = BluetoothServiceInfo(
    name="Random Device",
    address="00:11:22:33:44:66",
    rssi=-40,
    manufacturer_data={},
    service_data={},
    service_uuids=["12345678-1234-1234-1234-123456789abc"],
    source="local",
)


async def test_bluetooth_discovery(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test the bluetooth discovery flow."""
    inject_bluetooth_service_info(hass, TEST_SERVICE_INFO)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TEST_SERVICE_INFO,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "confirm"
    
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Philips Hue Smart Plug"
    assert result["data"] == {CONF_ADDRESS: TEST_ADDRESS}
    assert len(mock_setup_entry.mock_calls) == 1


async def test_bluetooth_discovery_unsupported_device(hass: HomeAssistant) -> None:
    """Test discovery with unsupported device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=UNSUPPORTED_SERVICE_INFO,
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_bluetooth_discovery_already_configured(hass: HomeAssistant) -> None:
    """Test discovery with already configured device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_ADDRESS,
        data={CONF_ADDRESS: TEST_ADDRESS},
    )
    entry.add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TEST_SERVICE_INFO,
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_no_devices(hass: HomeAssistant) -> None:
    """Test user flow when no devices are found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_flow_with_devices(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test user flow with discovered devices."""
    inject_bluetooth_service_info(hass, TEST_SERVICE_INFO)
    await hass.async_block_till_done()
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ADDRESS: TEST_ADDRESS}
    )
    await hass.async_block_till_done()
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Philips Hue Smart Plug"
    assert result["data"] == {CONF_ADDRESS: TEST_ADDRESS}
    assert len(mock_setup_entry.mock_calls) == 1


async def test_connection_error_during_confirm(hass: HomeAssistant) -> None:
    """Test connection error during confirmation."""
    with patch(
        "homeassistant.components.philips_hue.config_flow.BleakClient"
    ) as mock_client_class:
        mock_client = Mock()
        mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
        mock_client.is_connected = False
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=TEST_SERVICE_INFO,
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "confirm"
        
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"


from tests.common import MockConfigEntry

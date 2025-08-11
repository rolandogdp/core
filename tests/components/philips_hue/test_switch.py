"""Test the Philips Hue Bluetooth switch entity."""

from unittest.mock import AsyncMock

from homeassistant.components.philips_hue.switch import PhilipsSmartPlug
from homeassistant.core import HomeAssistant


async def test_async_turn_on_off_updates_state(hass: HomeAssistant) -> None:
    """Test turning the switch on and off updates state and calls device."""
    plug = PhilipsSmartPlug("aa:bb:cc:dd:ee:ff", name="Test Plug")
    plug._device.turn_on = AsyncMock()
    plug._device.turn_off = AsyncMock()

    await plug.async_turn_on()
    plug._device.turn_on.assert_awaited_once()
    assert plug.is_on

    await plug.async_turn_off()
    plug._device.turn_off.assert_awaited_once()
    assert not plug.is_on

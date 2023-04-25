"""File for the Interface Class for the Philips Hue Bluetooth Power Plug."""
import logging

from bleak import BleakClient, BleakScanner

from .const import DEFAULT_NAME, PLUG_STATE

_LOGGER = logging.getLogger(__name__)


async def discover():
    """Discovering Bluetooth Devices."""
    devices = await BleakScanner.discover()
    _LOGGER.debug("Discovered devices: %s", devices)
    return [device for device in devices if device.name.startswith(DEFAULT_NAME)]


class PhilipsHuePlug:
    """Interface Class for the Philips Hue Bluetooth Power Plug."""

    def __init__(self, mac, name) -> None:
        """Init function."""
        self._mac = mac
        self._name = name
        self.bleak_client = BleakClient(self._mac)
        self._paired = None

    def update_bleak_client(self, bleak_client: BleakClient):
        """Replace/update the bleakClient."""
        self.bleak_client = bleak_client

    def create_bleak_client(self, mac_or_ble_device):
        """Create a bleakClient."""
        self.bleak_client = BleakClient(mac_or_ble_device)

    async def pair(self):
        """Use the bleakClient to pair to the device."""
        paired = await self.bleak_client.pair(protection_level=2)
        if not paired:
            raise ConnectionError

    async def turn_on(self):
        """Use the paired bleakClient to send a turn on event."""
        await self.bleak_client.write_gatt_char(PLUG_STATE, b"\x01")

    async def turn_off(self):
        """Use the paired bleakClient to send a turn off event."""
        await self.bleak_client.write_gatt_char(PLUG_STATE, b"\x00")

    async def get_status(self):
        """Use the paired bleakClient to get current status."""
        status = await self.bleak_client.read_gatt_char(PLUG_STATE)
        if status == b"\x01":
            return True
        if status == b"\x00":
            return False
        raise ValueError

"""BLE scanner for FVTLED devices."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .const import BLE_DISCOVERY_UUID, BLE_NAME_PREFIX

_LOGGER = logging.getLogger(__name__)


@dataclass
class FVTLEDDeviceInfo:
    """Discovered FVTLED BLE device information."""

    address: str
    name: str
    rssi: int
    ble_device: BLEDevice
    advertisement: AdvertisementData
    service_uuids: list[str] = field(default_factory=list)


def _is_fvtled_device(device: BLEDevice, advertisement: AdvertisementData) -> bool:
    """Return True when the advertisement belongs to an FVTLED/MagicHome device.

    Detection criteria (either is sufficient):
    1. The device name starts with the expected prefix (``IOTWF``).
    2. The advertisement includes the FVTLED discovery service UUID (0x5A01).
    """
    name = device.name or ""
    if name.upper().startswith(BLE_NAME_PREFIX.upper()):
        return True
    uuids = [u.lower() for u in advertisement.service_uuids]
    return BLE_DISCOVERY_UUID.lower() in uuids


async def scan(
    timeout: float = 10.0,
) -> list[FVTLEDDeviceInfo]:
    """Scan for nearby FVTLED BLE devices.

    Args:
        timeout: BLE scan duration in seconds.

    Returns:
        List of :class:`FVTLEDDeviceInfo` objects for every discovered
        FVTLED device.
    """
    found: list[FVTLEDDeviceInfo] = []

    def _callback(device: BLEDevice, advertisement: AdvertisementData) -> None:
        if _is_fvtled_device(device, advertisement):
            _LOGGER.debug(
                "Discovered FVTLED device: %s (%s) RSSI=%d",
                device.name,
                device.address,
                advertisement.rssi,
            )
            found.append(
                FVTLEDDeviceInfo(
                    address=device.address,
                    name=device.name or "",
                    rssi=advertisement.rssi,
                    ble_device=device,
                    advertisement=advertisement,
                    service_uuids=list(advertisement.service_uuids),
                )
            )

    async with BleakScanner(detection_callback=_callback) as scanner:
        await scanner.wait_for(timeout=timeout)

    return found

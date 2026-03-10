"""Tests for the BLE scanner helpers."""

import pytest
from unittest.mock import MagicMock

from fvtled_control.scanner import _is_fvtled_device, FVTLEDDeviceInfo
from fvtled_control.const import BLE_DISCOVERY_UUID, BLE_NAME_PREFIX


def _make_device(name: str | None = None):
    device = MagicMock()
    device.name = name
    device.address = "AA:BB:CC:DD:EE:FF"
    return device


def _make_advertisement(service_uuids: list[str] | None = None, rssi: int = -60):
    adv = MagicMock()
    adv.service_uuids = service_uuids or []
    adv.rssi = rssi
    return adv


class TestIsFVTLEDDevice:
    def test_detects_by_name_prefix(self):
        device = _make_device("IOTWFE1B")
        adv = _make_advertisement()
        assert _is_fvtled_device(device, adv) is True

    def test_detects_by_name_prefix_lowercase(self):
        device = _make_device("iotwfe1b")
        adv = _make_advertisement()
        assert _is_fvtled_device(device, adv) is True

    def test_detects_by_discovery_uuid(self):
        device = _make_device(None)
        adv = _make_advertisement(service_uuids=[BLE_DISCOVERY_UUID])
        assert _is_fvtled_device(device, adv) is True

    def test_detects_by_discovery_uuid_uppercase(self):
        device = _make_device(None)
        adv = _make_advertisement(service_uuids=[BLE_DISCOVERY_UUID.upper()])
        assert _is_fvtled_device(device, adv) is True

    def test_ignores_unrelated_device_by_name(self):
        device = _make_device("SomeLED")
        adv = _make_advertisement()
        assert _is_fvtled_device(device, adv) is False

    def test_ignores_none_name_no_uuid(self):
        device = _make_device(None)
        adv = _make_advertisement()
        assert _is_fvtled_device(device, adv) is False

    def test_ignores_unrelated_uuid_only(self):
        device = _make_device(None)
        adv = _make_advertisement(service_uuids=["0000180a-0000-1000-8000-00805f9b34fb"])
        assert _is_fvtled_device(device, adv) is False

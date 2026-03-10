"""Tests for device state parsing and FVTLEDDevice logic."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from fvtled_control.device import DeviceState, FVTLEDDevice, _parse_status
from fvtled_control.const import (
    BLE_WRITE_CHARACTERISTIC_UUID,
    STATUS_POWER_ON_VALUE,
    STATUS_POWER_OFF_VALUE,
)


class TestParseStatus:
    def _make_status_bytes(
        self,
        power=STATUS_POWER_ON_VALUE,
        red=255,
        green=128,
        blue=64,
        brightness=200,
    ) -> bytes:
        # Pad to at least 10 bytes; meaningful offsets: 2, 6, 7, 8, 9
        data = bytearray(10)
        data[2] = power
        data[6] = red
        data[7] = green
        data[8] = blue
        data[9] = brightness
        return bytes(data)

    def test_parse_on(self):
        raw = self._make_status_bytes(power=STATUS_POWER_ON_VALUE)
        state = _parse_status(raw)
        assert state is not None
        assert state.is_on is True

    def test_parse_off(self):
        raw = self._make_status_bytes(power=STATUS_POWER_OFF_VALUE)
        state = _parse_status(raw)
        assert state is not None
        assert state.is_on is False

    def test_parse_rgb(self):
        raw = self._make_status_bytes(red=10, green=20, blue=30)
        state = _parse_status(raw)
        assert state is not None
        assert state.red == 10
        assert state.green == 20
        assert state.blue == 30
        assert state.rgb == (10, 20, 30)

    def test_parse_brightness(self):
        raw = self._make_status_bytes(brightness=77)
        state = _parse_status(raw)
        assert state is not None
        assert state.brightness == 77

    def test_too_short_returns_none(self):
        assert _parse_status(bytes(5)) is None

    def test_exact_length_works(self):
        raw = self._make_status_bytes()
        assert _parse_status(raw) is not None


class TestDeviceState:
    def test_rgb_property(self):
        state = DeviceState(is_on=True, red=1, green=2, blue=3, brightness=255)
        assert state.rgb == (1, 2, 3)


class TestFVTLEDDeviceConnect:
    """Unit tests that mock BleakClient."""

    def _make_mock_client(self, connected=True):
        client = AsyncMock()
        client.is_connected = connected
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.write_gatt_char = AsyncMock()
        client.read_gatt_char = AsyncMock(return_value=bytes(10))
        client.start_notify = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        mock_client = self._make_mock_client()
        with patch("fvtled_control.device.BleakClient", return_value=mock_client):
            device = FVTLEDDevice("AA:BB:CC:DD:EE:FF")
            await device.connect()
            assert device.is_connected
            await device.disconnect()
            mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        mock_client = self._make_mock_client()
        with patch("fvtled_control.device.BleakClient", return_value=mock_client):
            async with FVTLEDDevice("AA:BB:CC:DD:EE:FF") as device:
                assert device.is_connected
            mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_turn_on_sends_correct_command(self):
        from fvtled_control.commands import build_power_on_command

        mock_client = self._make_mock_client()
        with patch("fvtled_control.device.BleakClient", return_value=mock_client):
            async with FVTLEDDevice("AA:BB:CC:DD:EE:FF") as device:
                await device.turn_on()
        mock_client.write_gatt_char.assert_any_call(
            BLE_WRITE_CHARACTERISTIC_UUID,
            build_power_on_command(),
            response=False,
        )

    @pytest.mark.asyncio
    async def test_turn_off_sends_correct_command(self):
        from fvtled_control.commands import build_power_off_command

        mock_client = self._make_mock_client()
        with patch("fvtled_control.device.BleakClient", return_value=mock_client):
            async with FVTLEDDevice("AA:BB:CC:DD:EE:FF") as device:
                await device.turn_off()
        mock_client.write_gatt_char.assert_any_call(
            BLE_WRITE_CHARACTERISTIC_UUID,
            build_power_off_command(),
            response=False,
        )

    @pytest.mark.asyncio
    async def test_set_color_sends_correct_command(self):
        from fvtled_control.commands import build_color_command

        mock_client = self._make_mock_client()
        with patch("fvtled_control.device.BleakClient", return_value=mock_client):
            async with FVTLEDDevice("AA:BB:CC:DD:EE:FF") as device:
                await device.set_color(255, 0, 128)
        mock_client.write_gatt_char.assert_any_call(
            BLE_WRITE_CHARACTERISTIC_UUID,
            build_color_command(255, 0, 128),
            response=False,
        )

    @pytest.mark.asyncio
    async def test_set_brightness_sends_correct_command(self):
        from fvtled_control.commands import build_brightness_command

        mock_client = self._make_mock_client()
        with patch("fvtled_control.device.BleakClient", return_value=mock_client):
            async with FVTLEDDevice("AA:BB:CC:DD:EE:FF") as device:
                await device.set_brightness(200)
        mock_client.write_gatt_char.assert_any_call(
            BLE_WRITE_CHARACTERISTIC_UUID,
            build_brightness_command(200),
            response=False,
        )

    @pytest.mark.asyncio
    async def test_not_connected_raises(self):
        device = FVTLEDDevice("AA:BB:CC:DD:EE:FF")
        with pytest.raises(RuntimeError, match="not connected"):
            await device.turn_on()

    @pytest.mark.asyncio
    async def test_state_callback_invoked(self):
        mock_client = self._make_mock_client()
        received_states = []

        with patch("fvtled_control.device.BleakClient", return_value=mock_client):
            async with FVTLEDDevice("AA:BB:CC:DD:EE:FF") as device:
                device.add_state_callback(received_states.append)
                # Simulate an incoming BLE notification
                raw = bytearray(10)
                raw[2] = STATUS_POWER_ON_VALUE
                raw[6] = 255
                device._handle_notification(0, bytes(raw))

        assert len(received_states) == 1
        assert received_states[0].is_on is True
        assert received_states[0].red == 255

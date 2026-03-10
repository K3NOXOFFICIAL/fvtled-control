"""Tests for command building utilities."""

import pytest

from fvtled_control.commands import (
    build_brightness_command,
    build_color_command,
    build_power_off_command,
    build_power_on_command,
    build_status_query_command,
    _checksum,
)
from fvtled_control.const import (
    CMD_COLOR_PREFIX,
    CMD_COLOR_SUFFIX,
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CMD_POWER_PREFIX,
)


class TestChecksum:
    def test_zero_bytes(self):
        assert _checksum(bytes([0x00, 0x00])) == 0x00

    def test_known_sum(self):
        # 0x71 + 0x23 + 0x0F = 0xA3
        assert _checksum(bytes([0x71, 0x23, 0x0F])) == 0xA3

    def test_overflow_wraps(self):
        # 0xFF + 0x01 = 0x100 → 0x00 after mask
        assert _checksum(bytes([0xFF, 0x01])) == 0x00


class TestPowerCommands:
    def test_power_on_structure(self):
        cmd = build_power_on_command()
        assert len(cmd) == 4
        assert cmd[0] == CMD_POWER_PREFIX
        assert cmd[1] == CMD_POWER_ON
        assert cmd[2] == 0x0F
        assert cmd[3] == _checksum(cmd[:3])

    def test_power_off_structure(self):
        cmd = build_power_off_command()
        assert len(cmd) == 4
        assert cmd[0] == CMD_POWER_PREFIX
        assert cmd[1] == CMD_POWER_OFF
        assert cmd[2] == 0x0F
        assert cmd[3] == _checksum(cmd[:3])

    def test_power_on_checksum_correct(self):
        cmd = build_power_on_command()
        assert _checksum(cmd[:3]) == cmd[3]

    def test_power_off_checksum_correct(self):
        cmd = build_power_off_command()
        assert _checksum(cmd[:3]) == cmd[3]


class TestColorCommand:
    def test_structure(self):
        cmd = build_color_command(255, 128, 0)
        assert len(cmd) == 9
        assert cmd[0] == CMD_COLOR_PREFIX
        assert cmd[1] == 255
        assert cmd[2] == 128
        assert cmd[3] == 0
        assert cmd[6] == CMD_COLOR_SUFFIX
        assert cmd[7] == 0x0F
        assert cmd[8] == _checksum(cmd[:8])

    def test_black(self):
        cmd = build_color_command(0, 0, 0)
        assert cmd[1] == 0
        assert cmd[2] == 0
        assert cmd[3] == 0

    def test_white(self):
        cmd = build_color_command(255, 255, 255)
        assert cmd[1] == 255
        assert cmd[2] == 255
        assert cmd[3] == 255

    def test_checksum_correct(self):
        cmd = build_color_command(100, 200, 50)
        assert _checksum(cmd[:8]) == cmd[8]

    @pytest.mark.parametrize("channel,value", [
        ("red", -1),
        ("red", 256),
        ("green", -1),
        ("green", 256),
        ("blue", -1),
        ("blue", 256),
    ])
    def test_invalid_channel_raises(self, channel, value):
        kwargs = {"red": 0, "green": 0, "blue": 0}
        kwargs[channel] = value
        with pytest.raises(ValueError, match=channel):
            build_color_command(**kwargs)


class TestBrightnessCommand:
    def test_structure(self):
        cmd = build_brightness_command(200)
        assert len(cmd) == 9
        assert cmd[0] == CMD_COLOR_PREFIX
        assert cmd[4] == 200
        assert cmd[6] == CMD_COLOR_SUFFIX
        assert cmd[7] == 0x0F
        assert _checksum(cmd[:8]) == cmd[8]

    def test_zero_brightness(self):
        cmd = build_brightness_command(0)
        assert cmd[4] == 0

    def test_max_brightness(self):
        cmd = build_brightness_command(255)
        assert cmd[4] == 255

    def test_invalid_brightness_raises(self):
        with pytest.raises(ValueError, match="Brightness"):
            build_brightness_command(256)

    def test_negative_brightness_raises(self):
        with pytest.raises(ValueError, match="Brightness"):
            build_brightness_command(-1)


class TestStatusQueryCommand:
    def test_length(self):
        cmd = build_status_query_command()
        assert len(cmd) == 4

    def test_fixed_bytes(self):
        cmd = build_status_query_command()
        assert cmd[0] == 0x81
        assert cmd[1] == 0x8A
        assert cmd[2] == 0x8B

    def test_checksum(self):
        cmd = build_status_query_command()
        assert _checksum(cmd[:3]) == cmd[3]

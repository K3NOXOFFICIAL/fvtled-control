"""Command building utilities for FVTLED BLE devices."""

from __future__ import annotations

from .const import (
    CMD_COLOR_PREFIX,
    CMD_COLOR_SUFFIX,
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CMD_POWER_PREFIX,
    CMD_STATUS_QUERY,
)


def _checksum(data: bytes) -> int:
    """Return single-byte checksum: sum of all bytes masked to 0xFF."""
    return sum(data) & 0xFF


def build_power_on_command() -> bytes:
    """Build the command bytes to power on the device."""
    payload = bytes([CMD_POWER_PREFIX, CMD_POWER_ON, 0x0F])
    return payload + bytes([_checksum(payload)])


def build_power_off_command() -> bytes:
    """Build the command bytes to power off the device."""
    payload = bytes([CMD_POWER_PREFIX, CMD_POWER_OFF, 0x0F])
    return payload + bytes([_checksum(payload)])


def build_color_command(red: int, green: int, blue: int) -> bytes:
    """Build the command bytes to set an RGB color.

    Args:
        red: Red channel value (0–255).
        green: Green channel value (0–255).
        blue: Blue channel value (0–255).

    Returns:
        Byte string ready to be written to the BLE write characteristic.

    Raises:
        ValueError: If any channel value is outside the 0–255 range.
    """
    for name, value in (("red", red), ("green", green), ("blue", blue)):
        if not 0 <= value <= 255:
            raise ValueError(
                f"Color channel '{name}' must be between 0 and 255, got {value}"
            )
    payload = bytes(
        [CMD_COLOR_PREFIX, red, green, blue, 0x00, 0x00, CMD_COLOR_SUFFIX, 0x0F]
    )
    return payload + bytes([_checksum(payload)])


def build_brightness_command(brightness: int) -> bytes:
    """Build the command bytes to set brightness on a white-channel device.

    For RGB LED strips the brightness should be controlled by scaling the
    RGB values directly.  This command is provided for devices that expose
    a separate white/brightness channel (value byte at offset 4).

    Args:
        brightness: Brightness value (0–255).

    Returns:
        Byte string ready to be written to the BLE write characteristic.

    Raises:
        ValueError: If the brightness value is outside the 0–255 range.
    """
    if not 0 <= brightness <= 255:
        raise ValueError(
            f"Brightness must be between 0 and 255, got {brightness}"
        )
    payload = bytes(
        [CMD_COLOR_PREFIX, 0x00, 0x00, 0x00, brightness, 0x00, CMD_COLOR_SUFFIX, 0x0F]
    )
    return payload + bytes([_checksum(payload)])


def build_status_query_command() -> bytes:
    """Build the status query command bytes."""
    return CMD_STATUS_QUERY + bytes([_checksum(CMD_STATUS_QUERY)])

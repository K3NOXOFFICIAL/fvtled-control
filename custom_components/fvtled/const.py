"""Constants for the FVTLED ARZ-2100 BLE integration."""
from __future__ import annotations

DOMAIN = "fvtled"

# BLE service and characteristic UUIDs for FVTLED ARZ-2100
# Primary service with FFF0 prefix – common for LED BLE controllers
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
WRITE_CHARACTERISTIC_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_CHARACTERISTIC_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

# Device name patterns used for BLE discovery
LOCAL_NAME_STARTS = ("ARZ", "FVTLED")

# Config entry data keys
CONF_ADDRESS = "address"
CONF_NAME = "name"

# Reconnect / disconnect timer
DISCONNECT_DELAY = 120  # seconds

# Retry parameters
DEFAULT_ATTEMPTS = 3

# ------------------------------------------------------------------
# Command byte protocol (7E frame format)
# Frame: 7E [len] [cmd] [data…] [checksum] EF
# ------------------------------------------------------------------
PACKET_START = 0x7E
PACKET_END = 0xEF

# Power commands
CMD_POWER = 0x04
POWER_ON_PAYLOAD: bytes = bytes([0x7E, 0x04, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0xEF])
POWER_OFF_PAYLOAD: bytes = bytes(
    [0x7E, 0x04, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0xEF]
)

# RGB color command (cmd 0x05, type 0x03)
CMD_COLOR = 0x05
CMD_COLOR_TYPE_RGB = 0x03

# Brightness command (cmd 0x01)
CMD_BRIGHTNESS = 0x01

# State query command
STATE_QUERY_PAYLOAD: bytes = bytes([0x7E, 0x02, 0x10, 0x00, 0xEF])

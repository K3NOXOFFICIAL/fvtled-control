"""Constants for the FVTLED BLE Controller integration."""

DOMAIN = "fvtled"

# BLE Service UUIDs
BLE_SERVICE_UUID_PRIMARY = "0000ffff-0000-1000-8000-00805f9b34fb"
BLE_SERVICE_UUID_SECONDARY = "0000fe00-0000-1000-8000-00805f9b34fb"
BLE_SERVICE_UUID_ADVERTISEMENT = "00005a01-0000-1000-8000-00805f9b34fb"

# BLE Characteristic UUIDs (primary service)
BLE_CHAR_WRITE = "0000ff01-0000-1000-8000-00805f9b34fb"
BLE_CHAR_NOTIFY = "0000ff02-0000-1000-8000-00805f9b34fb"

# BLE Characteristic UUIDs (secondary service)
BLE_CHAR_WRITE_2 = "0000ff11-0000-1000-8000-00805f9b34fb"
BLE_CHAR_NOTIFY_2 = "0000ff22-0000-1000-8000-00805f9b34fb"

# Protocol command bytes
CMD_POWER_ON = bytes([0x71, 0x23, 0x0F])
CMD_POWER_OFF = bytes([0x71, 0x24, 0x0F])
CMD_GET_STATE = bytes([0x81, 0x8A, 0x8B])

# Color mode command prefix and suffix
CMD_COLOR_PREFIX = 0x56
CMD_COLOR_SUFFIX = bytes([0x00, 0xF0, 0xAA])

# Effect/mode constants
EFFECT_STATIC = 0x61
EFFECT_CUSTOM = 0x60

# Scan and connection timeouts (seconds)
SCAN_TIMEOUT = 10
CONNECT_TIMEOUT = 15
STATE_POLL_INTERVAL = 30
NOTIFY_RESPONSE_DELAY = 0.3

# Config entry keys
CONF_ADDRESS = "address"
CONF_NAME = "name"

# Default name prefix for discovered devices
DEFAULT_NAME = "FVTLED"

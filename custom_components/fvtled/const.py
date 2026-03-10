"""Constants for the FVTLED integration."""

DOMAIN = "fvtled"

# BLE advertisement service UUID used by FVTLED ARZ-2100 devices
BLE_ADV_SERVICE_UUID = "00005a01-0000-1000-8000-00805f9b34fb"

# BLE GATT service UUIDs
BLE_SERVICE_UUID_PRIMARY = "0000ffff-0000-1000-8000-00805f9b34fb"
BLE_SERVICE_UUID_SECONDARY = "0000fe00-0000-1000-8000-00805f9b34fb"

# BLE GATT characteristic UUIDs (primary service 0xFFFF)
CHAR_UUID_WRITE = "0000ff01-0000-1000-8000-00805f9b34fb"
CHAR_UUID_NOTIFY = "0000ff02-0000-1000-8000-00805f9b34fb"

# BLE GATT characteristic UUIDs (secondary service 0xFE00)
CHAR_UUID_WRITE_ALT = "0000ff11-0000-1000-8000-00805f9b34fb"
CHAR_UUID_NOTIFY_ALT = "0000ff22-0000-1000-8000-00805f9b34fb"

# Device name prefix used in BLE advertisements
BLE_DEVICE_NAME_PREFIX = "IOTWF"

# BLE protocol commands
CMD_POWER_ON = bytes([0x71, 0x23, 0x0F])
CMD_POWER_OFF = bytes([0x71, 0x24, 0x0F])

# Color command prefix and suffix
CMD_COLOR_PREFIX = 0x56
CMD_COLOR_SUFFIX = bytes([0x00, 0xF0, 0xAA])

# Status request command
CMD_STATUS_REQUEST = bytes([0xEF, 0x01, 0x77])

# Minimum brightness value (0-255)
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 255

# Default transition time (seconds)
DEFAULT_TRANSITION = 0.5

# Connection timeout (seconds)
CONNECTION_TIMEOUT = 10.0

# Reconnect interval (seconds)
RECONNECT_INTERVAL = 30.0

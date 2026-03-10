"""Constants for FVTLED ARZ-2100 integration."""

DOMAIN = "fvtled_arz2100"

# Default port for Zengge protocol
DEFAULT_PORT = 5577

# Device model info
DEVICE_MODEL = "ARZ-2100"
DEVICE_MANUFACTURER = "FVTLED"

# Protocol constants
PROTOCOL_VERSION = 9
STATUS_RESPONSE_LENGTH = 28  # This device uses 28-byte status response

# Command bytes
CMD_POWER_ON = 0x71
CMD_POWER_OFF = 0x71
CMD_SET_COLOR = 0x31
CMD_QUERY_STATUS = 0x81
CMD_SET_MODE = 0x61

# Response constants
RESPONSE_HEADER = 0x81

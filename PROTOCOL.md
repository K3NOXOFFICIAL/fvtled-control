# FVTLED ARZ-2100 Protocol Documentation

## Overview

The FVTLED ARZ-2100 uses a variant of the Zengge/MagicHome protocol (Version 9) with firmware `WF.52.B6.26.0,V9_ZG-BL-3KEY`. Some devices return **27-byte status responses** while others may return 28 bytes, different from the standard 14-byte implementation.

## Connection Details

- **Protocol**: TCP
- **Port**: 5577
- **Connection Type**: Local network (no cloud required)
- **Encryption**: None (plaintext)

## Command Structure

All commands follow this general structure:

```
[Command Byte] [Data Bytes...] [Checksum]
```

### Checksum Calculation

```python
def calculate_checksum(data: bytes) -> int:
    """Calculate checksum (sum of all bytes & 0xFF)"""
    return sum(data) & 0xFF
```

## Commands

### 1. Query Status (0x81)

**Request:**
```
81 8A 8B
```

**Response (27 or 28 bytes):**
```
81 [device_type] [power] [mode] [speed] [R] [G] [B] [W] [ext...] [checksum (optional)]
```

**Byte Breakdown:**

| Byte Index | Description | Values |
|------------|-------------|---------|
| 0 | Response header | Always `0x81` |
| 1 | Device type | `0x25` for RGBW |
| 2 | Power state | `0x23` = ON, `0x24` = OFF |
| 3 | Mode | `0x61` = static, others = effects |
| 4 | Speed | `0x00` - `0xFF` |
| 5 | Red value | `0x00` - `0xFF` |
| 6 | Green value | `0x00` - `0xFF` |
| 7 | Blue value | `0x00` - `0xFF` |
| 8 | White value | `0x00` - `0xFF` |
| 9-25/26 | Extended data | Device-specific |
| 26/27 | Checksum (optional) | Sum of previous bytes & 0xFF |

**Note:** Some device variants return 27 bytes, others return 28 bytes. The protocol accepts both.

**Example Response (Device ON, Red Color):**
```
81 25 23 61 1F FF 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5C
```

Parsing:
- Byte 0: `0x81` (header)
- Byte 2: `0x23` (power ON)
- Byte 5: `0xFF` (red = 255)
- Byte 6: `0x00` (green = 0)
- Byte 7: `0x00` (blue = 0)
- Byte 8: `0x00` (white = 0)

### 2. Power Control (0x71)

**Turn ON:**
```
71 23 0F A3
```

**Turn OFF:**
```
71 24 0F A4
```

**Format:**
- Byte 0: `0x71` (power command)
- Byte 1: `0x23` (ON) or `0x24` (OFF)
- Byte 2: `0x0F` (constant)
- Byte 3: Checksum

### 3. Set Color (0x31)

**Command Structure:**
```
31 [R] [G] [B] [W] 00 0F [checksum]
```

**Example - Red (255, 0, 0, 0):**
```
31 FF 00 00 00 00 0F 3F
```

**Example - White (0, 0, 0, 255):**
```
31 00 00 00 FF 00 0F 3F
```

**Example - Purple (128, 0, 128, 0):**
```
31 80 00 80 00 00 0F 1F
```

**Format:**
- Byte 0: `0x31` (color command)
- Byte 1: Red value (0-255)
- Byte 2: Green value (0-255)
- Byte 3: Blue value (0-255)
- Byte 4: White value (0-255)
- Byte 5: `0x00` (reserved)
- Byte 6: `0x0F` (constant)
- Byte 7: Checksum (sum of bytes 0-6 & 0xFF)

### 4. Set Mode/Effect (0x61)

**Command Structure:**
```
61 [mode] [speed] 0F [checksum]
```

**Common Modes:**
- `0x25`: Seven color cross fade
- `0x26`: Red gradual change
- `0x27`: Green gradual change
- `0x28`: Blue gradual change
- `0x29`: Yellow gradual change
- `0x2A`: Cyan gradual change
- `0x2B`: Purple gradual change
- `0x2C`: White gradual change
- `0x2D`: Red/Green cross fade
- `0x2E`: Red/Blue cross fade
- `0x2F`: Green/Blue cross fade

**Speed:** `0x01` (slowest) to `0x1F` (fastest)

## Protocol Analysis Tools

### Python Test Script

```python
import socket

def send_command(host, port, command):
    """Send command and receive response"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)  # Increased timeout for reliability

    try:
        sock.connect((host, port))
        sock.send(bytes(command))
        response = sock.recv(28)  # Read up to 28 bytes (device may return 27 or 28)
        return response
    finally:
        sock.close()

# Test status query
host = "192.168.178.236"
port = 5577

# Query status
response = send_command(host, port, [0x81, 0x8A, 0x8B])
print(f"Status: {response.hex()}")
print(f"Response length: {len(response)} bytes")
print(f"Power: {'ON' if response[2] == 0x23 else 'OFF'}")
print(f"RGB: ({response[5]}, {response[6]}, {response[7]})")
print(f"White: {response[8]}")

# Turn on
response = send_command(host, port, [0x71, 0x23, 0x0F, 0xA3])

# Set red color
response = send_command(host, port, [0x31, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x3F])
```

### netcat Test

```bash
# Query status
echo -ne "\x81\x8A\x8B" | nc 192.168.178.236 5577 | xxd

# Turn on
echo -ne "\x71\x23\x0F\xA3" | nc 192.168.178.236 5577

# Set red color
echo -ne "\x31\xFF\x00\x00\x00\x00\x0F\x3F" | nc 192.168.178.236 5577
```

### Wireshark Filter

```
tcp.port == 5577
```

## Differences from Standard Zengge Protocol

### Standard Protocol (14-byte response)
```
81 [type] [power] [mode] [speed] [R] [G] [B] [W] 00 [version] 00 00 [checksum]
```

### Extended Protocol (27-byte response)
```
81 [type] [power] [mode] [speed] [R] [G] [B] [W] ... (27 bytes total)
```

### ARZ-2100 Protocol (27 or 28-byte response)
```
81 [type] [power] [mode] [speed] [R] [G] [B] [W] ... (27 or 28 bytes total)
```

**Key Issue:** Standard libraries expect responses up to 14 or 27 bytes. The ARZ-2100 may return 27 or 28 bytes depending on the device variant. This implementation accepts both lengths.

## Firmware Information

From device logs:

```
Firmware: WF.52.B6.26.0,V9_ZG-BL-3KEY
Build Date: B6_26_20240514_ZG-BL-3KEY
Module ID: AK001-ZJ21413
Product ID: 182
```

**Protocol Version:** 9 (ZG-BL-3KEY variant)

## Device Discovery

The device can be discovered via:

1. **UDP Broadcast** (standard Zengge method):
   - Broadcast: `HF-A11ASSISTHREAD`
   - Port: 48899
   - Response contains IP and MAC

2. **MQTT Cloud** (optional):
   - Broker: `mqttus.magichue.net:1883`
   - Topics:
     - Subscribe: `TCP_WF/2020637058179182593/+/device`
     - Subscribe: `SIG_M_GW/2020637058179182593/+/device`

3. **BLE** (not implemented in this integration):
   - Service UUID: Custom Zengge BLE service
   - Characteristics: Control and status

## Error Handling

### Connection Errors

```python
try:
    sock.connect((host, port))
except socket.timeout:
    # Device not reachable
    pass
except ConnectionRefusedError:
    # Port closed or device off
    pass
except OSError:
    # Network error
    pass
```

### Response Validation

```python
def validate_response(response: bytes) -> bool:
    """Validate 27 or 28-byte response"""
    if len(response) < 27:
        return False
    if response[0] != 0x81:  # Check header
        return False
    # Note: Checksum validation optional as some devices return 27 bytes without checksum
    return True
```

## Performance Characteristics

- **Connection Time**: ~100-200ms
- **Command Response**: ~50-100ms
- **Status Query**: ~100-150ms
- **Reconnection Overhead**: ~200-300ms

**Recommendation:** Keep connection alive if sending multiple commands, or use single connection per command.

## Integration Testing

### Unit Tests

```python
def test_checksum():
    data = bytes([0x71, 0x23, 0x0F])
    assert calculate_checksum(data) == 0xA3

def test_power_on_command():
    cmd = bytes([0x71, 0x23, 0x0F, 0xA3])
    assert len(cmd) == 4
    assert cmd[3] == calculate_checksum(cmd[0:3])

def test_color_command():
    # Red color
    cmd = bytes([0x31, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x0F])
    checksum = calculate_checksum(cmd)
    full_cmd = cmd + bytes([checksum])
    assert full_cmd == bytes([0x31, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x3F])
```

### Integration Tests

```python
async def test_device_connection():
    protocol = FVTLEDARZ2100Protocol("192.168.178.236")
    assert await protocol.async_test_connection()

async def test_power_control():
    protocol = FVTLEDARZ2100Protocol("192.168.178.236")
    assert await protocol.async_turn_on()
    await asyncio.sleep(1)
    status = await protocol.async_get_status()
    assert status["power"] == True

async def test_color_change():
    protocol = FVTLEDARZ2100Protocol("192.168.178.236")
    await protocol.async_set_color(255, 0, 0, 0, 255)
    await asyncio.sleep(1)
    status = await protocol.async_get_status()
    assert status["red"] == 255
    assert status["green"] == 0
    assert status["blue"] == 0
```

## Known Limitations

1. **No Authentication**: Protocol has no security/authentication
2. **Single Connection**: Device may have issues with concurrent connections
3. **No State Confirmation**: Commands don't return success/failure
4. **Limited Error Info**: No detailed error messages from device
5. **BLE Not Supported**: This integration only uses WiFi/TCP

## Future Enhancements

Potential improvements:

1. **BLE Support**: Add Bluetooth Low Energy control
2. **Effects**: Implement built-in effects (pulse, strobe, etc.)
3. **Scenes**: Support for saving/recalling color scenes
4. **Transitions**: Smooth color transitions
5. **Music Sync**: Sync with music (if device supports)

## References

- [Home Assistant Light Platform](https://developers.home-assistant.io/docs/core/entity/light)
- [Zengge Protocol (GitHub)](https://github.com/vikstrous/zengge-lightcontrol)
- [flux_led Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/flux_led)

## Contributing

If you discover additional protocol features or commands, please contribute to this documentation via pull request.

## License

MIT License - See LICENSE file for details

# FVTLED ARZ-2100 Home Assistant Integration

Custom Home Assistant integration for the FVTLED ARZ-2100 RGB controller that supports the newer 28-byte Zengge protocol.

## Overview

The FVTLED ARZ-2100 uses a newer version (v9) of the Zengge/MagicHome protocol with firmware `WF.52.B6.26.0,V9_ZG-BL-3KEY`. This device responds with 28-byte status packets instead of the standard 14 or 27 bytes, which causes compatibility issues with standard flux_led integrations.

### Device Specifications

| Parameter | Value |
|-----------|-------|
| Model | ARZ-2100 |
| Manufacturer | FVTLED |
| Protocol | Zengge TCP_WF v9 |
| Connection | WiFi (TCP Port 5577) |
| Color Mode | RGBW |
| Firmware | WF.52.B6.26.0,V9_ZG-BL-3KEY |
| Response Length | 28 bytes |

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/fvtled_arz2100` directory to your Home Assistant `config/custom_components/` directory:

```bash
cd /config
mkdir -p custom_components
cp -r /path/to/fvtled-control/custom_components/fvtled_arz2100 custom_components/
```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "FVTLED ARZ-2100"

5. Enter your device's IP address (e.g., `192.168.178.236`)

### Method 2: HACS Installation (Future)

This integration can be installed via HACS once it's published:

1. Open HACS
2. Go to "Integrations"
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add this repository URL
6. Install "FVTLED ARZ-2100"

## Configuration

### Prerequisites

1. **Set Static IP**: Configure your router to assign a static IP address to the FVTLED ARZ-2100 device using DHCP reservation for MAC address `24:94:94:11:8E:1B` (or your device's MAC address).

2. **Verify Network Connectivity**: Ensure the device is connected to your WiFi network and accessible from your Home Assistant instance.

3. **Test Connection**: You can verify the device is reachable using:
   ```bash
   nmap -p 5577 <device-ip>
   ```
   Port 5577 should show as "open".

### Adding the Device

1. Navigate to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "FVTLED ARZ-2100"
4. Enter the following information:
   - **IP Address**: The static IP of your device (e.g., `192.168.178.236`)
   - **Device Name**: A friendly name for your device (e.g., "Living Room RGB Strip")

## Features

- ✅ Turn on/off
- ✅ Set RGB colors
- ✅ Set white channel
- ✅ Adjust brightness
- ✅ Full RGBW color control
- ✅ Status polling
- ✅ 28-byte protocol support

## Usage Example

### Automations

```yaml
automation:
  - alias: "Turn on RGB strip at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.fvtled_arz_2100
        data:
          brightness: 200
          rgbw_color: [255, 100, 0, 0]  # Orange color
```

### Scripts

```yaml
script:
  party_mode:
    sequence:
      - service: light.turn_on
        target:
          entity_id: light.fvtled_arz_2100
        data:
          brightness: 255
          rgbw_color: [255, 0, 255, 0]  # Purple
```

## Troubleshooting

### Device Not Responding

1. **Check Network Connection**:
   - Verify the device is powered on
   - Ensure it's connected to your WiFi network
   - Ping the device IP from Home Assistant: `ping <device-ip>`

2. **Check Port Accessibility**:
   ```bash
   nmap -p 5577 <device-ip>
   ```

3. **Verify Static IP**:
   - Make sure the device hasn't changed IP addresses
   - Set up DHCP reservation in your router

### Integration Not Loading

1. Check Home Assistant logs for errors:
   ```bash
   tail -f /config/home-assistant.log | grep fvtled
   ```

2. Verify all files are in the correct location:
   ```
   /config/custom_components/fvtled_arz2100/
   ├── __init__.py
   ├── config_flow.py
   ├── const.py
   ├── light.py
   ├── manifest.json
   ├── protocol.py
   └── translations/
       ├── en.json
       └── de.json
   ```

3. Restart Home Assistant after installation

### Colors Not Accurate

The device uses RGBW mode. If colors appear incorrect:
- Adjust the white channel value
- Use the RGBW color picker in Home Assistant
- Example: Pure red = `[255, 0, 0, 0]`, Warm white = `[0, 0, 0, 255]`

## Technical Details

### Protocol Information

The FVTLED ARZ-2100 uses the Zengge/MagicHome protocol with these characteristics:

- **Port**: TCP 5577
- **Protocol Version**: 9 (ZG-BL-3KEY)
- **Status Response**: 28 bytes

#### Status Response Format (28 bytes)

| Byte | Description |
|------|-------------|
| 0 | Response header (0x81) |
| 1 | Device type |
| 2 | Power state (0x23=on, 0x24=off) |
| 3 | Mode |
| 4 | Speed |
| 5 | Red value (0-255) |
| 6 | Green value (0-255) |
| 7 | Blue value (0-255) |
| 8 | White value (0-255) |
| 9-26 | Extended data |
| 27 | Checksum |

#### Command Format

Commands use the standard Zengge format with checksums:

- **Power On**: `71 23 0F A3`
- **Power Off**: `71 24 0F A4`
- **Query Status**: `81 8A 8B`
- **Set Color**: `31 RR GG BB WW 00 0F CS` (CS = checksum)

## Known Issues

1. **28-Byte Response**: The standard flux_led and MagicHome integrations expect 14 or 27-byte responses and will fail with this device. This custom integration specifically handles the 28-byte response.

2. **MQTT Cloud**: The device also supports cloud control via `mqttus.magichue.net`, but this integration only uses local TCP control for better reliability and privacy.

3. **BLE Support**: This integration currently only supports WiFi/TCP control. BLE support may be added in the future.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

- **Issues**: [GitHub Issues](https://github.com/K3NOXOFFICIAL/fvtled-control/issues)
- **Discussions**: [GitHub Discussions](https://github.com/K3NOXOFFICIAL/fvtled-control/discussions)

## License

This project is licensed under the MIT License.

## Credits

Developed based on analysis of FVTLED ARZ-2100 logcat data and reverse engineering of the Zengge/MagicHome protocol v9.

## Related Links

- [Home Assistant](https://www.home-assistant.io/)
- [flux_led (Original Integration)](https://github.com/home-assistant/core/tree/dev/homeassistant/components/flux_led)
- [Zengge Protocol Documentation](https://github.com/vikstrous/zengge-lightcontrol)

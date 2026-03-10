# fvtled-control

A Home Assistant custom integration for controlling **FVTLED ARZ-2100** RGB LED
controllers via Bluetooth Low Energy (BLE).

## Supported Devices

| Device | BLE Name | Connectivity |
|--------|----------|-------------|
| FVTLED ARZ-2100 | `IOTWF*` (e.g. `IOTWFE1B`) | BLE + WiFi |

### BLE Profile

| Parameter | Value |
|-----------|-------|
| Advertisement Service UUID | `0x5A01` |
| Primary Service UUID | `0xFFFF` |
| Write Characteristic | `0xFF01` |
| Notify Characteristic | `0xFF02` |
| Secondary Service UUID | `0xFE00` |
| Write Characteristic (alt) | `0xFF11` |
| Notify Characteristic (alt) | `0xFF22` |

## Installation

1. Copy the `custom_components/fvtled/` directory into your Home Assistant
   `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and search for
   **FVTLED**.
4. Select your FVTLED device from the list of discovered BLE devices and follow
   the prompts.

## Requirements

- Home Assistant 2024.1 or newer
- A Bluetooth adapter recognised by Home Assistant
- The FVTLED ARZ-2100 device must be powered on and within Bluetooth range

## Features

- **Auto-discovery** – detected automatically when the device is in range
- **Power on/off**
- **RGB color control**
- **Brightness control**
- **Real-time status** via BLE notifications
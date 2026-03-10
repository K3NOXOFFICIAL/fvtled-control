# fvtled-control

A Home Assistant custom integration for the **FVTLED ARZ-2100 RGB LED controller** using Bluetooth Low Energy (BLE).

Standard integrations like Magic Home / flux_led use a TCP/Wi-Fi protocol that this device does not speak. This integration communicates directly over BLE using the device's GATT profile.

---

## Supported Devices

| Device | Protocol | BLE Name |
|--------|----------|----------|
| FVTLED ARZ-2100 | BLE (GATT) | `IOTWFE1B` / `IOTWFxxxx` |

---

## BLE GATT Profile

| Role | UUID |
|------|------|
| Advertisement service | `00005a01-0000-1000-8000-00805f9b34fb` |
| Primary service | `0000ffff-0000-1000-8000-00805f9b34fb` |
| Write characteristic | `0000ff01-0000-1000-8000-00805f9b34fb` |
| Notify characteristic | `0000ff02-0000-1000-8000-00805f9b34fb` |
| Secondary service | `0000fe00-0000-1000-8000-00805f9b34fb` |
| Write characteristic 2 | `0000ff11-0000-1000-8000-00805f9b34fb` |
| Notify characteristic 2 | `0000ff22-0000-1000-8000-00805f9b34fb` |

---

## Installation

### HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/K3NOXOFFICIAL/fvtled-control` as an **Integration**
3. Install **FVTLED BLE Controller** and restart Home Assistant

### Manual

1. Copy the `custom_components/fvtled` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **FVTLED BLE Controller**
3. The integration will auto-discover the device if it is advertising; otherwise enter the Bluetooth MAC address manually (e.g. `24:94:94:11:8E:1B`)
4. Confirm to create the device

The controller appears as a **light** entity supporting:
- On / Off
- RGB colour
- Brightness

---

## Requirements

- Home Assistant 2024.1 or newer
- A Bluetooth adapter accessible to Home Assistant (built-in or USB dongle)
- FVTLED ARZ-2100 device powered on and within Bluetooth range
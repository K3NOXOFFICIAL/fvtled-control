# fvtled-control

A Python library for controlling **FVTLED ARZ-2100 RGB** LED strips over
Bluetooth Low Energy (BLE).

## Device identification

FVTLED ARZ-2100 RGB devices advertise over BLE with:

| BLE field | Value |
|-----------|-------|
| Device name prefix | `IOTWF` (e.g. `IOTWFE1B`) |
| Discovery service UUID | `0x5A01` |
| Control service UUID | `0xFFFF` |
| Write characteristic | `0xFF01` |
| Notify characteristic | `0xFF02` |
| Status service UUID | `0xFE00` |
| Status write characteristic | `0xFF11` |
| Status notify characteristic | `0xFF22` |

## Requirements

- Python 3.10+
- [`bleak`](https://github.com/hbldh/bleak) ≥ 0.21 (cross-platform BLE library)

## Installation

```bash
pip install fvtled-control
```

## Quick start

```python
import asyncio
from fvtled_control import FVTLEDDevice, scan

async def main():
    # Discover nearby FVTLED devices
    devices = await scan(timeout=10.0)
    for info in devices:
        print(f"Found: {info.name} @ {info.address} (RSSI {info.rssi} dBm)")

    if not devices:
        print("No FVTLED devices found.")
        return

    # Connect to the first discovered device and control it
    async with FVTLEDDevice(devices[0].ble_device) as device:
        await device.turn_on()
        await device.set_color(255, 0, 0)   # Red
        await asyncio.sleep(1)
        await device.set_color(0, 255, 0)   # Green
        await asyncio.sleep(1)
        await device.set_color(0, 0, 255)   # Blue
        await asyncio.sleep(1)
        await device.turn_off()

asyncio.run(main())
```

## API reference

### `scan(timeout=10.0) → list[FVTLEDDeviceInfo]`

Scans for nearby FVTLED BLE devices.  Returns a list of
`FVTLEDDeviceInfo` objects each containing `address`, `name`, `rssi`,
`ble_device`, and `service_uuids`.

### `FVTLEDDevice(address_or_ble_device, *, connection_timeout=20.0)`

Async controller for an FVTLED device.  Can be used as an async context
manager (recommended) or by calling `connect()` / `disconnect()` manually.

| Method | Description |
|--------|-------------|
| `connect()` | Establish BLE connection and subscribe to notifications |
| `disconnect()` | Close the BLE connection |
| `turn_on()` | Power the device on |
| `turn_off()` | Power the device off |
| `set_color(red, green, blue)` | Set RGB color (values 0–255) |
| `set_brightness(brightness)` | Set brightness via white channel (0–255) |
| `get_state()` | Query and return current `DeviceState` |
| `add_state_callback(cb)` | Register a callback for state change notifications |
| `remove_state_callback(cb)` | Unregister a state callback |

### `DeviceState`

Dataclass with fields: `is_on`, `red`, `green`, `blue`, `brightness`, and
the convenience property `rgb → tuple[int, int, int]`.

## Running tests

```bash
pip install -e ".[dev]"
pytest
```
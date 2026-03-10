# fvtled-control

A [Home Assistant](https://www.home-assistant.io/) custom integration for the **FVTLED ARZ-2100** RGB LED controller.  
The ARZ-2100 communicates via **Bluetooth Low Energy (BLE)** and is **not** compatible with the standard Magic Home / Flux LED protocols.  
This integration reverse-engineers the proprietary `0x7E` BLE command protocol used by the official FVTLED app.

---

## Supported Devices

| Brand  | Model    | Connection |
|--------|----------|------------|
| FVTLED | ARZ-2100 | BLE / LE   |

Other FVTLED BLE controllers that advertise their name starting with `ARZ` or `FVTLED` may also work.

---

## Features

- ✅ Turn on / off
- ✅ Set RGB colour
- ✅ Set brightness
- ✅ Auto-discovery via Home Assistant Bluetooth integration
- ✅ Config flow (set up entirely through the Home Assistant UI)
- ✅ Works with ESPHome Bluetooth proxy

---

## Requirements

- Home Assistant 2023.8 or later
- The **Bluetooth** integration enabled in Home Assistant
- A Bluetooth adapter within range of the ARZ-2100 (or an [ESPHome BLE proxy](https://esphome.io/components/bluetooth_proxy.html))

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → **⋮** → **Custom repositories**.
2. Add `https://github.com/K3NOXOFFICIAL/fvtled-control` as an **Integration**.
3. Search for **FVTLED ARZ-2100 BLE** and install it.
4. Restart Home Assistant.

### Manual

1. Download or clone this repository.
2. Copy the `custom_components/fvtled` folder into your Home Assistant
   `<config>/custom_components/` directory.
3. Restart Home Assistant.

---

## Setup

1. Make sure the **Bluetooth** integration is active and your ARZ-2100 is
   powered on and within Bluetooth range.
2. Home Assistant should automatically discover the device. Accept the
   notification, or go to **Settings → Devices & Services → + Add Integration**
   and search for **FVTLED ARZ-2100 BLE**.
3. Confirm the device and it will appear as a **light** entity.

---

## BLE Protocol

The ARZ-2100 uses a simple framed binary protocol over BLE:

| Operation  | Payload (hex)                          |
|------------|----------------------------------------|
| Power ON   | `7E 04 04 01 00 00 00 00 EF`          |
| Power OFF  | `7E 04 04 00 00 00 00 00 EF`          |
| Set RGB    | `7E 07 05 03 RR GG BB 00 EF`          |
| Brightness | `7E 04 01 <level 0-FF> 00 00 00 00 EF`|

Commands are written to GATT characteristic  
`0000fff3-0000-1000-8000-00805f9b34fb`  
under service `0000fff0-0000-1000-8000-00805f9b34fb`.

---

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| Device not discovered | Bring the device closer to the Bluetooth adapter. Make sure it is powered on. |
| Connection fails | Restart the ARZ-2100 (power cycle). If you have other apps connected, close them first – BLE devices typically allow only one connection at a time. |
| Commands not working | Open an issue and attach your `home-assistant.log` entries for the `fvtled` component (`logger: default: info, logs: custom_components.fvtled: debug`). |

---

## Contributing

Pull requests and bug reports are welcome!  
Please open an issue first to discuss any major changes.

---

## License

MIT License – see [LICENSE](LICENSE) for details.

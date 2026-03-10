# Installation und Einrichtung / Installation and Setup

## Übersicht / Overview

Diese Integration ermöglicht die lokale Steuerung des FVTLED ARZ-2100 RGB Controllers über Home Assistant.

This integration enables local control of the FVTLED ARZ-2100 RGB Controller via Home Assistant.

---

## Installation Steps

### Schritt 1: Dateien kopieren / Step 1: Copy Files

```
Home Assistant Verzeichnisstruktur / Directory Structure:
config/
├── configuration.yaml
├── custom_components/          ← Hier kopieren / Copy here
│   └── fvtled_arz2100/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── const.py
│       ├── light.py
│       ├── manifest.json
│       ├── protocol.py
│       └── translations/
│           ├── de.json
│           └── en.json
```

**Befehl / Command:**
```bash
# Von diesem Repository / From this repository
cd /config
mkdir -p custom_components
cp -r /path/to/fvtled-control/custom_components/fvtled_arz2100 custom_components/

# Oder via wget
wget https://github.com/K3NOXOFFICIAL/fvtled-control/archive/refs/heads/main.zip
unzip main.zip
cp -r fvtled-control-main/custom_components/fvtled_arz2100 custom_components/
```

### Schritt 2: Neustart / Step 2: Restart

Home Assistant neu starten / Restart Home Assistant:
- **Einstellungen** → **System** → **Neu starten**
- **Settings** → **System** → **Restart**

### Schritt 3: Netzwerk vorbereiten / Step 3: Prepare Network

#### 3a. Gerät im Netzwerk finden / Find Device in Network

Verwende die FVTLED App, um die IP-Adresse zu finden, oder scanne dein Netzwerk:

Use the FVTLED app to find the IP address, or scan your network:

```bash
# Option 1: nmap
nmap -p 5577 192.168.178.0/24

# Option 2: arp-scan
sudo arp-scan --localnet | grep 24:94:94

# Option 3: Router-Oberfläche / Router Interface
# Suche nach Gerät mit MAC: 24:94:94:11:8E:1B
# Look for device with MAC: 24:94:94:11:8E:1B
```

#### 3b. Statische IP einrichten / Setup Static IP

**Fritz!Box (Deutsch):**
1. http://fritz.box öffnen
2. **Heimnetz** → **Netzwerk** → **Netzwerkverbindungen**
3. Gerät mit MAC `24:94:94:11:8E:1B` finden
4. Stift-Symbol klicken → **Immer gleiche IPv4-Adresse zuweisen**
5. IP-Adresse festlegen (z.B. `192.168.178.236`)

**Generic Router (English):**
1. Open router web interface
2. Find **DHCP** or **LAN** settings
3. Look for **DHCP Reservation** or **Static IP**
4. Add entry:
   - MAC Address: `24:94:94:11:8E:1B`
   - IP Address: `192.168.178.236` (or your preferred IP)
5. Save and reboot device

### Schritt 4: Integration hinzufügen / Step 4: Add Integration

#### Home Assistant UI:

1. **Einstellungen / Settings** → **Geräte & Dienste / Devices & Services**

2. Klicke / Click **+ Integration hinzufügen / + Add Integration**

3. Suche / Search: `FVTLED ARZ-2100`

4. Eingabe / Enter:
   - **IP-Adresse / IP Address**: `192.168.178.236` (deine Geräte-IP / your device IP)
   - **Gerätename / Device Name**: `Wohnzimmer LED / Living Room LED` (optional)

5. **Absenden / Submit** klicken / click

### Schritt 5: Testen / Step 5: Test

#### UI Test:

1. Gehe zu / Go to **Übersicht / Overview**
2. Finde die neue Licht-Entity / Find the new light entity
3. Klicke / Click the light icon to toggle on/off
4. Klicke / Click **Einstellungen / Settings** (gear icon)
5. Ändere Farbe und Helligkeit / Change color and brightness

#### Service Call Test (Developer Tools):

```yaml
# Einschalten mit Farbe / Turn on with color
service: light.turn_on
target:
  entity_id: light.fvtled_arz_2100
data:
  brightness: 200
  rgbw_color: [255, 0, 0, 0]  # Rot / Red
```

---

## Fehlerbehebung / Troubleshooting

### Problem: Integration wird nicht angezeigt / Integration not showing

**Lösung / Solution:**

1. Überprüfe Dateien / Check files:
```bash
ls -la /config/custom_components/fvtled_arz2100/
# Should show: __init__.py, config_flow.py, const.py, light.py, manifest.json, protocol.py, translations/
```

2. Prüfe Logs / Check logs:
```bash
tail -f /config/home-assistant.log | grep fvtled
```

3. Neustart erzwingen / Force restart:
   - Cache löschen / Clear cache
   - Home Assistant komplett neu starten / Full restart Home Assistant

### Problem: Gerät nicht gefunden / Device not found

**Diagnose / Diagnosis:**

```bash
# 1. Ping Test
ping 192.168.178.236

# 2. Port Test
nmap -p 5577 192.168.178.236
# Expected: 5577/tcp open

# 3. Telnet Test
telnet 192.168.178.236 5577
# Expected: Connection established
```

**Lösungen / Solutions:**

- ❌ **Ping erfolgreich, Port geschlossen** / Ping works, port closed
  - Gerät neu starten / Restart device
  - Firewall prüfen / Check firewall

- ❌ **Ping fehlschlägt** / Ping fails
  - IP-Adresse überprüfen / Check IP address
  - WLAN-Verbindung prüfen / Check WiFi connection
  - Gerät mit App neu einrichten / Re-setup device with app

### Problem: Farben falsch / Colors incorrect

Das Gerät verwendet RGBW (4 Kanäle) / Device uses RGBW (4 channels):

```yaml
# Format: [Red, Green, Blue, White]
# Beispiele / Examples:

Reines Rot / Pure Red:        [255, 0, 0, 0]
Reines Grün / Pure Green:     [0, 255, 0, 0]
Reines Blau / Pure Blue:      [0, 0, 255, 0]
Weißes Licht / White Light:   [0, 0, 0, 255]
Warmweiß / Warm White:        [255, 200, 100, 100]
Kaltweiß / Cool White:        [200, 200, 255, 200]
```

### Problem: Verbindung bricht ab / Connection drops

**Kurzfristig / Short-term:**
```bash
# Gerät neu verbinden / Reconnect device
service: homeassistant.reload_config_entry
target:
  entry_id: <your_entry_id>
```

**Langfristig / Long-term:**
- Statische IP sicherstellen / Ensure static IP
- WiFi-Signalstärke verbessern / Improve WiFi signal
- 2.4 GHz Band verwenden / Use 2.4 GHz band (not 5 GHz)

---

## Erweiterte Konfiguration / Advanced Configuration

### Service Calls

```yaml
# Einschalten / Turn On
service: light.turn_on
target:
  entity_id: light.fvtled_arz_2100
data:
  brightness: 255          # 0-255
  rgbw_color: [255, 0, 0, 0]

# Ausschalten / Turn Off
service: light.turn_off
target:
  entity_id: light.fvtled_arz_2100

# Toggle
service: light.toggle
target:
  entity_id: light.fvtled_arz_2100
```

### Entities

Nach der Installation verfügbar / Available after installation:

- `light.fvtled_arz_2100` - Hauptlicht-Entity / Main light entity

### Attributes

```yaml
# Attribute ansehen / View attributes
{{ state_attr('light.fvtled_arz_2100', 'brightness') }}
{{ state_attr('light.fvtled_arz_2100', 'rgbw_color') }}
{{ state_attr('light.fvtled_arz_2100', 'supported_color_modes') }}
```

---

## Performance-Tipps / Performance Tips

1. **Polling-Intervall** anpassen / Adjust polling interval
   - Standard / Default: 30 Sekunden / seconds
   - Für schnellere Updates / For faster updates: custom scan_interval

2. **Netzwerk optimieren** / Optimize network
   - Gerät nah am Router / Device close to router
   - 2.4 GHz WLAN verwenden / Use 2.4 GHz WiFi
   - Statische IP verwenden / Use static IP

3. **Automationen** / Automations
   - Mehrere Farbwechsel zu Szenen kombinieren / Combine multiple color changes into scenes
   - Verzögerungen zwischen Befehlen / Delays between commands

---

## Deinstallation / Uninstallation

1. Integration entfernen / Remove integration:
   - **Einstellungen** → **Geräte & Dienste** → **FVTLED ARZ-2100** → **Löschen**
   - **Settings** → **Devices & Services** → **FVTLED ARZ-2100** → **Delete**

2. Dateien löschen / Delete files:
```bash
rm -rf /config/custom_components/fvtled_arz2100
```

3. Home Assistant neu starten / Restart Home Assistant

---

## Weitere Hilfe / Further Help

- **GitHub Issues**: [fvtled-control/issues](https://github.com/K3NOXOFFICIAL/fvtled-control/issues)
- **Home Assistant Community**: [community.home-assistant.io](https://community.home-assistant.io/)
- **Dokumentation / Documentation**: [README.md](README.md)

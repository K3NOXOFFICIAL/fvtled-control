# Schnellstart-Anleitung / Quick Start Guide

## Deutsch

### FVTLED ARZ-2100 in Home Assistant einbinden

Diese Anleitung hilft dir, deinen FVTLED ARZ-2100 RGB Controller in Home Assistant zu integrieren.

#### Schritt 1: Installation

1. **Dateien kopieren**
   - Lade dieses Repository herunter
   - Kopiere den Ordner `custom_components/fvtled_arz2100` in dein Home Assistant `config/custom_components/` Verzeichnis

2. **Home Assistant neu starten**
   - Gehe zu **Einstellungen** → **System** → **Neu starten**

#### Schritt 2: Gerät konfigurieren

1. **Statische IP-Adresse einrichten**
   - Öffne deine Router-Einstellungen
   - Suche nach DHCP-Reservierung
   - Weise deinem FVTLED-Gerät (MAC: `24:94:94:11:8E:1B`) eine feste IP-Adresse zu
   - Empfohlen: `192.168.178.236` oder eine andere freie IP in deinem Netzwerk

2. **Integration hinzufügen**
   - Gehe zu **Einstellungen** → **Geräte & Dienste**
   - Klicke auf **+ Integration hinzufügen**
   - Suche nach "FVTLED ARZ-2100"
   - Gib die IP-Adresse deines Geräts ein (z.B. `192.168.178.236`)
   - Gib einen Namen ein (z.B. "Wohnzimmer LED-Streifen")
   - Klicke auf **Absenden**

#### Schritt 3: Testen

1. Gehe zu **Übersicht**
2. Du solltest jetzt eine neue Licht-Entity sehen
3. Teste das Ein-/Ausschalten und die Farbänderung

### Fehlerbehebung

**Problem: Gerät wird nicht gefunden**
- Überprüfe, ob Port 5577 offen ist: `nmap -p 5577 <deine-ip>`
- Stelle sicher, dass das Gerät mit dem WLAN verbunden ist
- Überprüfe, ob die IP-Adresse korrekt ist

**Problem: Farben sind falsch**
- Das Gerät verwendet RGBW-Modus
- Verwende den RGBW-Farbwähler in Home Assistant
- Beispiel: Reines Rot = `[255, 0, 0, 0]`

---

## English

### Integrating FVTLED ARZ-2100 into Home Assistant

This guide will help you integrate your FVTLED ARZ-2100 RGB Controller into Home Assistant.

#### Step 1: Installation

1. **Copy Files**
   - Download this repository
   - Copy the `custom_components/fvtled_arz2100` folder to your Home Assistant `config/custom_components/` directory

2. **Restart Home Assistant**
   - Go to **Settings** → **System** → **Restart**

#### Step 2: Configure Device

1. **Set Static IP Address**
   - Open your router settings
   - Look for DHCP reservation
   - Assign a fixed IP address to your FVTLED device (MAC: `24:94:94:11:8E:1B`)
   - Recommended: `192.168.178.236` or another free IP in your network

2. **Add Integration**
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for "FVTLED ARZ-2100"
   - Enter your device's IP address (e.g., `192.168.178.236`)
   - Enter a name (e.g., "Living Room LED Strip")
   - Click **Submit**

#### Step 3: Test

1. Go to **Overview**
2. You should now see a new light entity
3. Test turning it on/off and changing colors

### Troubleshooting

**Problem: Device not found**
- Check if port 5577 is open: `nmap -p 5577 <your-ip>`
- Make sure the device is connected to WiFi
- Verify the IP address is correct

**Problem: Colors are wrong**
- The device uses RGBW mode
- Use the RGBW color picker in Home Assistant
- Example: Pure red = `[255, 0, 0, 0]`

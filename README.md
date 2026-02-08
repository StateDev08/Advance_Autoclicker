# Advanced Gaming v3.0 - Ultimate Automation Suite

🔥 **DIE PROFESSIONELLSTE MAKRO-AUTOMATISIERUNG FÜR WINDOWS** 🔥

Von einfachen Klicks zu hochkomplexen, zeitgesteuerten, bildbasierten Multi-Monitor-Workflows mit vollständiger Statistik-Analyse!

---

## 🎯 HIGHLIGHTS v3.0

### ⭐ REVOLUTIONÄRE FEATURES

#### ⏰ **MAKRO-SCHEDULER** - Zeitgesteuerte Automatisierung
- ✅ 5 Schedule-Typen: EINMALIG, TÄGLICH, WÖCHENTLICH, INTERVALL, COUNTDOWN
- ✅ Live-Countdown bis zur nächsten Ausführung
- ✅ Background-Worker für automatische Ausführung
- ✅ Perfekt für: Daily Logins, Wöchentliche Reports, Auto-Backups

#### 📊 **STATISTIKEN & ANALYTICS** - Performance-Tracking
- ✅ Automatisches Tracking jeder Makro-Ausführung
- ✅ Erfolgsrate, Durchschnittsdauer, Min/Max Performance
- ✅ Execution-Historie (letzte 1000 Runs)
- ✅ CSV-Export für Excel-Analyse
- ✅ Live-Updates alle 5 Sekunden

#### 💾 **IMPORT/EXPORT** - Makro-Bibliothek
- ✅ JSON-Export: Einzelne Makros oder komplette Profile
- ✅ CSV-Export: Actions als Tabelle
- ✅ Template-Sammlung erstellen
- ✅ Makros mit Freunden teilen

#### 🎨 **PIXEL-FARB-ERKENNUNG** - Color-Based Automation
- ✅ Finde Pixel nach RGB-Farbe
- ✅ Warte bis Pixel Farbe ändert
- ✅ Klicke auf erste gefundene Farbe
- ✅ Toleranz-System für Helligkeit
- ✅ Perfekt für: Health-Bars, Status-LEDs, Buttons

#### 🖥️ **MULTI-MONITOR-SUPPORT** - Für Streamer & Power-User
- ✅ Automatische Monitor-Erkennung
- ✅ Koordinaten-Konvertierung (absolut ↔ relativ)
- ✅ Actions mit Monitor-ID
- ✅ Perfekt für: Multi-Screen-Setups, Streaming, Trading

#### 🔔 **SYSTEM-TRAY-INTEGRATION** - Always Available
- ✅ Minimiere zur Taskleiste
- ✅ Schnellstart-Menü (bis zu 10 Makros)
- ✅ Benachrichtigungen bei Makro-Start/Ende
- ✅ Läuft im Hintergrund

---

## 🖼️ BILD-ERKENNUNG (v2.0+)

### OpenCV Template Matching
- ✅ **Click on Image**: Finde & klicke auf Screenshot
- ✅ **Wait for Image**: Warte bis Bild erscheint
- ✅ Template-Caching für Performance
- ✅ Konfidenz-basierte Suche (0.0 - 1.0)
- ✅ Multi-Match-Unterstützung
- ✅ Template-Manager GUI

**Use-Cases:**
- Button klicken ohne Koordinaten
- UI-Automation mit dynamischen Layouts
- Game-Bots mit bildbasierter Logik

---

## 🔢 VARIABLEN & BEDINGUNGEN (v2.0+)

### Safe Expression Engine
- ✅ **Variablen**: Local & Global Scope
- ✅ **Arithmetik**: `+`, `-`, `*`, `/`, `%`, `**`
- ✅ **Vergleiche**: `==`, `!=`, `>`, `<`, `>=`, `<=`
- ✅ **Logik**: `and`, `or`, `not`
- ✅ **Funktionen**: `random()`, `random_int(min, max)`
- ✅ **If/Else**: Bedingte Action-Ausführung

**Beispiele:**
```python
# Zähler
{counter} + 1

# Bedingung
{health} < 50

# Zufall
random_int(1, 5)

# Komplex
({x} > 100) and ({y} < 200)
```

---

## 📋 PROFESSIONELLES LOGGING (v2.0+)

### Multi-Logger-System
- ✅ **4 Logger**: Main, Macro, Error, Performance
- ✅ **Log-Rotation**: 10MB Files, 5 Backups
- ✅ **Live Log-Viewer**: GUI-Tab mit Filter
- ✅ **Farbcodierte Ausgabe**: Debug/Info/Warning/Error
- ✅ **Export-Funktion**: Log als Textdatei

**Logs:**
- `logs/main.log` - Hauptlog
- `logs/macro.log` - Makro-Ausführung
- `logs/error.log` - Nur Fehler
- `logs/performance.log` - Timing-Daten

---

## ✨ CORE FEATURES

### 🎬 Makro-Aufnahme
- ✅ Echtzeit-Aufnahme: Maus & Tastatur
- ✅ Aktions-Liste während Aufnahme
- ✅ Start/Stop mit Hotkeys (F9/F10)
- ✅ Automatisches Speichern

### 🛠️ Erweiterter Action-Editor
- ✅ **Visueller Editor**: Drag & Drop
- ✅ **11+ Action-Typen**:
  - Click, Double Click, Mouse Move
  - Key Press, Type Text, Delay
  - Click on Image, Wait for Image
  - Set Variable, If Condition
  - Wait for Pixel Color, Click at Color
- ✅ **Action-Dialog**: Detaillierte Parameter
- ✅ **Preview**: Visualisierung im Editor

### 📁 Profile-Verwaltung
- ✅ Mehrere Profile
- ✅ Schnelles Wechseln
- ✅ Profile-spezifische Makros
- ✅ Hotkey pro Profil
- ✅ SQLite-Datenbank

### 🎯 Window Detection
- ✅ Makros nur in bestimmten Fenstern
- ✅ Window-Title-Matching
- ✅ Auto-Detection

### ⌨️ Globale Hotkeys
- ✅ Makros mit Tastenkombination starten
- ✅ Frei konfigurierbar
- ✅ Funktioniert in allen Programmen

### 🔁 Schleifen & Geschwindigkeit
- ✅ Repeat: 1x - ∞
- ✅ Repeat Delay: 0s - 60s
- ✅ Geschwindigkeitsregelung: 0.1x - 10x

### ⚙️ Einstellungen
- ✅ Vollständig anpassbar
- ✅ Auto-Save
- ✅ Notifications
- ✅ Gaming Overlay (Countdown, aktives Fenster, Minimal-Ansicht)
- ✅ Anti-Erkennung (Klick-Offset, Zufalls-Delays)
- ✅ Spiel-Vorlagen, Makro-Kette, Toggle-Makro
- ✅ Minimize to Tray

---

## 📦 ALLE ACTION-TYPEN

| Action | Version | Beschreibung |
|--------|---------|--------------|
| **click** | v1.0 | Mausklick an Position |
| **double_click** | v1.0 | Doppelklick |
| **mouse_move** | v1.0 | Maus bewegen |
| **key_press** | v1.0 | Taste drücken |
| **delay** | v1.0 | Warten |
| **type_text** | v1.0 | Text eingeben |
| **click_on_image** | v2.0 | Bild finden & klicken |
| **wait_for_image** | v2.0 | Auf Bild warten |
| **set_variable** | v2.0 | Variable setzen |
| **if_condition** | v2.0 | Bedingte Ausführung |
| **wait_for_pixel_color** | v3.0 | Auf Pixelfarbe warten |
| **click_at_color** | v3.0 | Auf Farbe klicken |
| **random_delay** | v3.0 | Zufallsverzögerung (min/max Sek.) |
| **reaction_delay** | v3.0 | Menschliche Reaktionszeit (ms) |
| **wait_for_health_color** | v3.0 | Warten auf eine von mehreren Farben |
| **click_at_health_color** | v3.0 | Klick auf erste Farbe aus Liste |
| **cooldown_wait** | v3.0 | Zufällige Cooldown-Wartezeit |
| **human_mouse_move** | v3.0 | Menschliche Mausbewegung (Schritte + Jitter) |

---

## 📊 TABS ÜBERSICHT

1. **Makros** - Makro-Verwaltung & Ausführung
2. **Recorder** - Makro-Aufnahme
3. **Profile** - Profile-Verwaltung
4. **Templates** - Screenshot-Verwaltung *(v2.0)*
5. **Log Viewer** - Live-Logs *(v2.0)*
6. **Hotkeys** - Hotkey-Konfiguration
7. **Einstellungen** - Programmeinstellungen
8. **Overlay** - Gaming-Overlay-Einstellungen
9. **Scheduler** - Zeitgesteuerte Ausführung *(v3.0)*
10. **Statistiken** - Performance-Analytics *(v3.0)*

---

## 📋 VORAUSSETZUNGEN

- **Windows 10/11**
- **Python 3.8+**
- **Administrator-Rechte** (für Hotkeys)

### Dependencies
```
PyQt6 >= 6.6.0
opencv-python >= 4.8.0
numpy >= 1.24.0
Pillow >= 10.0.0
pywin32 >= 306
```

---

## 🔧 INSTALLATION

### ⚡ Quick Start (5 Minuten)

```powershell
# 1. Dependencies installieren
pip install -r requirements.txt

# 2. Programm starten
python main.py
```

✅ **Fertig!** Das war's schon.

---

### 🏗️ Build als .exe (Optional)

```bash
# Installation
install.bat

# Build
build.bat

# .exe starten
dist\AdvancedGaming.exe
```

**Vorteile:**
- Keine Python-Installation nötig
- Portabel (kopierbar)
- Schnellerer Start

---

## 🎮 ANWENDUNGSFÄLLE

### Gaming
- ✅ **Daily Login**: Scheduler um 08:00
- ✅ **Auto-Farming**: Bild-Erkennung + Loop
- ✅ **Color-Check**: Health-Bar Monitoring
- ✅ **Multi-Monitor**: Game + Chat-Automation

### Business/Office
- ✅ **Wöchentliche Reports**: Freitag 16:00
- ✅ **Auto-Backups**: Interval alle 30 Min
- ✅ **UI-Automation**: Formular-Ausfüllung
- ✅ **Statistik-Tracking**: Performance-Analyse

### Development
- ✅ **Nightly Tests**: Daily um 02:00
- ✅ **Build-Automation**: Scheduler + Scripts
- ✅ **Debug-Logging**: Professionelle Logs
- ✅ **Multi-Monitor**: Code + Docs-Setup

---

## 📚 DOKUMENTATION

| Datei | Inhalt |
|-------|--------|
| **[QUICK_START.md](QUICK_START.md)** | 5-Min Setup & Tutorials |
| **[CHANGELOG.md](CHANGELOG.md)** | Version History (v3.0) |
| **[API_REFERENCE.md](API_REFERENCE.md)** | Alle Action-Typen |
| **[UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)** | Installation & Beispiele |
| **[BUILD.md](BUILD.md)** | Build-Anleitung |

---

## 🚀 ERSTE SCHRITTE

### 1. Erstes Makro (2 Minuten)
```
1. Tab: Profile → "Neues Profil" (F1)
2. Tab: Recorder → "Aufnahme starten" (F9)
3. Maus bewegen & klicken
4. "Aufnahme stoppen" (F10) → Speichern
5. F1 drücken → Makro läuft!
```

### 2. Bild-Erkennung (5 Minuten)
```
1. Screenshot erstellen (Windows + Shift + S)
2. Als PNG in data/templates/ speichern
3. Tab: Makros → Action Editor
4. Action: "Click on Image" → Template wählen
5. Ausführen → Klick auf Bild!
```

### 3. Scheduler (3 Minuten)
```
1. Tab: Scheduler → "Schedule erstellen"
2. Makro wählen
3. Type: "Daily", Time: 08:00
4. Speichern
5. Jeden Tag um 08:00 → Auto-Ausführung!
```

---

## 💡 TIPPS & TRICKS

### 🎯 Accuracy
- **Image Recognition**: Confidence 0.8-0.9 optimal
- **Pixel Detection**: Tolerance 10-30 je nach Helligkeit

### ⚡ Performance
- **Delays**: Nur wo nötig, `wait_for_image` statt feste Delays
- **Loops**: Repeat Delay 0.1-0.5s ausreichend

### 🔒 Sicherheit
- **Passwörter**: Variablen nutzen, nicht im Export
- **Anti-Bot**: Zufällige Delays mit `random_int(1, 3)`

---

## 🐛 TROUBLESHOOTING

**Image nicht gefunden?**
```
→ Confidence verringern (0.7)
→ Screenshot neu erstellen
→ Template Manager → Preview
```

**Makro zu schnell?**
```
→ Delays zwischen Actions
→ wait_for_image statt sofort klicken
```

**Hotkey funktioniert nicht?**
```
→ Als Admin starten
→ Anderen Hotkey wählen
→ Tab: Hotkeys → Test
```

---

## 📈 STATISTIKEN

### v3.0 Zahlen
- **+6 Major Features**
- **+8 neue Core-Module**
- **+2 neue GUI-Tabs**
- **+1960 Zeilen Code**
- **10 Tabs insgesamt**

### Kumulativ (v1.0 → v3.0)
- **+15 neue Dateien**
- **+3810 Zeilen Code**
- **+14 neue Action-Typen**
- **400%+ Funktionalität**
- **100% abwärtskompatibel**

---

## 🎉 FEATURES IM DETAIL

<details>
<summary><b>🖼️ Bild-Erkennung (v2.0)</b></summary>

- Template Matching mit OpenCV
- Konfidenz-basierte Suche
- Template-Caching
- Multi-Match-Unterstützung
- Template-Manager GUI
- Actions: click_on_image, wait_for_image
</details>

<details>
<summary><b>🔢 Variablen (v2.0)</b></summary>

- Local & Global Scope
- Safe Expression Engine (kein eval)
- Arithmetik, Vergleiche, Logik
- Built-in Funktionen
- If/Else Bedingungen
</details>

<details>
<summary><b>📋 Logging (v2.0)</b></summary>

- 4 Logger (Main, Macro, Error, Perf)
- Log-Rotation (10MB, 5 Backups)
- Live Log-Viewer Tab
- Farbcodierte Ausgabe
- Export-Funktion
</details>

<details>
<summary><b>⏰ Scheduler (v3.0)</b></summary>

- 5 Schedule-Typen
- Live-Countdown
- Background-Worker
- Scheduler-Tab GUI
- Run-Counter
</details>

<details>
<summary><b>📊 Statistiken (v3.0)</b></summary>

- Auto-Tracking
- Erfolgsrate, Dauer, Count
- Execution-Historie
- CSV-Export
- Live-Updates
</details>

<details>
<summary><b>💾 Import/Export (v3.0)</b></summary>

- JSON-Export (Makro/Profil)
- CSV-Export (Actions)
- Schema-Versionierung
- Template-Bibliothek
</details>

<details>
<summary><b>🎨 Pixel-Farben (v3.0)</b></summary>

- RGB-Farb-Suche
- Color-Distance-Algorithmus
- Toleranz-System
- Region-Support
- Actions: wait_for_pixel_color, click_at_color
</details>

<details>
<summary><b>🖥️ Multi-Monitor (v3.0)</b></summary>

- Auto-Detection
- Koordinaten-Konvertierung
- Monitor-spezifische Actions
- Virtual-Screen-Bounds
- Win32-API-Integration
</details>

<details>
<summary><b>🔔 System-Tray (v3.0)</b></summary>

- Tray-Icon
- Kontext-Menü
- Schnellstart (10 Makros)
- Benachrichtigungen
- Minimize-to-Tray
</details>

---

## 🌟 WARUM ADVANCED AUTO CLICKER?

✅ **Professionell**: 3810+ Zeilen sauberer Code  
✅ **Mächtig**: 14 Action-Typen, unbegrenzte Möglichkeiten  
✅ **Flexibel**: Gaming, Office, Development  
✅ **Intelligent**: Bild-Erkennung, Variablen, Bedingungen  
✅ **Automatisch**: Scheduler für zeitgesteuerte Runs  
✅ **Überwacht**: Statistiken & Performance-Tracking  
✅ **Open Source**: Vollständiger Quellcode verfügbar  
✅ **Kostenlos**: Keine Limits, keine Werbung  

---

## 📞 SUPPORT

- **GitHub Issues**: Bug-Reports & Feature-Requests
- **Logs**: `logs/` Ordner
- **Docs**: [QUICK_START.md](QUICK_START.md)

---

## 📜 LIZENZ

MIT License - Frei nutzbar für private & kommerzielle Zwecke.

---

## 🎯 NEXT STEPS

1. ✅ `pip install -r requirements.txt`
2. ✅ `python main.py`
3. ✅ [QUICK_START.md](QUICK_START.md) lesen
4. ✅ Erstes Makro erstellen
5. ✅ Features erkunden!

**Happy Automating!** 🚀

---

**Version 3.0.0** | Made with ❤️ | Windows 10/11
   ```bash
   git clone https://github.com/yourusername/Advanced_Gaming.git
   cd Advanced_Gaming
   ```

2. **Installation ausführen**
   ```bash
   install.bat
   ```

3. **Anwendung starten**
   ```bash
   start.bat
   ```

## 📖 Verwendung

### Profile erstellen
1. Öffnen Sie den "Profile"-Tab
2. Klicken Sie auf "➕ Neu"
3. Geben Sie einen Namen und eine Beschreibung ein
4. Klicken Sie auf "OK"

### Makro aufzeichnen
1. Wählen Sie ein Profil aus
2. Wechseln Sie zum "Aufnahme"-Tab
3. Klicken Sie auf "🎙️ Aufnahme starten"
4. Führen Sie die gewünschten Aktionen aus
5. Klicken Sie auf "⏹️ Aufnahme stoppen"
6. Geben Sie einen Namen ein und speichern Sie das Makro

### Makro abspielen
1. Wählen Sie ein Profil aus
2. Wechseln Sie zum "Makros"-Tab
3. Wählen Sie ein Makro aus
4. Klicken Sie auf "▶️ Abspielen"

### Makro bearbeiten
1. Wählen Sie ein Makro aus
2. Klicken Sie auf "✏️ Bearbeiten"
3. Passen Sie die Einstellungen an:
   - Name und Beschreibung
   - Hotkey für schnellen Zugriff
   - Wiederholungen (Anzahl oder unendlich)
   - Verzögerung zwischen Wiederholungen
   - Fenster-Filter für selektive Ausführung

### Window-Detection verwenden
1. Bearbeiten Sie ein Makro
2. Geben Sie im Feld "Fenster-Filter" einen Fensternamen, Klassennamen oder Prozessnamen ein
   - Beispiel: "Notepad" - Makro wird nur in Notepad ausgeführt
   - Beispiel: "chrome.exe" - Makro wird nur in Chrome ausgeführt
3. Das Makro wird nur ausgeführt, wenn das entsprechende Fenster aktiv ist

### Globale Hotkeys einrichten
1. Bearbeiten Sie ein Makro
2. Geben Sie im Feld "Hotkey" eine Tastenkombination ein
   - **Neu**: Klicken Sie auf den "🎙️ Aufnahme"-Button und drücken Sie einfach die gewünschte Tastenkombination!
   - Oder tippen Sie manuell: "ctrl+shift+a", "alt+f1"
3. Das Makro kann jetzt jederzeit mit dieser Tastenkombination gestartet werden

**Tipp**: In den Einstellungen können Sie auch globale Hotkeys für Aufnahme-Start/Stop und Wiedergabe-Stop per Aufnahme festlegen!

### Für Gamer (Steam, GeForce Now, Anti-Erkennung)
- **Fenster-Filter:** Vordefinierte Presets für Steam, GeForce Now, Valorant, Minecraft, Roblox, GTA V, CS2, Elden Ring usw. – im Makro-Dialog unter „Vordefiniert“ wählen.
- **Neue Aktionen:** `random_delay`, `reaction_delay`, `wait_for_health_color`, `click_at_health_color`, `cooldown_wait`, `human_mouse_move` (siehe Action-Tabelle oben).
- **Anti-Erkennung:** Einstellungen → „Klick-Zufalls-Offset“ und „Zufalls-Delay vor jeder Aktion“.
- **Spiel-Vorlagen:** Profil-Tab → Spiel-Vorlagen erstellen (Profil + Fenster-Filter), „Starten“ lädt das Setup.
- **Makro-Kette & Toggle:** Einstellungen → Makro-Kette (IDs kommagetrennt) + Kette-Hotkey; Toggle-Makro (ID) + Toggle-Hotkey (gleicher Hotkey startet/stoppt).
- **Hotkey-Übersicht:** Toolbar „Hotkeys“ zeigt alle Hotkeys inkl. Gaming-Maus (Seitentasten). Siehe auch **QUICK_START.md** → „Für Gamer“.

## 🏗️ Projektstruktur

```
Advanced_Gaming/
├── main.py                 # Haupteinstiegspunkt
├── requirements.txt        # Python-Abhängigkeiten
├── README.md              # Diese Datei
├── database/              # Datenbank-Module
│   ├── __init__.py
│   └── db_manager.py      # SQLite-Verwaltung
├── core/                  # Kernfunktionalität
│   ├── __init__.py
│   ├── recorder.py        # Makro-Aufnahme
│   ├── player.py          # Makro-Wiedergabe
│   ├── hotkey_manager.py  # Globale Hotkeys
│   └── window_detector.py # Window-Detection
├── gui/                   # Benutzeroberfläche
│   ├── __init__.py
│   ├── main_window.py     # Hauptfenster
│   ├── profile_tab.py     # Profile-Verwaltung
│   ├── macro_tab.py       # Makro-Verwaltung
│   ├── recorder_tab.py    # Aufnahme-Interface
│   └── settings_tab.py    # Einstellungen
├── data/                  # Datenbank-Dateien (wird automatisch erstellt)
└── backups/              # Backup-Dateien (wird automatisch erstellt)
```

## 🛠️ Technologie-Stack

- **GUI**: PyQt6 - Moderne, plattformübergreifende GUI
- **Input-Handling**: pynput - Maus- und Tastatur-Aufnahme/-Steuerung
- **Window-Detection**: pywin32 - Windows-API-Zugriff
- **Datenbank**: SQLite - Leichtgewichtige, eingebettete Datenbank

## ⚠️ Wichtige Hinweise

### Sicherheit
- Verwenden Sie die Anwendung verantwortungsvoll
- Makros können potenziell unerwünschte Aktionen ausführen
- Testen Sie Makros zuerst in einer sicheren Umgebung

### Performance
- Bei sehr langen Makros kann die Aufnahme große Dateien erzeugen
- Die Wiedergabe-Geschwindigkeit hängt von der System-Performance ab
- Window-Detection verursacht minimal zusätzliche CPU-Last

### Kompatibilität
- Die Anwendung ist für Windows optimiert
- Globale Hotkeys funktionieren systemweit
- Administratorrechte können für einige Funktionen erforderlich sein

## 🐛 Fehlerbehebung

### Anwendung startet nicht
- Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
- Prüfen Sie, ob Python 3.8+ installiert ist
- Aktivieren Sie die virtuelle Umgebung

### Hotkeys funktionieren nicht
- Starten Sie die Anwendung als Administrator
- Prüfen Sie, ob die Hotkeys nicht bereits von anderen Programmen verwendet werden
- Aktivieren Sie "Globale Hotkeys" in den Einstellungen

### Makros werden nicht korrekt ausgeführt
- Prüfen Sie den Fenster-Filter
- Reduzieren Sie die Wiedergabe-Geschwindigkeit
- Überprüfen Sie die Verzögerungen zwischen Aktionen

### Window-Detection funktioniert nicht
- Starten Sie die Anwendung als Administrator
- Prüfen Sie den Fenster-Filter auf Tippfehler
- Verwenden Sie die aktuelle Fensterinformation in der Statusleiste

## 📝 Lizenz

Dieses Projekt ist für den persönlichen Gebrauch gedacht. 
© 2026 Advanced Gaming

## 🤝 Beiträge

Beiträge, Issues und Feature-Anfragen sind willkommen!

## 📧 Kontakt

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im Repository.

---

**Viel Spaß mit Advanced Gaming!** 🎉

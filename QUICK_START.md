# 🚀 Quick Start Guide - Advanced Gaming v3.0

## ⏱️ 5-Minuten-Setup

### Schritt 1: Installation (1 Min)

```powershell
# In Projektordner navigieren
cd d:\Projekte\Advanced_Gaming

# Dependencies installieren
pip install -r requirements.txt

# Programm starten
python main.py
```

**Dependencies:**
- PyQt6 ≥ 6.6.0
- opencv-python ≥ 4.8.0
- numpy ≥ 1.24.0
- Pillow ≥ 10.0.0
- pywin32 ≥ 306

---

### Schritt 2: Erstes Makro (2 Min)

1. **Profil erstellen:**
   - Tab: "Profile"
   - Button: "Neues Profil"
   - Name: "Mein erstes Profil"
   - Hotkey: F1

2. **Makro aufnehmen:**
   - Tab: "Recorder"
   - Button: "Aufnahme starten" (F9)
   - Maus bewegen & klicken
   - Button: "Aufnahme stoppen" (F10)
   - Name: "Test Makro"
   - Speichern

3. **Makro abspielen:**
   - Tab: "Makros"
   - Makro auswählen
   - Button: "Abspielen"
   - ODER: Hotkey drücken (F1)

✅ **Fertig!** Dein erstes Makro funktioniert.

---

### Schritt 3: Features erkunden (2 Min)

#### 🖼️ Bild-Erkennung testen
1. Tab: "Templates"
2. Screenshot erstellen (Screenshot-Tool)
3. Als PNG speichern in `data/templates/`
4. Tab: "Makros" → Action Editor
5. Action: "Click on Image"
6. Template auswählen

#### 📊 Statistiken ansehen
1. Tab: "Statistiken"
2. Makro ausführen (mehrmals)
3. Live-Updates beobachten
4. Export als CSV

#### ⏰ Scheduler einrichten
1. Tab: "Scheduler"
2. Button: "Schedule erstellen"
3. Makro wählen
4. Type: "Daily"
5. Zeit: 08:00
6. Speichern

**Ergebnis:** Makro läuft jeden Tag automatisch um 08:00!

---

## 🎮 Für Gamer – Wichtige Voraussetzungen

Damit Makros und das Overlay in Spielen zuverlässig funktionieren, beachten Sie bitte folgende Punkte:

1.  **Administratorrechte:** Starten Sie `Advanced Gaming` immer als **Administrator** (Rechtsklick auf die EXE oder `main.py` -> "Als Administrator ausführen"). Ohne diese Rechte können Makros oft keine Eingaben in Spielefenster senden.
2.  **Borderless Windowed Mode:** Stellen Sie Ihr Spiel auf **"Fenster-Modus (Rahmenlos)"** (Borderless Windowed) ein. In "Echtem Vollbild" (Exclusive Fullscreen) kann Windows das Overlay oft nicht über das Spiel zeichnen.
3.  **Fenster-Filter:** Nutzen Sie Fenster-Filter, damit Makros nur im Spiel aktiv sind.
4.  **Anti-Cheat:** Bei aggressiven Anti-Cheats nutzen Sie die **Anti-Erkennung**-Features (Zufalls-Delays, Human Mouse Move) in den Einstellungen.

---

## 🎮 Features für Gamer – Overlay, Fenster-Filter, Steam/GeForce Now, Anti-Erkennung

- **Overlay:** Zeigt „Bereit“ / „Läuft“ und Fortschritt; Kompakt-Modus (▸), Minimal (M), Pin, Click-through. Optional: Countdown (z. B. „Nächster Skill in 12s“), Anzeige des aktiven Fensters/Spiels. Hotkey in Einstellungen.
- **Fenster-Filter:** Beim Bearbeiten eines Makros „Vordefiniert“ nutzen: Kategorien **Steam / GeForce Now** und **Spiele** (z. B. Steam, GeForce Now, Valorant, Minecraft, Roblox, GTA V, CS2, Elden Ring, Fortnite, LoL) oder „Aktuelles Fenster erfassen“. Makro läuft nur, wenn das passende Fenster aktiv ist. Ideal für Steam Games und GeForce Now.
- **Spiel-Modus:** Einstellungen → „Spiel-Modus“ aktivieren. Reduziert Overlay-Updates (2–5 Hz), weniger CPU-Last.
- **Neue Aktionen (Action Editor):**  
  - **random_delay** / **reaction_delay** – Zufallsverzögerung (Anti-Pattern).  
  - **wait_for_health_color** / **click_at_health_color** – Warten auf bzw. Klick auf eine von mehreren Farben (z. B. Lebensbalken, Potion-Button).  
  - **cooldown_wait** – Zufällige Wartezeit für Skill-Cooldowns.  
  - **human_mouse_move** – Mausbewegung in Schritten mit Jitter (menschlicher).
- **Anti-Erkennung (Einstellungen):** „Klick-Zufalls-Offset“ und „Zufalls-Delay vor jeder Aktion“ für weniger starre Muster.
- **Spiel-Vorlagen (Profil-Tab):** „Spiel-Vorlagen“ – Vorlage erstellen (Name, Profil, Fenster-Filter), „Starten“ lädt das Profil und zeigt den Fenster-Filter für Makros.
- **Makro-Kette:** Einstellungen → „Makro-Kette (IDs)“ (kommagetrennt, z. B. 1,2,3) und „Kette-Hotkey“. Ein Tastendruck startet die Makros nacheinander.
- **Toggle-Makro:** „Toggle-Makro (ID)“ + „Toggle-Hotkey“ – gleicher Hotkey startet das Makro oder stoppt die Wiedergabe.
- **Hotkey-Übersicht:** Toolbar → „Hotkeys“ zeigt alle globalen und Makro-Hotkeys inkl. Gaming-Maus (Seitentasten) und markiert Doppelbelegungen.
- **Beispiele:** Siehe Tutorial „Gaming: Auto-Farming“ und „Color-Based: Health Monitor“ unten.

---

## 🎯 USE-CASE TUTORIALS

### 1. Gaming: Auto-Farming

**Ziel:** Bot für wiederkehrende Game-Tasks

**Schritte:**
1. **Screenshots erstellen:**
   - Screenshot von "Collect"-Button → `collect_button.png`
   - Screenshot von "Ready"-Icon → `ready_icon.png`
   - In `data/templates/` speichern

2. **Makro erstellen:**
   ```
   Tab: Makros → Action Editor
   
   Action 1: wait_for_image
     - Template: ready_icon.png
     - Timeout: 30
   
   Action 2: click_on_image
     - Template: collect_button.png
     - Confidence: 0.85
   
   Action 3: delay
     - Duration: 2
   
   Action 4: set_variable
     - Name: farm_count
     - Value: {farm_count} + 1
   
   Action 5: if_condition
     - Condition: {farm_count} > 10
     - Then: Notification ("10 Mal gefarmt!")
   ```

3. **Loop aktivieren:**
   - Repeat: 999x
   - Repeat Delay: 5s

4. **Hotkey setzen:** F5

**Fertig!** F5 drücken → Bot farmt automatisch.

---

### 2. Office: Automatische Reports

**Ziel:** Jeden Freitag um 16:00 Report erstellen

**Schritte:**
1. **Makro aufnehmen:**
   - Excel öffnen
   - Datei öffnen: `C:\Reports\weekly.xlsx`
   - Aktualisieren (F5)
   - Speichern (Ctrl+S)
   - Export als PDF (Ctrl+P)

2. **Scheduler erstellen:**
   ```
   Tab: Scheduler → Neue Schedule
   
   Makro: Weekly Report
   Type: WEEKLY
   Weekday: Friday
   Time: 16:00
   Enabled: ✓
   ```

3. **System Tray aktivieren:**
   ```
   Tab: Einstellungen
   
   ✓ Minimize to Tray
   ✓ Show Notifications
   ```

**Ergebnis:**
- Programm läuft im Hintergrund (Tray)
- Jeden Freitag 16:00 → Report automatisch
- Notification bei Abschluss

---

### 3. Development: Nightly Tests

**Ziel:** Jeden Tag um 02:00 Tests ausführen

**Schritte:**
1. **Test-Makro erstellen:**
   ```
   Action 1: key_press
     - Key: win+r
   
   Action 2: type_text
     - Text: cmd.exe
   
   Action 3: key_press
     - Key: enter
   
   Action 4: delay
     - Duration: 1
   
   Action 5: type_text
     - Text: cd C:\Projects\MyApp
   
   Action 6: key_press
     - Key: enter
   
   Action 7: type_text
     - Text: npm test
   
   Action 8: key_press
     - Key: enter
   ```

2. **Schedule erstellen:**
   ```
   Type: DAILY
   Time: 02:00
   ```

3. **Statistiken tracken:**
   - Tab: Statistiken
   - Export täglich als CSV
   - Analyse in Excel

---

### 4. Multi-Monitor: Streamer-Setup

**Ziel:** Game auf Monitor 1, Chat auf Monitor 2

**Schritte:**
1. **Multi-Monitor prüfen:**
   ```python
   # Console
   from core.multi_monitor import MultiMonitorManager
   mgr = MultiMonitorManager()
   print(mgr.get_monitor_count())  # z.B. 2
   ```

2. **Makro erstellen:**
   ```
   Action 1: click_on_image (Monitor 0)
     - Template: game_icon.png
     - Monitor: 0
   
   Action 2: mouse_move (Monitor 1)
     - X: 500
     - Y: 300
     - Monitor: 1
   
   Action 3: click_on_image (Monitor 1)
     - Template: chat_window.png
   ```

3. **Hotkey setzen:** F6

**Use:** F6 → Game & Chat automatisch öffnen!

---

### 5. Color-Based: Health Monitor

**Ziel:** Alarm wenn Health-Bar rot wird

**Schritte:**
1. **Pixel-Position finden:**
   - Mouse Position Tool: F11
   - Health-Bar Position notieren (z.B. 100, 50)
   - RGB-Wert notieren (Grün: 0, 255, 0)

2. **Makro erstellen:**
   ```
   Action 1: wait_for_pixel_color
     - X: 100
     - Y: 50
     - Color: [255, 0, 0]  # Rot
     - Tolerance: 30
     - Timeout: 60
   
   Action 2: key_press
     - Key: space  # Health Potion
   
   Action 3: delay
     - Duration: 1
   ```

3. **Loop aktivieren:**
   - Repeat: ∞
   - Repeat Delay: 0.5s

**Ergebnis:** Auto-Heal bei Low-Health!

---

## 🔧 ERWEITERTE FEATURES

### Variablen & Bedingungen

**Beispiel: Zähler mit Bedingung**

```
Action 1: set_variable
  - Name: counter
  - Value: 0
  - Scope: local

Action 2: click
  - X: 500
  - Y: 300

Action 3: set_variable
  - Name: counter
  - Value: {counter} + 1

Action 4: if_condition
  - Condition: {counter} >= 5
  - Then Actions:
      - type_text: "5 Mal geklickt!"
      - set_variable: counter = 0
```

**Beispiel: Zufällige Delays (Anti-Bot)**

```
Action 1: set_variable
  - Name: wait_time
  - Value: random_int(1, 5)

Action 2: delay
  - Duration: {wait_time}

Action 3: click
  - X: 500
  - Y: 300
```

---

### Import/Export

**Makro exportieren:**
1. Tab: Makros
2. Rechtsklick auf Makro
3. "Exportieren" → JSON speichern

**Makro importieren:**
1. Tab: Makros
2. Button: "Importieren"
3. JSON-Datei auswählen

**Use-Cases:**
- Makros mit Freunden teilen
- Backup erstellen
- Migration zwischen PCs

---

### Logging & Debugging

**Log-Viewer nutzen:**
1. Tab: "Log Viewer"
2. Filter: Error/Warning/Info
3. Export → Textdatei

**Performance-Logging:**
- Aktivieren: Settings → "Performance Logging"
- Log zeigt: Action-Dauer, Total-Zeit
- Optimization: Langsame Actions finden

---

## 💡 TIPPS & TRICKS

### 🎯 Accuracy verbessern
- **Image Recognition:**
  - Confidence: 0.8-0.9 optimal
  - Screenshot exakt zuschneiden
  - Template-Cache aktivieren

- **Pixel Detection:**
  - Tolerance: 10-30 je nach Helligkeit
  - Region einschränken (Performance)

### ⚡ Performance optimieren
- **Delays minimieren:**
  - Nur wo nötig
  - `wait_for_image` statt feste Delays

- **Loops:**
  - Repeat Delay: 0.1-0.5s ausreichend
  - Keine 0s (CPU-Last)

### 🔒 Sicherheit
- **Passwörter:**
  - Variablen nutzen statt Plaintext
  - Export: Passwörter entfernen

- **Anti-Bot:**
  - Zufällige Delays: `random_int(1, 3)`
  - Zufällige Positionen: `{x} + random_int(-5, 5)`

### 🐛 Troubleshooting

**Problem:** Image nicht gefunden
```
Lösung:
1. Confidence verringern (0.7)
2. Screenshot neu erstellen
3. Template Manager → Preview
```

**Problem:** Makro zu schnell
```
Lösung:
1. Delays zwischen Actions
2. wait_for_image statt click sofort
```

**Problem:** Hotkey funktioniert nicht
```
Lösung:
1. Programm als Admin starten
2. Anderer Hotkey (nicht von Windows genutzt)
3. Tab: Hotkeys → Test
```

---

## 📊 MONITORING

### Statistiken nutzen

**Performance-Analyse:**
1. Tab: Statistiken
2. Sortieren: "Avg Duration"
3. Langsame Makros optimieren

**Fehler-Tracking:**
1. Filter: Success Rate < 80%
2. Logs ansehen
3. Actions debuggen

**Export:**
1. Button: "Export CSV"
2. Excel öffnen
3. Pivot-Tabellen erstellen

---

## 🎓 LERNPFAD

### Anfänger (Woche 1)
- ✅ Recorder nutzen
- ✅ Einfache Makros (Click, Delay)
- ✅ Hotkeys setzen
- ✅ Profiles erstellen

### Fortgeschritten (Woche 2)
- ✅ Bild-Erkennung
- ✅ Variablen nutzen
- ✅ If-Bedingungen
- ✅ Scheduler einrichten

### Experte (Woche 3+)
- ✅ Multi-Monitor-Setups
- ✅ Pixel-Detection
- ✅ Komplexe Workflows
- ✅ Import/Export
- ✅ Statistik-Analyse

---

## 🆘 SUPPORT

**Dokumentation:**
- [CHANGELOG.md](CHANGELOG.md) - Features
- [API_REFERENCE.md](API_REFERENCE.md) - Action-Typen
- [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) - Installation

**Logs:**
- `logs/main.log` - Hauptlog
- `logs/macro.log` - Makro-Ausführung
- `logs/error.log` - Fehler

**Community:**
- GitHub Issues
- Discord Server
- Forum

---

## 🎉 LOS GEHT'S!

**Nächste Schritte:**
1. ✅ `pip install -r requirements.txt`
2. ✅ `python main.py`
3. ✅ Erstes Makro aufnehmen
4. ✅ Feature ausprobieren
5. ✅ Spaß haben! 🚀

**Happy Automating!** 🎯

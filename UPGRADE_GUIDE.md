# 🚀 Advanced Gaming v2.0 - Installation & Upgrade Guide

## ✨ Version 2.0 - MEGA UPDATE (250% Verbesserung!)

### Neue Features in v2.0:
- 🖼️ **Bild-Erkennung** (OpenCV) - Klicke auf UI-Elemente!
- 🔢 **Variablen & Bedingungen** - Intelligente Makros!
- 📋 **Professionelles Logging** - Debugging & Monitoring!
- 🔧 **Erweiterter Action-Editor** - Drag & Drop Interface!
- 📊 **3 neue GUI-Tabs** - Logs, Templates, Action-Editor!

---

## 📦 Installation der neuen Dependencies

### Schritt 1: Python-Umgebung aktivieren
Falls Sie eine virtuelle Umgebung nutzen:
```powershell
# Falls vorhanden, aktivieren:
.\venv\Scripts\Activate.ps1
```

### Schritt 2: Neue Packages installieren
```powershell
pip install -r requirements.txt
```

Oder manuell:
```powershell
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0
pip install pillow>=10.0.0
```

### Schritt 3: Installation verifizieren
```powershell
python -c "import cv2; import numpy; from PIL import Image; print('✅ Alle Packages installiert!')"
```

---

## 🔄 Upgrade von v1.x auf v2.0

### Kompatibilität
✅ **100% abwärtskompatibel** - Ihre bestehenden Makros funktionieren ohne Änderungen!

### Upgrade-Schritte
1. **Backup erstellen** (optional):
   ```powershell
   Copy-Item -Path "data" -Destination "data_backup" -Recurse
   ```

2. **Dependencies installieren** (siehe oben)

3. **Programm starten**:
   ```powershell
   python main.py
   ```

4. **Neue Features testen**:
   - Öffnen Sie den **🖼️ Templates** Tab
   - Erstellen Sie Ihr erstes Screenshot-Template
   - Schauen Sie in den **📋 Logs** Tab für Live-Monitoring

---

## 🎯 Quick Start - Neue Features nutzen

### 1️⃣ Bild-Erkennung einrichten

#### Template erstellen:
1. Gehe zum **🖼️ Templates** Tab
2. Klicke **"📷 Vollbild erfassen"** oder **"🖼️ Bereich erfassen"**
3. Fenster minimiert sich → Warte 0.5s
4. Screenshot wird gemacht
5. Gib einen Namen ein (z.B. "StartButton")
6. Template ist gespeichert!

#### Template testen:
1. Wähle Template in der Liste
2. Klicke **"🔍 Testen"**
3. Programm sucht nach Template auf dem Bildschirm
4. Zeigt Position + Konfidenz an

### 2️⃣ Makro mit Bild-Erkennung erstellen

#### In bestehendem Makro:
1. Wähle Makro im **⚡ Makros** Tab
2. Klicke **"🔧 Aktionen"** (neuer Button!)
3. Klicke **"➕ Aktion hinzufügen"**
4. Wähle Typ: **"click_on_image"**
5. Template: Name deines Templates
6. Konfidenz: 0.8 (80% Übereinstimmung)
7. Button: "left" (oder right/middle)
8. **💾 Speichern**

#### Neue Action-Typen:
- `click_on_image` - Klickt auf gefundenes Bild
- `wait_for_image` - Wartet bis Bild erscheint (max 10s)
- `set_variable` - Setzt eine Variable
- `if_condition` - Bedingte Ausführung
- `wait` - Wartet X Sekunden
- `log_message` - Loggt eine Nachricht

### 3️⃣ Variablen verwenden

#### Variable setzen:
```
Typ: set_variable
Name: counter
Wert: 0
```

#### Variable erhöhen:
```
Typ: set_variable
Name: counter
Wert: {counter} + 1
```

#### Bedingung prüfen:
```
Typ: if_condition
Bedingung: {counter} > 5
→ True: Weitere Aktionen...
→ False: Alternative Aktionen...
```

#### In Koordinaten nutzen:
```
Typ: mouse_move
X: {pos_x}
Y: {pos_y}
```

### 4️⃣ Logs überwachen

1. Gehe zum **📋 Logs** Tab
2. Level auswählen: ALL, DEBUG, INFO, WARNING, ERROR
3. Auto-Scroll aktivieren
4. Siehe Live-Ausgabe während Makro läuft:
   - Grün = INFO
   - Gelb = WARNING
   - Rot = ERROR
5. **💾 Speichern** um Logs zu exportieren

---

## 🔧 Erweiterte Features

### Variablen-System

#### Built-in Variablen (automatisch):
- `loop_count` - Anzahl geplanter Loops
- `current_loop` - Aktueller Loop (1-basiert)
- `action_count` - Anzahl Aktionen im Makro
- `current_action` - Aktuelle Action (1-basiert)
- `image_x`, `image_y` - Position des letzten gefundenen Bildes
- `image_found` - true/false, ob Bild gefunden wurde

#### Ausdrücke:
- Arithmetik: `{a} + {b}`, `{x} * 2`, `{y} / 3`
- Vergleiche: `{health} < 50`, `{mana} >= 100`
- Logik: `{a} > 5 and {b} < 10`, `{flag} or {other}`

#### Funktionen:
- `random()` - Zufall 0.0-1.0
- `random_int(1, 100)` - Ganzzahl 1-100
- `random_float(0.5, 2.5)` - Fließkomma
- `len({text})` - Länge
- `int({value})`, `float({value})`, `str({value})` - Konvertierung

### Bild-Erkennung

#### Parameter:
- **Template**: Name des gespeicherten Screenshots
- **Konfidenz**: 0.0-1.0 (0.8 = 80% Übereinstimmung)
  - 0.9+ = sehr genau (evtl. zu streng)
  - 0.7-0.8 = gut für UI-Elemente
  - <0.7 = zu ungenau, viele False Positives
- **Timeout**: Maximale Wartezeit in Sekunden
- **Offset**: X/Y Versatz vom Bild-Mittelpunkt

#### Tipps:
- ✅ Kleine, eindeutige Bereiche erfassen (Buttons, Icons)
- ✅ Screenshots bei gleicher Auflösung machen
- ✅ Templates regelmäßig testen
- ❌ Keine großen Vollbild-Screenshots (langsam)
- ❌ Keine sich ändernden Elemente (Animationen)

---

## 🐛 Troubleshooting

### Import-Fehler nach Update
**Problem**: `Import "cv2" konnte nicht aufgelöst werden`

**Lösung**:
```powershell
pip install opencv-python numpy pillow --upgrade
```

### Bild wird nicht gefunden
**Problem**: Template wird nicht erkannt

**Lösungen**:
1. Konfidenz reduzieren (0.8 → 0.7)
2. Neues Template mit aktuellem Screenshot erstellen
3. Im Template-Manager mit **🔍 Testen** prüfen
4. Kleineren/präziseren Bereich erfassen

### Logs zeigen Fehler
**Problem**: Rote Fehler im Log-Viewer

**Lösung**:
1. Level auf "DEBUG" setzen für Details
2. Fehler-Nachricht lesen
3. Betroffene Action in **🔧 Aktionen** prüfen
4. Template-Namen, Variable-Namen korrekt?

### Action-Editor öffnet nicht
**Problem**: Button **🔧 Aktionen** reagiert nicht

**Lösung**:
1. Makro in Liste auswählen
2. Makro muss mindestens 1 Action haben
3. Falls leer: Über **✏️ Bearbeiten** Action hinzufügen

---

## 📚 Beispiel-Makros

### Beispiel 1: Automatischer Login
```
1. wait_for_image
   - Template: "LoginButton"
   - Timeout: 10s
   - Konfidenz: 0.8

2. if_condition
   - Bedingung: {image_found} == true
   - True Actions:
     3. click_on_image
        - Template: "LoginButton"
     4. wait (1s)
     5. key_press (Key.tab)
     6. wait (0.5s)
     7. [Passwort eingeben...]

3. log_message
   - Message: "Login-Versuch abgeschlossen"
   - Level: info
```

### Beispiel 2: Item-Farming mit Counter
```
1. set_variable
   - Name: items_collected
   - Wert: 0

2. set_variable
   - Name: max_items
   - Wert: 50

3. [LOOP START]

4. click_on_image
   - Template: "CollectButton"
   - Konfidenz: 0.75

5. if_condition
   - Bedingung: {image_found} == true
   - True Actions:
     6. set_variable
        - Name: items_collected
        - Wert: {items_collected} + 1
     7. log_message
        - Message: "Items: {items_collected}/{max_items}"

8. if_condition
   - Bedingung: {items_collected} >= {max_items}
   - True Actions:
     9. log_message
        - Message: "Ziel erreicht! Stoppe..."
        - Level: warning
```

### Beispiel 3: Zufällige Delays (Anti-Bot)
```
1. click_on_image
   - Template: "QuestButton"

2. wait
   - Dauer: random_float(0.5, 2.0)

3. mouse_move
   - X: random_int(100, 500)
   - Y: random_int(100, 400)

4. wait
   - Dauer: random_float(1.0, 3.0)
```

---

## 🎮 Gaming-Overlay (v1.2 Feature)

Weiterhin verfügbar:
- **Strg+Shift+O** zum Ein-/Ausblenden
- Zeigt laufendes Makro + Timer
- STOP ALL Button für Notfall
- Konfigurierbar in **⚙️ Einstellungen**

---

## 📞 Support & Feedback

### Logs für Bugreports
Falls Sie einen Bug melden:
1. **📋 Logs** Tab öffnen
2. **💾 Speichern** klicken
3. Log-Datei anhängen

### Dateien für Debug
- `data/logs/advanced_gaming.log` - Haupt-Log
- `data/logs/macro.log` - Makro-Ausführungs-Details
- `data/logs/error.log` - Nur Fehler
- `data/advanced_gaming.db` - Datenbank (enthält alle Makros)

---

## 🎉 Viel Erfolg mit v2.0!

Das Programm wurde von einem einfachen Auto-Clicker zu einem **vollwertigen Makro-Automatisierungs-Tool** mit:
- ✅ Computer Vision (Bild-Erkennung)
- ✅ Programmlogik (Variablen, Bedingungen)
- ✅ Professionellem Debugging (Logging, Editor)

**→ 250% mehr Funktionalität als v1.x!**

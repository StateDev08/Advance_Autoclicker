# API-Referenz - Advanced Gaming v3.0

## 📋 Übersicht

Dieses Dokument beschreibt **alle verfügbaren Action-Typen** und deren Parameter für das Makro-System.

---

## 🎯 ACTION-TYPEN

### 1. CLICK - Mausklick

Führt einen Mausklick an einer bestimmten Position aus.

**Parameter:**
- `x` (int): X-Koordinate
- `y` (int): Y-Koordinate
- `button` (str): Maustaste - `'left'`, `'right'`, `'middle'`
- `monitor_id` (int, optional): Monitor-Nummer (Multi-Monitor)

**Beispiel:**
```python
{
    "type": "click",
    "x": 500,
    "y": 300,
    "button": "left",
    "monitor_id": 0  # Hauptmonitor
}
```

**Use-Cases:**
- Button klicken
- Menü öffnen
- Element auswählen

---

### 2. DOUBLE_CLICK - Doppelklick

Führt einen Doppelklick aus.

**Parameter:**
- `x` (int): X-Koordinate
- `y` (int): Y-Koordinate
- `button` (str): Maustaste - `'left'`, `'right'`, `'middle'`

**Beispiel:**
```python
{
    "type": "double_click",
    "x": 400,
    "y": 250,
    "button": "left"
}
```

**Use-Cases:**
- Datei öffnen
- Text markieren

---

### 3. MOUSE_MOVE - Mausbewegung

Bewegt die Maus zu einer Position.

**Parameter:**
- `x` (int): Ziel X-Koordinate
- `y` (int): Ziel Y-Koordinate
- `monitor_id` (int, optional): Monitor-Nummer

**Beispiel:**
```python
{
    "type": "mouse_move",
    "x": 800,
    "y": 600,
    "monitor_id": 1  # Zweiter Monitor
}
```

**Use-Cases:**
- Hover-Effekt triggern
- Position vorbereiten

---

### 4. KEY_PRESS - Tastendruck

Drückt eine Taste oder Tastenkombination.

**Parameter:**
- `key` (str): Tasten-Code oder Kombination
  - Einzeln: `'a'`, `'enter'`, `'esc'`, `'space'`
  - Kombination: `'ctrl+c'`, `'ctrl+shift+s'`, `'alt+f4'`

**Spezial-Tasten:**
- `enter`, `tab`, `esc`, `space`, `backspace`, `delete`
- `left`, `right`, `up`, `down`
- `home`, `end`, `pageup`, `pagedown`
- `f1`-`f12`
- `ctrl`, `shift`, `alt`, `win`

**Beispiel:**
```python
{
    "type": "key_press",
    "key": "ctrl+s"  # Speichern
}
```

**Use-Cases:**
- Shortcuts ausführen
- Text eingeben
- Fenster wechseln

---

### 5. DELAY - Verzögerung

Wartet eine bestimmte Zeit.

**Parameter:**
- `duration` (float): Zeit in Sekunden (0.001 bis 3600)
- `duration` (str): Variable/Expression z.B. `"{wait_time}"`

**Beispiel:**
```python
{
    "type": "delay",
    "duration": 1.5  # 1.5 Sekunden
}
```

**Use-Cases:**
- Warten auf Ladezeiten
- Verzögerung zwischen Actions
- Rate-Limiting

---

### 6. TYPE_TEXT - Text eingeben

Tippt einen Text Zeichen für Zeichen.

**Parameter:**
- `text` (str): Zu schreibender Text
- `interval` (float, optional): Verzögerung zwischen Zeichen (Standard: 0.05s)

**Variablen-Support:**
- `{variable_name}` wird ersetzt

**Beispiel:**
```python
{
    "type": "type_text",
    "text": "Hallo {username}!",
    "interval": 0.1
}
```

**Use-Cases:**
- Formular ausfüllen
- Chat-Nachrichten
- Passwort eingeben

---

### 7. CLICK_ON_IMAGE - Bild-basierter Klick (v2.0+)

Sucht ein Template-Bild auf dem Bildschirm und klickt darauf.

**Parameter:**
- `image_path` (str): Pfad zum Template (relativ zu `data/templates/`)
- `confidence` (float): Mindest-Ähnlichkeit 0.0-1.0 (Standard: 0.8)
- `timeout` (int): Max. Wartezeit in Sekunden (Standard: 10)
- `button` (str): Maustaste - `'left'`, `'right'`, `'middle'`

**Beispiel:**
```python
{
    "type": "click_on_image",
    "image_path": "login_button.png",
    "confidence": 0.85,
    "timeout": 5,
    "button": "left"
}
```

**Use-Cases:**
- Button klicken ohne Koordinaten
- UI-Element finden (dynamische Layouts)
- Game-Automation

**Wichtig:**
- Screenshot muss in `data/templates/` liegen
- Funktioniert mit OpenCV Template Matching
- Klick erfolgt in die Mitte des gefundenen Bildes

---

### 8. WAIT_FOR_IMAGE - Auf Bild warten (v2.0+)

Wartet bis ein Template-Bild erscheint.

**Parameter:**
- `image_path` (str): Pfad zum Template
- `confidence` (float): Mindest-Ähnlichkeit (Standard: 0.8)
- `timeout` (int): Max. Wartezeit in Sekunden (Standard: 30)

**Beispiel:**
```python
{
    "type": "wait_for_image",
    "image_path": "loading_complete.png",
    "confidence": 0.9,
    "timeout": 60
}
```

**Use-Cases:**
- Warten auf Ladebildschirm
- Synchronisation mit UI
- Bedingtes Warten

---

### 9. SET_VARIABLE - Variable setzen (v2.0+)

Setzt eine Variable auf einen Wert.

**Parameter:**
- `name` (str): Variablen-Name
- `value` (any): Wert (int, float, str, bool)
- `value` (str): Expression z.B. `"{counter} + 1"`
- `scope` (str): `'local'` (Makro) oder `'global'` (alle Makros)

**Expressions:**
- Arithmetik: `+`, `-`, `*`, `/`, `%`, `**`
- Vergleiche: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logik: `and`, `or`, `not`
- Funktionen: `random()`, `random_int(min, max)`

**Beispiele:**
```python
# Einfacher Wert
{
    "type": "set_variable",
    "name": "counter",
    "value": 0,
    "scope": "local"
}

# Expression
{
    "type": "set_variable",
    "name": "counter",
    "value": "{counter} + 1",
    "scope": "local"
}

# Random
{
    "type": "set_variable",
    "name": "wait_time",
    "value": "random_int(1, 5)",
    "scope": "local"
}
```

**Use-Cases:**
- Zähler/Schleifen
- Zufallswerte
- State-Management

---

### 10. IF_CONDITION - Bedingte Ausführung (v2.0+)

Führt Actions nur aus wenn Bedingung erfüllt ist.

**Parameter:**
- `condition` (str): Bedingung als Expression
- `then_actions` (list): Actions bei `True`
- `else_actions` (list, optional): Actions bei `False`

**Bedingungen:**
- Vergleiche: `{counter} > 10`
- Logik: `{is_logged_in} and {has_credits}`
- Kombiniert: `({x} > 5) or ({y} < 3)`

**Beispiel:**
```python
{
    "type": "if_condition",
    "condition": "{counter} > 5",
    "then_actions": [
        {
            "type": "type_text",
            "text": "Counter ist groß!"
        }
    ],
    "else_actions": [
        {
            "type": "delay",
            "duration": 1
        }
    ]
}
```

**Use-Cases:**
- Verzweigungen
- Error-Handling
- Adaptive Makros

---

### 11. WAIT_FOR_PIXEL_COLOR - Auf Pixelfarbe warten (v3.0+)

Wartet bis ein Pixel eine bestimmte Farbe hat.

**Parameter:**
- `x` (int): X-Koordinate
- `y` (int): Y-Koordinate
- `color` (list/str): RGB-Tuple `[255, 0, 0]` oder Hex `"#FF0000"`
- `tolerance` (int): Farb-Toleranz 0-255 (Standard: 10)
- `timeout` (int): Max. Wartezeit in Sekunden (Standard: 30)
- `monitor_id` (int, optional): Monitor-Nummer

**Beispiel:**
```python
{
    "type": "wait_for_pixel_color",
    "x": 100,
    "y": 200,
    "color": [0, 255, 0],  # Grün
    "tolerance": 20,
    "timeout": 10
}
```

**Use-Cases:**
- Warten bis Button aktiviert (Color-Change)
- Health-Bar Monitoring
- Status-LED Detection

---

### 12. CLICK_AT_COLOR - Auf Farbe klicken (v3.0+)

Sucht eine Farbe auf dem Bildschirm und klickt darauf.

**Parameter:**
- `color` (list/str): RGB-Tuple oder Hex
- `tolerance` (int): Farb-Toleranz (Standard: 20)
- `region` (tuple, optional): Suchbereich `(x1, y1, x2, y2)`
- `button` (str): Maustaste (Standard: `'left'`)
- `timeout` (int): Max. Wartezeit (Standard: 10)

**Beispiel:**
```python
{
    "type": "click_at_color",
    "color": "#FF0000",  # Rot
    "tolerance": 30,
    "region": [0, 0, 1920, 1080],  # Ganzer Screen
    "button": "left"
}
```

**Use-Cases:**
- Roten Button finden & klicken
- Color-Coded UI-Automation
- Dynamic Element Finding

---

## 🔧 SPEZIELLE FEATURES

### Multi-Monitor-Support (v3.0+)

**Funktionen:**
- Automatische Monitor-Erkennung
- Koordinaten-Konvertierung
- Monitor-spezifische Actions

**Actions mit Monitor-Support:**
- `click` → `monitor_id`
- `mouse_move` → `monitor_id`
- `click_on_image` → Sucht auf allen Monitoren
- `wait_for_pixel_color` → `monitor_id`

**Beispiel:**
```python
# Monitor 1 (Index 0)
{"type": "click", "x": 500, "y": 300, "monitor_id": 0}

# Monitor 2 (Index 1)
{"type": "click", "x": 500, "y": 300, "monitor_id": 1}
```

---

### Variablen-System (v2.0+)

**Variable in Actions verwenden:**

Alle Parameter können Variablen enthalten:
```python
{
    "type": "delay",
    "duration": "{wait_time}"
}

{
    "type": "type_text",
    "text": "Hallo {username}, du hast {score} Punkte!"
}
```

**Scope:**
- **Local**: Nur innerhalb eines Makros
- **Global**: Über alle Makros hinweg

**Built-in Variablen:**
- `{mouse_x}` - Aktuelle Maus X-Position
- `{mouse_y}` - Aktuelle Maus Y-Position

---

### Scheduler-Integration (v3.0+)

Actions können **zeitgesteuert** ausgeführt werden:

**Schedule-Typen:**
1. **ONCE** - Einmalig zu bestimmter Uhrzeit
2. **DAILY** - Täglich zur selben Zeit
3. **WEEKLY** - Wöchentlich an bestimmtem Tag
4. **INTERVAL** - Alle X Minuten
5. **COUNTDOWN** - Nach X Sekunden

**Beispiel:**
```python
# Täglich um 08:00 → Login-Makro
Schedule(
    macro_id=1,
    type=ScheduleType.DAILY,
    time="08:00"
)
```

---

## 📊 ACTION-KOMPATIBILITÄT

| Action | v1.0 | v2.0 | v3.0 | Multi-Monitor | Variablen |
|--------|------|------|------|---------------|-----------|
| click | ✅ | ✅ | ✅ | ✅ | ✅ |
| double_click | ✅ | ✅ | ✅ | ❌ | ✅ |
| mouse_move | ✅ | ✅ | ✅ | ✅ | ✅ |
| key_press | ✅ | ✅ | ✅ | ❌ | ✅ |
| delay | ✅ | ✅ | ✅ | ❌ | ✅ |
| type_text | ✅ | ✅ | ✅ | ❌ | ✅ |
| click_on_image | ❌ | ✅ | ✅ | ✅ | ✅ |
| wait_for_image | ❌ | ✅ | ✅ | ✅ | ✅ |
| set_variable | ❌ | ✅ | ✅ | ❌ | ✅ |
| if_condition | ❌ | ✅ | ✅ | ❌ | ✅ |
| wait_for_pixel_color | ❌ | ❌ | ✅ | ✅ | ✅ |
| click_at_color | ❌ | ❌ | ✅ | ✅ | ✅ |

---

## 🎯 BEISPIEL-MAKROS

### Gaming: Auto-Login

```json
{
    "name": "Daily Login",
    "actions": [
        {
            "type": "click_on_image",
            "image_path": "game_icon.png",
            "confidence": 0.9
        },
        {
            "type": "wait_for_image",
            "image_path": "login_button.png",
            "timeout": 30
        },
        {
            "type": "click_on_image",
            "image_path": "login_button.png"
        },
        {
            "type": "type_text",
            "text": "{username}"
        },
        {
            "type": "key_press",
            "key": "tab"
        },
        {
            "type": "type_text",
            "text": "{password}"
        },
        {
            "type": "key_press",
            "key": "enter"
        }
    ]
}
```

### Office: Wöchentlicher Report

```json
{
    "name": "Friday Report",
    "actions": [
        {
            "type": "key_press",
            "key": "win+r"
        },
        {
            "type": "delay",
            "duration": 0.5
        },
        {
            "type": "type_text",
            "text": "excel.exe"
        },
        {
            "type": "key_press",
            "key": "enter"
        },
        {
            "type": "wait_for_image",
            "image_path": "excel_ready.png",
            "timeout": 10
        },
        {
            "type": "key_press",
            "key": "ctrl+o"
        },
        {
            "type": "type_text",
            "text": "C:\\Reports\\weekly.xlsx"
        },
        {
            "type": "key_press",
            "key": "enter"
        }
    ]
}
```

### Multi-Monitor: Streamer-Setup

```json
{
    "name": "Stream Setup",
    "actions": [
        {
            "type": "click_on_image",
            "image_path": "obs_start.png",
            "monitor_id": 0
        },
        {
            "type": "mouse_move",
            "x": 500,
            "y": 300,
            "monitor_id": 1
        },
        {
            "type": "click_on_image",
            "image_path": "chat_window.png",
            "monitor_id": 1
        }
    ]
}
```

---

## 🔍 ERROR-HANDLING

### Image-Actions
**Fehler:** Template nicht gefunden
```
ImageNotFoundException: Template 'button.png' not found after 10s
```
**Lösung:**
- Confidence verringern
- Timeout erhöhen
- Screenshot überprüfen

### Variable-Actions
**Fehler:** Variable nicht definiert
```
VariableNotDefinedException: Variable 'counter' not found
```
**Lösung:**
- `set_variable` vor Verwendung
- Scope prüfen (local/global)

### Pixel-Color-Actions
**Fehler:** Farbe nicht gefunden
```
ColorNotFoundException: Color (255, 0, 0) not found after 30s
```
**Lösung:**
- Tolerance erhöhen
- Koordinaten prüfen
- Region einschränken

---

## 📚 SIEHE AUCH

- **CHANGELOG.md** - Version History
- **UPGRADE_GUIDE.md** - Installation & Tutorials
- **README.md** - Projekt-Übersicht

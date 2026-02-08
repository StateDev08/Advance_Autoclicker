# Advanced Gaming - Build Anleitung

## 🔨 Erstellen einer ausführbaren .exe-Datei

### Voraussetzungen
- Python 3.8+
- Alle Abhängigkeiten installiert (siehe requirements.txt)

### Schritt-für-Schritt Anleitung

#### 1. Installation durchführen
Falls noch nicht geschehen, führen Sie zuerst die Installation aus:
```bash
install.bat
```

#### 2. Build erstellen
Führen Sie das Build-Script aus:
```bash
build.bat
```

Das Script wird:
- PyInstaller installieren (falls nicht vorhanden)
- Alle alten Build-Dateien aufräumen
- Eine neue .exe-Datei erstellen
- Die Datei im `dist`-Ordner ablegen

#### 3. Fertig!
Die ausführbare Datei befindet sich in:
```
dist\AdvancedGaming.exe
```

### 📦 Verteilung

Die erstellte .exe-Datei ist **standalone** und kann:
- ✅ An jeden beliebigen Ort kopiert werden
- ✅ Ohne Python-Installation ausgeführt werden
- ✅ Auf jedem Windows-System funktionieren
- ✅ Mit anderen geteilt werden

### 💾 Datenbankdateien

**Wichtig:** Die .exe erstellt beim ersten Start automatisch einen `data`-Ordner am gleichen Ort wie die .exe. Dort werden alle Profile und Makros gespeichert.

Wenn Sie die .exe verschieben möchten und Ihre Daten behalten wollen:
1. Kopieren Sie die .exe UND den `data`-Ordner
2. Oder: Exportieren Sie Ihre Daten vorher im Einstellungs-Tab

### 🔧 Build-Optionen anpassen

Sie können die Build-Optionen in `build_exe.py` anpassen:

- **Icon hinzufügen**: Ersetzen Sie `'--icon=NONE'` mit `'--icon=icon.ico'`
- **Konsolenfenster anzeigen**: Entfernen Sie `'--windowed'`
- **Mehrere Dateien statt einer**: Ersetzen Sie `'--onefile'` mit `'--onedir'`

### 📊 Build-Größe

Die .exe-Datei ist ca. 80-120 MB groß, da sie folgendes enthält:
- Python-Runtime
- PyQt6-Bibliotheken
- Alle Dependencies
- Anwendungscode

### ❗ Häufige Probleme

**Antivirus-Warnung:**
- Manche Antivirus-Programme markieren PyInstaller-Builds als verdächtig
- Dies ist ein bekanntes False-Positive-Problem
- Fügen Sie die .exe zur Whitelist hinzu

**Build schlägt fehl:**
- Stellen Sie sicher, dass alle Dependencies installiert sind
- Löschen Sie die `build`- und `dist`-Ordner manuell
- Führen Sie `build.bat` erneut aus

**Admin-Rechte erforderlich:**
- Für globale Hotkeys und Window-Detection
- Führen Sie die .exe als Administrator aus
- Rechtsklick → "Als Administrator ausführen"

### 🚀 Schnellstart für Endbenutzer

Wenn Sie die .exe an andere verteilen:

1. **Download**: `AdvancedGaming.exe` herunterladen
2. **Starten**: Doppelklick auf die .exe
3. **Fertig**: Die Anwendung startet sofort!

Beim ersten Start wird automatisch:
- Der `data`-Ordner erstellt
- Die Datenbank initialisiert
- Die Standardeinstellungen gesetzt

---

**Viel Erfolg beim Builden!** 🎉

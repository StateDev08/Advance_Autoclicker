# Update & Auto-Update einrichten

Dieses Dokument beschreibt, wie du das Update-System von **Advanced Gaming** einrichtest und verwendest.

## 1. Version im Code pflegen

Die Versionsnummer wird zentral in `core/version.py` verwaltet:

- `APP_NAME` – Anzeigename
- `APP_VERSION` – aktuelle Version (z.B. `"1.0.0"`)
- `APP_COPYRIGHT` – Copyright-Text

Bei einem neuen Release:

1. `core/version.py` öffnen.
2. `APP_VERSION` auf die neue Version setzen, z.B. `"1.1.0"`.
3. Speichern.

Die neue Version erscheint automatisch im Fenstertitel und im **Über**-Dialog.

## 2. EXE bauen

Zum Erstellen der ausführbaren Datei wird PyInstaller verwendet.

### Variante A: Build-Skript verwenden

1. Virtuelle Umgebung aktivieren (falls nötig).
2. `build_exe.py` ausführen, z.B.:
   ```bash
   python build_exe.py
   ```
3. Nach erfolgreichem Build liegt die EXE in `dist/AdvancedGaming.exe`.

### Variante B: `build.bat` nutzen

Alternativ kannst du das mitgelieferte `build.bat` verwenden (falls entsprechend konfiguriert), z.B. per Doppelklick oder aus der Konsole.

## 3. Datei auf den Webserver hochladen

Die Anwendung erwartet die aktuelle Version immer unter dieser URL:

`https://drenor.de/programme/advanced_gaming/AdvancedGaming.exe`

Für ein neues Release:

1. Die frisch gebaute `dist/AdvancedGaming.exe` lokal testen.
2. Die geprüfte EXE auf den Webserver an genau diese Stelle hochladen und die alte Datei ersetzen.
3. (Optional) Vorher ein Backup der alten EXE machen.

**Versionsprüfung (empfohlen):** Lege auf dem Server eine Datei `version.json` im gleichen Ordner ab, z.B. Inhalt:
```json
{"version": "3.0.0", "url": "https://drenor.de/programme/advanced_gaming/AdvancedGaming.exe"}
```
Die App prüft beim Klick auf „Update“, ob eine neuere Version existiert; nur dann wird „Update verfügbar“ angezeigt. Ohne `version.json` kann der Nutzer trotzdem „Trotzdem herunterladen“ wählen.

## 4. Update-Funktion in der Anwendung

In der Toolbar des Hauptfensters gibt es den Button **"🔄 Update"**.

### 4.1 Verhalten

- Beim Klick auf **"🔄 Update"**:
  1. Die App öffnet einen **Speicher-Dialog**.
  2. Standard-Vorschlag (bei EXE-Betrieb):
     - Gleicher Ordner wie die aktuell laufende EXE.
     - Dateiname `AdvancedGaming_Update.exe` (oder dein aktueller Name + `_Update.exe`).
  3. Die EXE wird von der oben genannten URL heruntergeladen.

- Im **Entwicklungsmodus** (`python main.py`):
  - Die Datei wird nur heruntergeladen.
  - Es erfolgt ein Hinweis, dass die Selbst-Aktualisierung nur mit der EXE funktioniert.

### 4.2 Auto-Update (Selbst-Aktualisierung)

Die automatische Selbst-Aktualisierung funktioniert nur, wenn:

1. Die Anwendung als **PyInstaller-EXE** gestartet wurde.
2. Die neue EXE in **denselben Ordner** wie die laufende EXE gespeichert wird (Standard-Vorschlag im Dialog).

Dann passiert Folgendes:

1. Nach dem Download erzeugt die App im Programmordner ein Skript `advanced_gaming_updater.bat`.
2. Du wirst gefragt, ob das Update jetzt angewendet werden soll.
3. Bei **Ja**:
   - Die App startet das Batch-Skript.
   - Die App zeigt eine Info an und beendet sich.
   - Das Batch-Skript wartet, bis die alte EXE nicht mehr gesperrt ist.
   - Die neue EXE (`*_Update.exe`) wird über die alte EXE kopiert.
   - Die neue EXE wird gestartet.
   - Das Batch-Skript löscht sich selbst.

Wenn du die neue EXE in einen **anderen Ordner** speicherst, wird kein Auto-Update ausgeführt; die Datei muss dann manuell gestartet/ersetzt werden.

## 5. Typischer Release-Ablauf

1. Codeänderungen vornehmen.
2. In `core/version.py` die `APP_VERSION` anpassen (z.B. von `1.0.0` auf `1.1.0`).
3. EXE mit `build_exe.py` (oder `build.bat`) neu bauen.
4. Die neue EXE lokal kurz testen (Start, Aufnahme, Wiedergabe, Update-Button, etc.).
5. Die getestete EXE auf den Server unter
   `https://drenor.de/programme/advanced_gaming/AdvancedGaming.exe`
   hochladen und die alte Datei ersetzen.
6. Fertig – Nutzer können nun über den **"🔄 Update"**-Button in der App auf die neue Version aktualisieren.

## 6. Hinweise & Sicherheit

- Da die EXE direkt aus dem Internet geladen wird, sollte der Webserver nur vertrauenswürdige, von dir signierte/erstellte Versionen ausliefern.
- Wenn du später Code-Signing oder zusätzliche Integritätsprüfungen (z.B. Hash-Vergleich) einbauen möchtest, kannst du das Update-System entsprechend erweitern.
- Die Updater-Batch-Datei wird bei jedem Update neu erzeugt und nach erfolgreichem Update wieder gelöscht.

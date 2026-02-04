@echo off

REM Ins Skript-Verzeichnis wechseln
cd /d "%~dp0"

echo ==========================================
echo Advanced Auto Clicker v3.0 - Installation
echo ==========================================
echo.
echo Installiere ultimative Makro-Suite mit:
echo   - Bild-Erkennung (OpenCV)
echo   - Variablen ^& Bedingungen
echo   - Scheduler (zeitgesteuert)
echo   - Statistiken ^& Analytics
echo   - Multi-Monitor-Support
echo   - Pixel-Farb-Erkennung
echo   - System-Tray-Integration
echo.
echo Dieser Prozess installiert:
echo   - PyQt6 (GUI)
echo   - OpenCV (Bild-Erkennung)
echo   - NumPy (Berechnungen)
echo   - Pillow (Screenshots)
echo   - PyWin32 (Windows-API)
echo   - PyInstaller (Build)
echo.

REM Prüfen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installieren Sie Python 3.8 oder höher von https://www.python.org
    pause
    exit /b 1
)

echo [OK] Python gefunden
echo.

REM Virtuelle Umgebung erstellen
echo Erstelle virtuelle Umgebung...
python -m venv venv
if errorlevel 1 (
    echo [FEHLER] Konnte virtuelle Umgebung nicht erstellen!
    pause
    exit /b 1
)

echo [OK] Virtuelle Umgebung erstellt
echo.

REM Virtuelle Umgebung aktivieren
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat

REM Pip aktualisieren
echo Aktualisiere pip...
python -m pip install --upgrade pip

REM Prüfen ob requirements.txt existiert
if not exist "requirements.txt" (
    echo [FEHLER] requirements.txt nicht gefunden!
    echo Bitte stellen Sie sicher, dass Sie install.bat aus dem Projektordner ausführen.
    echo Aktuelles Verzeichnis: %CD%
    pause
    exit /b 1
)

REM Abhängigkeiten installieren
echo.
echo ==========================================
echo Installiere v3.0 Abhängigkeiten...
echo ==========================================
echo.
echo Dies kann einige Minuten dauern...
echo (OpenCV und NumPy sind grosse Pakete)
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [FEHLER] Konnte Abhängigkeiten nicht installieren!
    echo.
    echo Mögliche Lösungen:
    echo   1. Python 3.8+ installiert? (python --version)
    echo   2. Internet-Verbindung ok?
    echo   3. Als Administrator ausführen?
    echo   4. Microsoft Visual C++ installiert?
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Installation erfolgreich abgeschlossen!
echo ==========================================
echo.
echo Installierte Features v3.0:
echo   [√] Bild-Erkennung (OpenCV)
echo   [√] Variablen ^& Bedingungen
echo   [√] Scheduler (zeitgesteuert)
echo   [√] Statistiken ^& Analytics
echo   [√] Multi-Monitor-Support
echo   [√] Pixel-Farb-Erkennung
echo   [√] System-Tray-Integration
echo.
echo Naechste Schritte:
echo   1. start.bat          - Programm starten
echo   2. build.bat          - .exe erstellen (optional)
echo   3. QUICK_START.md     - 5-Min Tutorial lesen
echo.
echo Viel Spass mit Advanced Auto Clicker v3.0!
echo.
pause

@echo off
echo ======================================
echo Advanced Gaming - Build
echo ======================================
echo.

REM Prüfen ob virtuelle Umgebung existiert
if not exist venv\Scripts\activate.bat (
    echo [FEHLER] Virtuelle Umgebung nicht gefunden!
    echo Bitte fuehren Sie zuerst install.bat aus.
    echo.
    pause
    exit /b 1
)

REM Virtuelle Umgebung aktivieren
call venv\Scripts\activate.bat

REM PyInstaller installieren falls nicht vorhanden
echo Pruefe PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installiere PyInstaller...
    pip install pyinstaller
    echo.
)

REM Build-Script ausführen
echo Starte Build-Prozess...
echo.
python build_exe.py

if errorlevel 1 (
    echo.
    echo [FEHLER] Build fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo ======================================
echo Build erfolgreich!
echo ======================================
echo.
echo Die .exe-Datei finden Sie in:
echo   dist\AdvancedGaming.exe
echo.
echo Sie koennen die Datei jetzt an einen beliebigen Ort kopieren.
echo.
pause

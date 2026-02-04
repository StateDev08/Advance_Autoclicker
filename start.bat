@echo off
echo ======================================
echo Advanced Auto Clicker
echo ======================================
echo.

REM Virtuelle Umgebung aktivieren
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Starte Advanced Auto Clicker...
    echo.
    python main.py
) else (
    echo [FEHLER] Virtuelle Umgebung nicht gefunden!
    echo Bitte führen Sie zuerst install.bat aus.
    echo.
    pause
)

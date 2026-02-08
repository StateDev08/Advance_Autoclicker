"""
Build-Script für die Erstellung einer ausführbaren .exe-Datei
"""

import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build_exe():
    """Erstellt die ausführbare Datei"""
    
    print("=" * 60)
    print("Advanced Gaming - Build Process")
    print("=" * 60)
    print()
    
    # Arbeitsverzeichnis
    project_dir = Path(__file__).parent
    
    # Aufräumen alter Builds
    print("Räume alte Build-Dateien auf...")
    for folder in ['build', 'dist']:
        folder_path = project_dir / folder
        if folder_path.exists():
            shutil.rmtree(folder_path)
            print(f"  - {folder}/ gelöscht")
    
    print()
    print("Starte PyInstaller...")
    print()
    
    # PyInstaller-Optionen
    PyInstaller.__main__.run([
        'main.py',                          # Haupt-Skript
        '--name=AdvancedGaming',            # Name der .exe
        '--onefile',                        # Alles in einer Datei
        '--windowed',                       # Keine Konsole
        '--icon=NONE',                      # Kein Icon (kann später hinzugefügt werden)
        '--add-data=database;database',     # Database-Modul einbinden
        '--add-data=core;core',             # Core-Modul einbinden
        '--add-data=gui;gui',               # GUI-Modul einbinden
        '--hidden-import=PyQt6',
        '--hidden-import=pynput',
        '--hidden-import=pywin32',
        '--hidden-import=sqlite3',
        '--clean',                          # Cache leeren
        '--noconfirm',                      # Keine Bestätigung
    ])
    
    print()
    print("=" * 60)
    print("Build abgeschlossen!")
    print("=" * 60)
    print()
    print(f"Die ausführbare Datei befindet sich in:")
    print(f"  {project_dir / 'dist' / 'AdvancedGaming.exe'}")
    print()

if __name__ == "__main__":
    build_exe()

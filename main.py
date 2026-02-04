"""
Advanced Auto Clicker - Professionelles Makro-Tool
Haupteinstiegspunkt der Anwendung
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow

def main():
    """Hauptfunktion zum Starten der Anwendung"""
    # High DPI Support aktivieren
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Advanced Auto Clicker")
    app.setOrganizationName("AdvanceAutoClicker")
    
    # Moderne dunkle Stil setzen
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

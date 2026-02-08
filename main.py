"""
Advanced Gaming - Professionelles Makro- und Game-Automation-Tool
Haupteinstiegspunkt der Anwendung
"""

import atexit
import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow
from gui.themes import apply_theme, DEFAULT_THEME
from core.logging_system import LogManager


def is_admin():
    """Prüft, ob die Anwendung mit Administratorrechten läuft."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def _remove_log_signal_handler():
    """Entfernt den Qt-Log-Handler vor logging.shutdown (atexit läuft vor dem Shutdown)."""
    try:
        LogManager.get_instance().remove_signal_handler_from_loggers()
    except Exception:
        pass


def main():
    """Hauptfunktion zum Starten der Anwendung"""
    atexit.register(_remove_log_signal_handler)

    # High DPI Support aktivieren
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Advanced Gaming")
    app.setOrganizationName("AdvancedGaming")
    
    # Theme aus gui/themes.py anwenden (Standard: Dark)
    apply_theme(app, DEFAULT_THEME)
    
    # Admin-Check
    if not is_admin():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Keine Administratorrechte")
        msg.setText("Die Anwendung läuft ohne Administratorrechte.")
        msg.setInformativeText(
            "In vielen Spielen funktionieren Makros und das Overlay nur, wenn "
            "das Programm als Administrator ausgeführt wird.\n\n"
            "Bitte starten Sie das Programm neu mit 'Als Administrator ausführen'."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    app.aboutToQuit.connect(lambda: LogManager.get_instance().remove_signal_handler_from_loggers())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

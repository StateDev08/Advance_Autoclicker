"""
System-Tray-Integration
Minimiere zur Taskleiste, Schnellzugriff auf Makros
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject
from typing import List, Tuple, Optional


class SystemTrayManager(QObject):
    """Verwaltet System-Tray-Icon"""
    
    # Signals
    show_window = pyqtSignal()
    quit_app = pyqtSignal()
    execute_macro = pyqtSignal(int, str)  # macro_id, macro_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self.tray_menu: Optional[QMenu] = None
        self.macro_menu: Optional[QMenu] = None
        
        self.setup_tray()
    
    def setup_tray(self):
        """Richtet das Tray-Icon ein"""
        # Icon erstellen (Pixel-Art Style)
        self.tray_icon = QSystemTrayIcon(self.parent())
        
        # Versuche Icon zu laden, sonst Standard
        try:
            icon = QIcon("icon.ico")
            if icon.isNull():
                # Fallback: Text-basiertes Icon
                from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
                pixmap = QPixmap(64, 64)
                pixmap.fill(QColor(0, 0, 0, 0))
                
                painter = QPainter(pixmap)
                painter.setBrush(QColor(0, 200, 255))
                painter.drawEllipse(2, 2, 60, 60)
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Arial", 32, QFont.Weight.Bold))
                painter.drawText(pixmap.rect(), 0x84, "A")  # AlignCenter
                painter.end()
                
                icon = QIcon(pixmap)
            
            self.tray_icon.setIcon(icon)
        except Exception:
            pass
        
        # Menü erstellen
        self.tray_menu = QMenu()
        
        # Anzeigen
        show_action = QAction("🪟 Fenster anzeigen", self)
        show_action.triggered.connect(self.show_window.emit)
        self.tray_menu.addAction(show_action)
        
        self.tray_menu.addSeparator()
        
        # Makro-Untermenü
        self.macro_menu = QMenu("⚡ Schnell-Start Makro")
        self.tray_menu.addMenu(self.macro_menu)
        
        self.tray_menu.addSeparator()
        
        # Beenden
        quit_action = QAction("🚪 Beenden", self)
        quit_action.triggered.connect(self.quit_app.emit)
        self.tray_menu.addAction(quit_action)
        
        # Menü setzen
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Doppelklick = Fenster anzeigen
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Tooltip
        self.tray_icon.setToolTip("Advanced Gaming - Makro- & Game-Automatisierung")
    
    def _on_tray_activated(self, reason):
        """Callback wenn Tray-Icon aktiviert wird"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window.emit()
    
    def show(self):
        """Zeigt das Tray-Icon"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide(self):
        """Versteckt das Tray-Icon"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def show_message(self, title: str, message: str, 
                    icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                    duration: int = 3000):
        """
        Zeigt eine Benachrichtigung
        
        Args:
            title: Titel der Benachrichtigung
            message: Nachricht
            icon: Icon-Typ
            duration: Anzeigedauer in ms
        """
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, duration)
    
    def update_macros(self, macros: List[Tuple[int, str]]):
        """
        Aktualisiert Makro-Schnellzugriff-Menü
        
        Args:
            macros: Liste von (macro_id, macro_name) Tupeln
        """
        if not self.macro_menu:
            return
        
        # Altes Menü leeren
        self.macro_menu.clear()
        
        if not macros:
            no_macros_action = QAction("Keine Makros verfügbar", self)
            no_macros_action.setEnabled(False)
            self.macro_menu.addAction(no_macros_action)
            return
        
        # Makros hinzufügen (max 10)
        for macro_id, macro_name in macros[:10]:
            action = QAction(f"▶️ {macro_name}", self)
            action.triggered.connect(
                lambda checked, mid=macro_id, mname=macro_name: 
                self.execute_macro.emit(mid, mname)
            )
            self.macro_menu.addAction(action)
        
        # Falls mehr als 10
        if len(macros) > 10:
            self.macro_menu.addSeparator()
            more_action = QAction(f"... und {len(macros) - 10} weitere", self)
            more_action.setEnabled(False)
            self.macro_menu.addAction(more_action)
    
    def set_tooltip(self, text: str):
        """Setzt den Tooltip-Text"""
        if self.tray_icon:
            self.tray_icon.setToolTip(text)
    
    def notify_macro_started(self, macro_name: str):
        """Benachrichtigt über gestartetes Makro"""
        self.show_message(
            "Makro gestartet",
            f"'{macro_name}' wird ausgeführt...",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def notify_macro_completed(self, macro_name: str, success: bool):
        """Benachrichtigt über abgeschlossenes Makro"""
        if success:
            self.show_message(
                "Makro abgeschlossen",
                f"'{macro_name}' erfolgreich beendet!",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.show_message(
                "Makro abgebrochen",
                f"'{macro_name}' wurde gestoppt.",
                QSystemTrayIcon.MessageIcon.Warning,
                3000
            )
    
    def notify_error(self, message: str):
        """Benachrichtigt über Fehler"""
        self.show_message(
            "Fehler",
            message,
            QSystemTrayIcon.MessageIcon.Critical,
            5000
        )

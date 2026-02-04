"""
Log-Viewer für Live-Log-Anzeige
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QComboBox, QLabel, QCheckBox)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QTextCursor, QColor
from core.logging_system import get_logger


class LogViewerWidget(QWidget):
    """Widget für Live-Log-Anzeige"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_lines = 1000
        self.auto_scroll = True
        self.setup_ui()
        self.connect_logger()
    
    def setup_ui(self):
        """Erstellt das UI"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.cmb_level = QComboBox()
        self.cmb_level.addItems(['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR'])
        self.cmb_level.setCurrentText('INFO')
        self.cmb_level.currentTextChanged.connect(self.on_level_changed)
        toolbar.addWidget(QLabel("Level:"))
        toolbar.addWidget(self.cmb_level)
        
        self.chk_auto_scroll = QCheckBox("Auto-Scroll")
        self.chk_auto_scroll.setChecked(True)
        self.chk_auto_scroll.toggled.connect(self.on_auto_scroll_changed)
        toolbar.addWidget(self.chk_auto_scroll)
        
        toolbar.addStretch()
        
        btn_clear = QPushButton("🗑️ Leeren")
        btn_clear.clicked.connect(self.clear_logs)
        toolbar.addWidget(btn_clear)
        
        btn_save = QPushButton("💾 Speichern")
        btn_save.clicked.connect(self.save_logs)
        toolbar.addWidget(btn_save)
        
        layout.addLayout(toolbar)
        
        # Log-Ausgabe
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.txt_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.txt_log)
        
        # Info
        self.lbl_info = QLabel("Zeigt Live-Logs der Anwendung")
        self.lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_info)
    
    def connect_logger(self):
        """Verbindet mit dem Logging-System"""
        try:
            logger = get_logger()
            signal_handler = logger.get_signal_handler()
            signal_handler.log_message.connect(self.on_log_message)
        except Exception as e:
            self.txt_log.append(f"Fehler beim Verbinden mit Logger: {e}")
    
    @pyqtSlot(str, str)
    def on_log_message(self, level: str, message: str):
        """Handler für neue Log-Nachrichten"""
        # Level-Filter
        min_level = self.cmb_level.currentText()
        if min_level != 'ALL':
            level_priority = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
            if level_priority.get(level, 0) < level_priority.get(min_level, 0):
                return
        
        # Farbcodierung basierend auf Level
        color = self.get_level_color(level)
        
        # HTML-formatierte Nachricht
        html_message = f'<span style="color: {color};">{message}</span>'
        
        self.txt_log.append(html_message)
        
        # Zeilen-Limit
        if self.txt_log.document().lineCount() > self.max_lines:
            cursor = self.txt_log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        
        # Auto-Scroll
        if self.auto_scroll:
            scrollbar = self.txt_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def get_level_color(self, level: str) -> str:
        """Gibt Farbe für Log-Level zurück"""
        colors = {
            'DEBUG': '#808080',      # Grau
            'INFO': '#00ff00',       # Grün
            'WARNING': '#ffff00',    # Gelb
            'ERROR': '#ff0000',      # Rot
            'CRITICAL': '#ff00ff'    # Magenta
        }
        return colors.get(level, '#d4d4d4')
    
    def on_level_changed(self, level: str):
        """Handler für Level-Änderung"""
        self.lbl_info.setText(f"Zeigt {level} und höher")
    
    def on_auto_scroll_changed(self, checked: bool):
        """Handler für Auto-Scroll Änderung"""
        self.auto_scroll = checked
    
    def clear_logs(self):
        """Leert die Log-Anzeige"""
        self.txt_log.clear()
    
    def save_logs(self):
        """Speichert Logs in Datei"""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Logs speichern",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.txt_log.toPlainText())
                self.lbl_info.setText(f"Logs gespeichert: {filename}")
            except Exception as e:
                self.lbl_info.setText(f"Fehler beim Speichern: {e}")

"""
Erweiterter Makro-Editor
Ermöglicht manuelle Bearbeitung von Aktionen, Drag & Drop, Hinzufügen neuer Aktionen
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QDialog, QFormLayout,
                             QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QLabel, QMessageBox, QTextEdit, QGroupBox, QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from typing import List, Dict, Optional
import json


class ActionEditorDialog(QDialog):
    """Dialog zum Bearbeiten einer einzelnen Aktion"""
    
    def __init__(self, action: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.action = action or {}
        self.setup_ui()
        self.load_action()
    
    def setup_ui(self):
        """Erstellt das UI"""
        self.setWindowTitle("Aktion bearbeiten")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Action-Typ Auswahl
        form = QFormLayout()
        
        self.cmb_type = QComboBox()
        self.cmb_type.addItems([
            "mouse_click",
            "mouse_move",
            "mouse_scroll",
            "key_press",
            "key_release",
            "wait",
            "set_variable",
            "if_condition",
            "click_on_image",
            "wait_for_image",
            "log_message"
        ])
        self.cmb_type.currentTextChanged.connect(self.on_type_changed)
        form.addRow("Typ:", self.cmb_type)
        
        self.txt_delay = QDoubleSpinBox()
        self.txt_delay.setRange(0, 999999)
        self.txt_delay.setDecimals(3)
        self.txt_delay.setSuffix(" s")
        form.addRow("Verzögerung:", self.txt_delay)
        
        layout.addLayout(form)
        
        # Container für typ-spezifische Felder
        self.param_group = QGroupBox("Parameter")
        self.param_layout = QFormLayout()
        self.param_group.setLayout(self.param_layout)
        layout.addWidget(self.param_group)
        
        # Parameter-Widgets (werden dynamisch erstellt)
        self.param_widgets = {}
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Speichern")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        # Initiales Update
        self.on_type_changed(self.cmb_type.currentText())
    
    def on_type_changed(self, action_type: str):
        """Aktualisiert Parameter-Felder basierend auf Action-Typ"""
        # Alte Widgets entfernen
        for widget in self.param_widgets.values():
            if isinstance(widget, QWidget):
                widget.deleteLater()
        self.param_widgets.clear()
        
        # Layout leeren
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Neue Widgets basierend auf Typ
        if action_type in ['mouse_click', 'mouse_move']:
            self.param_widgets['x'] = QSpinBox()
            self.param_widgets['x'].setRange(-9999, 9999)
            self.param_layout.addRow("X:", self.param_widgets['x'])
            
            self.param_widgets['y'] = QSpinBox()
            self.param_widgets['y'].setRange(-9999, 9999)
            self.param_layout.addRow("Y:", self.param_widgets['y'])
            
            if action_type == 'mouse_click':
                self.param_widgets['button'] = QComboBox()
                self.param_widgets['button'].addItems(['left', 'right', 'middle', 'x1', 'x2'])
                self.param_layout.addRow("Button:", self.param_widgets['button'])
                
                self.param_widgets['pressed'] = QCheckBox("Gedrückt (sonst losgelassen)")
                self.param_widgets['pressed'].setChecked(True)
                self.param_layout.addRow("", self.param_widgets['pressed'])
        
        elif action_type == 'mouse_scroll':
            self.param_widgets['x'] = QSpinBox()
            self.param_widgets['x'].setRange(-9999, 9999)
            self.param_layout.addRow("X:", self.param_widgets['x'])
            
            self.param_widgets['y'] = QSpinBox()
            self.param_widgets['y'].setRange(-9999, 9999)
            self.param_layout.addRow("Y:", self.param_widgets['y'])
            
            self.param_widgets['dx'] = QSpinBox()
            self.param_widgets['dx'].setRange(-100, 100)
            self.param_layout.addRow("Scroll X:", self.param_widgets['dx'])
            
            self.param_widgets['dy'] = QSpinBox()
            self.param_widgets['dy'].setRange(-100, 100)
            self.param_layout.addRow("Scroll Y:", self.param_widgets['dy'])
        
        elif action_type in ['key_press', 'key_release']:
            self.param_widgets['key'] = QLineEdit()
            self.param_widgets['key'].setPlaceholderText("z.B. 'a' oder 'Key.space'")
            self.param_layout.addRow("Taste:", self.param_widgets['key'])
        
        elif action_type == 'wait':
            self.param_widgets['duration'] = QDoubleSpinBox()
            self.param_widgets['duration'].setRange(0, 999999)
            self.param_widgets['duration'].setDecimals(3)
            self.param_widgets['duration'].setSuffix(" s")
            self.param_widgets['duration'].setValue(1.0)
            self.param_layout.addRow("Dauer:", self.param_widgets['duration'])
        
        elif action_type == 'set_variable':
            self.param_widgets['name'] = QLineEdit()
            self.param_widgets['name'].setPlaceholderText("Variable Name")
            self.param_layout.addRow("Name:", self.param_widgets['name'])
            
            self.param_widgets['value'] = QLineEdit()
            self.param_widgets['value'].setPlaceholderText("Wert oder Ausdruck")
            self.param_layout.addRow("Wert:", self.param_widgets['value'])
        
        elif action_type == 'if_condition':
            self.param_widgets['condition'] = QLineEdit()
            self.param_widgets['condition'].setPlaceholderText("{var} > 10")
            self.param_layout.addRow("Bedingung:", self.param_widgets['condition'])
            
            label = QLabel("True/False Aktionen müssen im JSON bearbeitet werden")
            label.setWordWrap(True)
            self.param_layout.addRow("", label)
        
        elif action_type in ['click_on_image', 'wait_for_image']:
            self.param_widgets['template'] = QLineEdit()
            self.param_widgets['template'].setPlaceholderText("Template Name")
            self.param_layout.addRow("Template:", self.param_widgets['template'])
            
            self.param_widgets['confidence'] = QDoubleSpinBox()
            self.param_widgets['confidence'].setRange(0.0, 1.0)
            self.param_widgets['confidence'].setDecimals(2)
            self.param_widgets['confidence'].setSingleStep(0.05)
            self.param_widgets['confidence'].setValue(0.8)
            self.param_layout.addRow("Konfidenz:", self.param_widgets['confidence'])
            
            if action_type == 'wait_for_image':
                self.param_widgets['timeout'] = QDoubleSpinBox()
                self.param_widgets['timeout'].setRange(0.1, 999)
                self.param_widgets['timeout'].setDecimals(1)
                self.param_widgets['timeout'].setSuffix(" s")
                self.param_widgets['timeout'].setValue(10.0)
                self.param_layout.addRow("Timeout:", self.param_widgets['timeout'])
            
            if action_type == 'click_on_image':
                self.param_widgets['button'] = QComboBox()
                self.param_widgets['button'].addItems(['left', 'right', 'middle'])
                self.param_layout.addRow("Button:", self.param_widgets['button'])
                
                self.param_widgets['offset_x'] = QSpinBox()
                self.param_widgets['offset_x'].setRange(-500, 500)
                self.param_layout.addRow("Offset X:", self.param_widgets['offset_x'])
                
                self.param_widgets['offset_y'] = QSpinBox()
                self.param_widgets['offset_y'].setRange(-500, 500)
                self.param_layout.addRow("Offset Y:", self.param_widgets['offset_y'])
        
        elif action_type == 'log_message':
            self.param_widgets['message'] = QLineEdit()
            self.param_widgets['message'].setPlaceholderText("Log-Nachricht")
            self.param_layout.addRow("Nachricht:", self.param_widgets['message'])
            
            self.param_widgets['level'] = QComboBox()
            self.param_widgets['level'].addItems(['info', 'debug', 'warning', 'error'])
            self.param_layout.addRow("Level:", self.param_widgets['level'])
    
    def load_action(self):
        """Lädt Aktion in UI"""
        if not self.action:
            return
        
        # Typ setzen
        action_type = self.action.get('type', 'mouse_click')
        index = self.cmb_type.findText(action_type)
        if index >= 0:
            self.cmb_type.setCurrentIndex(index)
        
        # Verzögerung
        self.txt_delay.setValue(self.action.get('delay', 0))
        
        # Parameter laden
        for key, widget in self.param_widgets.items():
            if key in self.action:
                value = self.action[key]
                
                if isinstance(widget, QSpinBox):
                    widget.setValue(int(value))
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value))
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
    
    def get_action(self) -> Dict:
        """Gibt die bearbeitete Aktion zurück"""
        action = {
            'type': self.cmb_type.currentText(),
            'delay': self.txt_delay.value()
        }
        
        # Parameter auslesen
        for key, widget in self.param_widgets.items():
            if isinstance(widget, QSpinBox):
                action[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                action[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                text = widget.text()
                # Versuche als Zahl zu parsen
                try:
                    action[key] = int(text)
                except ValueError:
                    try:
                        action[key] = float(text)
                    except ValueError:
                        action[key] = text
            elif isinstance(widget, QComboBox):
                action[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                action[key] = widget.isChecked()
        
        return action


class MacroEditorWidget(QWidget):
    """Widget für erweiterten Makro-Editor"""
    
    actions_changed = pyqtSignal()  # Signal wenn Aktionen geändert wurden
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.actions: List[Dict] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt das UI"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("➕ Aktion hinzufügen")
        btn_add.clicked.connect(self.add_action)
        toolbar.addWidget(btn_add)
        
        btn_edit = QPushButton("✏️ Bearbeiten")
        btn_edit.clicked.connect(self.edit_action)
        toolbar.addWidget(btn_edit)
        
        btn_duplicate = QPushButton("📋 Duplizieren")
        btn_duplicate.clicked.connect(self.duplicate_action)
        toolbar.addWidget(btn_duplicate)
        
        btn_delete = QPushButton("🗑️ Löschen")
        btn_delete.clicked.connect(self.delete_action)
        toolbar.addWidget(btn_delete)
        
        toolbar.addStretch()
        
        btn_move_up = QPushButton("⬆️")
        btn_move_up.clicked.connect(self.move_up)
        toolbar.addWidget(btn_move_up)
        
        btn_move_down = QPushButton("⬇️")
        btn_move_down.clicked.connect(self.move_down)
        toolbar.addWidget(btn_move_down)
        
        layout.addLayout(toolbar)
        
        # Action Liste
        self.list_actions = QListWidget()
        self.list_actions.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_actions.itemDoubleClicked.connect(self.edit_action)
        self.list_actions.model().rowsMoved.connect(self.on_rows_moved)
        layout.addWidget(self.list_actions)
        
        # Info Label
        self.lbl_info = QLabel("Doppelklick zum Bearbeiten | Drag & Drop zum Umsortieren")
        self.lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_info)
    
    def set_actions(self, actions: List[Dict]):
        """Setzt die Aktionen"""
        self.actions = actions.copy()
        self.refresh_list()
    
    def get_actions(self) -> List[Dict]:
        """Gibt die Aktionen zurück"""
        return self.actions.copy()
    
    def refresh_list(self):
        """Aktualisiert die Liste"""
        self.list_actions.clear()
        
        for i, action in enumerate(self.actions):
            action_type = action.get('type', 'unknown')
            delay = action.get('delay', 0)
            
            # Beschreibung erstellen
            desc = self.get_action_description(action)
            
            text = f"{i+1}. [{action_type}] {desc}"
            if delay > 0:
                text += f" (⏱️ {delay:.3f}s)"
            
            self.list_actions.addItem(text)
    
    def get_action_description(self, action: Dict) -> str:
        """Erstellt eine lesbare Beschreibung der Aktion"""
        action_type = action.get('type', '')
        
        if action_type == 'mouse_click':
            x, y = action.get('x', 0), action.get('y', 0)
            button = action.get('button', 'left')
            return f"{button} click at ({x}, {y})"
        
        elif action_type == 'mouse_move':
            x, y = action.get('x', 0), action.get('y', 0)
            return f"move to ({x}, {y})"
        
        elif action_type == 'key_press':
            key = action.get('key', '')
            return f"press '{key}'"
        
        elif action_type == 'key_release':
            key = action.get('key', '')
            return f"release '{key}'"
        
        elif action_type == 'wait':
            duration = action.get('duration', 0)
            return f"wait {duration}s"
        
        elif action_type == 'set_variable':
            name = action.get('name', '')
            value = action.get('value', '')
            return f"{name} = {value}"
        
        elif action_type == 'if_condition':
            condition = action.get('condition', '')
            return f"if {condition}"
        
        elif action_type == 'click_on_image':
            template = action.get('template', '')
            return f"click on '{template}'"
        
        elif action_type == 'wait_for_image':
            template = action.get('template', '')
            timeout = action.get('timeout', 10)
            return f"wait for '{template}' ({timeout}s)"
        
        elif action_type == 'log_message':
            msg = action.get('message', '')
            return f"log: {msg}"
        
        return ""
    
    def add_action(self):
        """Fügt eine neue Aktion hinzu"""
        dialog = ActionEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_action = dialog.get_action()
            self.actions.append(new_action)
            self.refresh_list()
            self.actions_changed.emit()
    
    def edit_action(self):
        """Bearbeitet die ausgewählte Aktion"""
        current_row = self.list_actions.currentRow()
        if current_row < 0 or current_row >= len(self.actions):
            return
        
        dialog = ActionEditorDialog(self.actions[current_row], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.actions[current_row] = dialog.get_action()
            self.refresh_list()
            self.list_actions.setCurrentRow(current_row)
            self.actions_changed.emit()
    
    def duplicate_action(self):
        """Dupliziert die ausgewählte Aktion"""
        current_row = self.list_actions.currentRow()
        if current_row < 0 or current_row >= len(self.actions):
            return
        
        duplicated = self.actions[current_row].copy()
        self.actions.insert(current_row + 1, duplicated)
        self.refresh_list()
        self.list_actions.setCurrentRow(current_row + 1)
        self.actions_changed.emit()
    
    def delete_action(self):
        """Löscht die ausgewählte Aktion"""
        current_row = self.list_actions.currentRow()
        if current_row < 0 or current_row >= len(self.actions):
            return
        
        reply = QMessageBox.question(
            self,
            "Aktion löschen",
            "Möchten Sie diese Aktion wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.actions[current_row]
            self.refresh_list()
            self.actions_changed.emit()
    
    def move_up(self):
        """Verschiebt Aktion nach oben"""
        current_row = self.list_actions.currentRow()
        if current_row <= 0:
            return
        
        self.actions[current_row], self.actions[current_row - 1] = \
            self.actions[current_row - 1], self.actions[current_row]
        
        self.refresh_list()
        self.list_actions.setCurrentRow(current_row - 1)
        self.actions_changed.emit()
    
    def move_down(self):
        """Verschiebt Aktion nach unten"""
        current_row = self.list_actions.currentRow()
        if current_row < 0 or current_row >= len(self.actions) - 1:
            return
        
        self.actions[current_row], self.actions[current_row + 1] = \
            self.actions[current_row + 1], self.actions[current_row]
        
        self.refresh_list()
        self.list_actions.setCurrentRow(current_row + 1)
        self.actions_changed.emit()
    
    def on_rows_moved(self):
        """Handler für Drag & Drop Neuordnung"""
        # Aktionen aus neuer Reihenfolge in Liste extrahieren
        new_actions = []
        for i in range(self.list_actions.count()):
            item_text = self.list_actions.item(i).text()
            # Extrahiere Index aus Text
            try:
                old_index = int(item_text.split('.')[0]) - 1
                if 0 <= old_index < len(self.actions):
                    new_actions.append(self.actions[old_index])
            except:
                pass
        
        if len(new_actions) == len(self.actions):
            self.actions = new_actions
            self.refresh_list()
            self.actions_changed.emit()

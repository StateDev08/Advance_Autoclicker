"""
Aufnahme Tab - Für das Aufzeichnen von Makros
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QLineEdit, QTextEdit, QMessageBox,
                              QGroupBox, QTableWidget, QTableWidgetItem,
                              QHeaderView, QComboBox, QDialog, QDialogButtonBox,
                              QSpinBox, QCheckBox, QDoubleSpinBox, QScrollArea, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from database import DatabaseManager
from core import MacroRecorder
from pynput import keyboard, mouse
import time

class RecorderTab(QWidget):
    """Tab für Makro-Aufnahme"""
    
    macro_saved = pyqtSignal()
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.recorder = MacroRecorder()
        self.is_recording = False  # Public für Hotkey-Zugriff
        self.start_time = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Steuerung
        control_group = QGroupBox("Aufnahme-Steuerung")
        control_layout = QVBoxLayout()
        
        info_label = QLabel(
            "Drücken Sie 'Aufnahme starten' um Maus- und Tastaturaktionen aufzuzeichnen.\n"
            "Verwenden Sie 'Aufnahme stoppen' um die Aufnahme zu beenden."
        )
        info_label.setWordWrap(True)
        control_layout.addWidget(info_label)
        
        # Aufnahme-Optionen
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Aufnehmen:"))
        
        # "Maus" steuert Bewegungen & normale Klicks (Links/Rechts/Mitte).
        # Seitentasten (Mouse4/Mouse5, x1/x2) werden immer aufgezeichnet,
        # damit sie als Makrotasten nutzbar bleiben – auch wenn dieses Häkchen aus ist.
        self.chk_record_mouse = QCheckBox("Maus (Bewegung + Links/Rechts/Mitte)")
        self.chk_record_mouse.setChecked(True)
        options_layout.addWidget(self.chk_record_mouse)
        
        self.chk_record_keyboard = QCheckBox("Tastatur")
        self.chk_record_keyboard.setChecked(True)
        options_layout.addWidget(self.chk_record_keyboard)
        
        options_layout.addStretch()
        control_layout.addLayout(options_layout)
        
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("🎙️ Aufnahme starten")
        self.btn_start.clicked.connect(self.start_recording)
        self.btn_start.setStyleSheet("QPushButton { font-size: 14pt; padding: 10px; }")
        btn_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹️ Aufnahme stoppen")
        self.btn_stop.clicked.connect(self.stop_recording)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("QPushButton { font-size: 14pt; padding: 10px; }")
        btn_layout.addWidget(self.btn_stop)
        
        control_layout.addLayout(btn_layout)
        
        # Status
        self.lbl_status = QLabel("Bereit zum Aufnehmen")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("QLabel { font-size: 12pt; font-weight: bold; }")
        control_layout.addWidget(self.lbl_status)
        
        self.lbl_timer = QLabel("00:00")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_timer.setStyleSheet("QLabel { font-size: 16pt; color: red; }")
        self.lbl_timer.setVisible(False)
        control_layout.addWidget(self.lbl_timer)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Aufgezeichnete Aktionen
        actions_group = QGroupBox("Aufgezeichnete Aktionen")
        actions_layout = QVBoxLayout()
        
        self.lbl_action_count = QLabel("Aktionen: 0")
        actions_layout.addWidget(self.lbl_action_count)
        
        self.table_actions = QTableWidget()
        self.table_actions.setColumnCount(4)
        self.table_actions.setHorizontalHeaderLabels(["#", "Typ", "Details", "Verzögerung (s)"])
        self.table_actions.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_actions.setMinimumHeight(200)
        actions_layout.addWidget(self.table_actions)
        
        # Buttons für Aktionen
        action_btn_layout = QHBoxLayout()
        
        self.btn_clear = QPushButton("🗑️ Löschen")
        self.btn_clear.clicked.connect(self.clear_actions)
        action_btn_layout.addWidget(self.btn_clear)
        
        self.btn_save = QPushButton("💾 Speichern")
        self.btn_save.clicked.connect(self.save_macro)
        action_btn_layout.addWidget(self.btn_save)
        
        actions_layout.addLayout(action_btn_layout)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Timer für Aufnahmedauer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
    
    def start_recording(self):
        """Startet die Aufnahme"""
        # Prüfen ob mindestens eine Option gewählt ist
        if not self.chk_record_mouse.isChecked() and not self.chk_record_keyboard.isChecked():
            QMessageBox.warning(
                self,
                "Warnung",
                "Bitte wählen Sie mindestens eine Option (Maus oder Tastatur)!"
            )
            return

        # Aufnahmeeinstellungen aus Datenbank übernehmen (Maus-Schwelle)
        try:
            threshold_ms = int(self.db.get_setting('mouse_threshold', '50'))
        except Exception:
            threshold_ms = 50
        # In Sekunden konvertieren, minimale Schwelle 5ms
        self.recorder.mouse_move_threshold = max(threshold_ms / 1000.0, 0.005)

        self.is_recording = True
        self.start_time = time.time()
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("🔴 AUFNAHME LÄUFT")
        self.lbl_timer.setVisible(True)
        self.table_actions.setRowCount(0)
        
        # Aufnahme mit Filtern starten
        self.recorder.record_mouse = self.chk_record_mouse.isChecked()
        self.recorder.record_keyboard = self.chk_record_keyboard.isChecked()
        
        self.recorder.start_recording(on_action=self.on_action_recorded)
        self.timer.start(100)  # Update alle 100ms
        
        self.recording_started.emit()
        
        QMessageBox.information(
            self,
            "Aufnahme gestartet",
            "Die Aufnahme wurde gestartet!\n\n"
            "Alle Maus- und Tastaturaktionen werden jetzt aufgezeichnet.\n"
            "Klicken Sie auf 'Aufnahme stoppen' wenn Sie fertig sind."
        )
    
    def stop_recording(self):
        """Stoppt die Aufnahme"""
        self.is_recording = False
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Aufnahme beendet")
        self.lbl_timer.setVisible(False)
        
        self.recorder.stop_recording()
        self.timer.stop()
        
        self.recording_stopped.emit()
        
        action_count = len(self.recorder.actions)
        QMessageBox.information(
            self,
            "Aufnahme beendet",
            f"Die Aufnahme wurde beendet!\n\n"
            f"Es wurden {action_count} Aktionen aufgezeichnet.\n"
            f"Sie können das Makro jetzt speichern."
        )
    
    def update_timer(self):
        """Aktualisiert den Timer"""
        if self.is_recording and self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.lbl_timer.setText(f"{minutes:02d}:{seconds:02d}")
    
    def on_action_recorded(self, action: dict):
        """Callback wenn eine Aktion aufgezeichnet wurde"""
        row = self.table_actions.rowCount()
        self.table_actions.insertRow(row)
        
        # Nummer
        self.table_actions.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        
        # Typ
        self.table_actions.setItem(row, 1, QTableWidgetItem(action.get('type', '')))
        
        # Details
        details = []
        for key, value in action.items():
            if key not in ['type', 'delay', 'timestamp']:
                details.append(f"{key}={value}")
        self.table_actions.setItem(row, 2, QTableWidgetItem(", ".join(details)))
        
        # Verzögerung
        self.table_actions.setItem(row, 3, QTableWidgetItem(f"{action.get('delay', 0):.3f}"))
        
        # Automatisch nach unten scrollen
        self.table_actions.scrollToBottom()
        
        # Zähler aktualisieren
        self.lbl_action_count.setText(f"Aktionen: {row + 1}")
    
    def clear_actions(self):
        """Löscht alle aufgezeichneten Aktionen"""
        reply = QMessageBox.question(
            self,
            "Aktionen löschen",
            "Möchten Sie wirklich alle aufgezeichneten Aktionen löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.recorder.actions = []
            self.table_actions.setRowCount(0)
            self.lbl_action_count.setText("Aktionen: 0")
    
    def save_macro(self):
        """Speichert das aufgezeichnete Makro"""
        if not self.recorder.actions:
            QMessageBox.warning(self, "Warnung", "Es wurden keine Aktionen aufgezeichnet!")
            return
        
        # Profile laden
        profiles = self.db.get_profiles()
        if not profiles:
            QMessageBox.warning(
                self,
                "Warnung",
                "Es existieren noch keine Profile!\n\n"
                "Bitte erstellen Sie zuerst ein Profil im Profile-Tab."
            )
            return
        
        # Dialog zum Speichern
        dialog = SaveMacroDialog(self, profiles, self.recorder.actions)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.create_macro(
                    data['profile_id'],
                    data['name'],
                    self.recorder.actions,
                    data['description'],
                    data['hotkey'],
                    data['loop_count'],
                    data['loop_infinite'],
                    data['delay_between_loops'],
                    data['window_filter']
                )
                QMessageBox.information(self, "Erfolg", "Makro gespeichert!")
                self.macro_saved.emit()
                self.clear_actions()
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}")

class SaveMacroDialog(QDialog):
    """Dialog zum Speichern eines aufgezeichneten Makros"""
    
    def __init__(self, parent, profiles, actions):
        super().__init__(parent)
        self.setWindowTitle("Makro speichern")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.profiles = profiles
        self.actions = actions
        self.hotkey_listener = None
        self.mouse_listener = None
        self.recording_field = None
        self.pressed_keys = set()
        self.last_hotkey = ""  # Speichert den zuletzt aufgenommenen Hotkey
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI"""
        layout = QVBoxLayout(self)
        
        # Profil auswählen
        layout.addWidget(QLabel("Profil:"))
        self.combo_profile = QComboBox()
        for profile in self.profiles:
            self.combo_profile.addItem(profile['name'], profile['id'])
        layout.addWidget(self.combo_profile)
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.txt_name = QLineEdit()
        layout.addWidget(self.txt_name)
        
        # Beschreibung
        layout.addWidget(QLabel("Beschreibung (optional):"))
        self.txt_description = QTextEdit()
        self.txt_description.setMaximumHeight(60)
        layout.addWidget(self.txt_description)
        
        # Hotkey
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Hotkey (optional):"))
        
        hotkey_input_layout = QHBoxLayout()
        self.txt_hotkey = QLineEdit()
        self.txt_hotkey.setPlaceholderText("z.B. ctrl+shift+a")
        hotkey_input_layout.addWidget(self.txt_hotkey)
        
        self.btn_record_hotkey = QPushButton("🎙️ Aufnahme")
        self.btn_record_hotkey.setMaximumWidth(100)
        self.btn_record_hotkey.clicked.connect(self.start_hotkey_recording)
        hotkey_input_layout.addWidget(self.btn_record_hotkey)
        
        hotkey_layout.addLayout(hotkey_input_layout)
        layout.addLayout(hotkey_layout)
        
        # Wiederholung
        repeat_layout = QHBoxLayout()
        
        self.chk_infinite = QCheckBox("Unendlich wiederholen")
        self.chk_infinite.stateChanged.connect(self.on_infinite_changed)
        repeat_layout.addWidget(self.chk_infinite)
        
        repeat_layout.addWidget(QLabel("Wiederholungen:"))
        self.spin_loops = QSpinBox()
        self.spin_loops.setMinimum(1)
        self.spin_loops.setMaximum(99999)
        self.spin_loops.setValue(1)
        repeat_layout.addWidget(self.spin_loops)
        
        repeat_layout.addWidget(QLabel("Verzögerung (s):"))
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setMinimum(0)
        self.spin_delay.setMaximum(3600)
        self.spin_delay.setSingleStep(0.1)
        self.spin_delay.setValue(0.0)
        repeat_layout.addWidget(self.spin_delay)
        
        layout.addLayout(repeat_layout)
        
        # Window-Filter
        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Fenster-Filter (optional):"))
        
        btn_detect_window = QPushButton("🎯 Aktuelles Fenster erfassen")
        btn_detect_window.clicked.connect(self.detect_current_window)
        btn_detect_window.setToolTip("Erfasst das aktuell aktive Fenster")
        window_layout.addWidget(btn_detect_window)
        window_layout.addStretch()
        
        layout.addLayout(window_layout)
        
        self.txt_window_filter = QLineEdit()
        self.txt_window_filter.setPlaceholderText("Leer = Alle Fenster | z.B. 'Notepad' oder 'chrome.exe'")
        layout.addWidget(self.txt_window_filter)
        
        # Fenster-Info anzeigen
        from core import WindowDetector
        window_info = WindowDetector.get_active_window_info()
        info_text = f"<small>Aktuell: <b>{window_info['title']}</b> ({window_info['process']})</small>"
        self.lbl_current_window = QLabel(info_text)
        self.lbl_current_window.setWordWrap(True)
        layout.addWidget(self.lbl_current_window)
        
        # Info
        info_label = QLabel(f"<small>Es werden {len(self.actions)} Aktionen gespeichert.</small>")
        layout.addWidget(info_label)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def on_infinite_changed(self, state):
        """Callback wenn Unendlich-Checkbox geändert wird"""
        self.spin_loops.setEnabled(state != Qt.CheckState.Checked.value)
    
    def detect_current_window(self):
        """Erfasst das aktuell aktive Fenster"""
        from core import WindowDetector
        from PyQt6.QtWidgets import QApplication
        import time
        
        # Kurz warten damit User zum Zielfenster wechseln kann
        reply = QMessageBox.information(
            self,
            "Fenster erfassen",
            "Klicken Sie OK und wechseln Sie dann innerhalb von 3 Sekunden \n"
            "zum Fenster, in dem das Makro ausgeführt werden soll.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Ok:
            # Countdown anzeigen
            for i in range(3, 0, -1):
                self.lbl_current_window.setText(f"<b>Erfassung in {i}...</b>")
                QApplication.processEvents()
                time.sleep(1)
            
            # Fenster erfassen
            window_info = WindowDetector.get_active_window_info()
            
            # Fenster-Titel verwenden (am spezifischsten)
            filter_text = window_info['title']
            if not filter_text:
                filter_text = window_info['process']
            
            self.txt_window_filter.setText(filter_text)
            
            info_text = f"<small>Erfasst: <b>{window_info['title']}</b> ({window_info['process']})</small>"
            self.lbl_current_window.setText(info_text)
            self.lbl_current_window.setStyleSheet("QLabel { color: green; }")
    
    def start_hotkey_recording(self):
        """Startet die Aufnahme einer Tastenkombination"""
        if self.recording_field is not None:
            # Es läuft bereits eine Aufnahme
            QMessageBox.warning(self, "Hinweis", "Es läuft bereits eine Hotkey-Aufnahme!")
            return
        
        self.recording_field = self.txt_hotkey
        self.pressed_keys.clear()
        
        # Feld visuell markieren
        self.txt_hotkey.setStyleSheet("QLineEdit { background-color: #ffffcc; border: 2px solid #ff6600; }")
        self.txt_hotkey.setText("Drücken Sie die gewünschte Tastenkombination... (ESC zum Abbrechen)")
        
        # Aufnahme-Button deaktivieren
        self.btn_record_hotkey.setEnabled(False)
        
        # Keyboard-Listener starten
        self.hotkey_listener = keyboard.Listener(
            on_press=self._on_hotkey_press,
            on_release=self._on_hotkey_release
        )
        self.hotkey_listener.start()
        
        # Mouse-Listener starten (für Gaming-Maus-Tasten)
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Wird aufgerufen, wenn eine Maustaste gedrückt/losgelassen wird"""
        if self.recording_field is None:
            return
        
        button_str = self._mouse_button_to_string(button)
        if not button_str:
            return
        
        if pressed:
            self.pressed_keys.add(button_str)
            current_combo = '+'.join(sorted(self.pressed_keys))
            self.last_hotkey = current_combo
            self.txt_hotkey.setText(current_combo)
        else:
            had_keys = len(self.pressed_keys) >= 1
            if button_str in self.pressed_keys:
                self.pressed_keys.discard(button_str)
            if len(self.pressed_keys) == 0 and had_keys:
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, self.finish_hotkey_recording)
    
    def _on_hotkey_press(self, key):
        """Wird aufgerufen, wenn eine Taste gedrückt wird"""
        if self.recording_field is None:
            return
        
        key_str = self._key_to_string(key)
        if key_str:
            self.pressed_keys.add(key_str)
            # Aktualisiere das Feld live mit der aktuellen Kombination
            current_combo = '+'.join(sorted(self.pressed_keys))
            self.last_hotkey = current_combo  # Speichere für später
            self.txt_hotkey.setText(current_combo)
    
    def _on_hotkey_release(self, key):
        """Wird aufgerufen, wenn eine Taste losgelassen wird"""
        if self.recording_field is None:
            return
        
        # ESC zum Abbrechen
        try:
            if key == keyboard.Key.esc:
                self.cancel_hotkey_recording()
                return
        except:
            pass
        
        # Prüfen ob Tasten gedrückt waren (mindestens 1)
        had_keys = len(self.pressed_keys) >= 1
        
        # Taste aus Set entfernen
        key_str = self._key_to_string(key)
        if key_str and key_str in self.pressed_keys:
            self.pressed_keys.discard(key_str)
        
        # Wenn alle Tasten losgelassen wurden UND es waren Tasten gedrückt
        if len(self.pressed_keys) == 0 and had_keys:
            # Kurze Verzögerung, damit alle Release-Events verarbeitet werden
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.finish_hotkey_recording)
    
    def finish_hotkey_recording(self):
        """Beendet die Hotkey-Aufnahme und speichert die Kombination"""
        if self.recording_field is None:
            return
        
        # Listener stoppen
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        # Speichere den letzten aufgenommenen Hotkey
        self.txt_hotkey.setText(self.last_hotkey)
        self.txt_hotkey.setStyleSheet("")  # Zurück zu Standard-Style
        
        # Aufnahme-Status zurücksetzen
        self.recording_field = None
        self.pressed_keys.clear()
        self.last_hotkey = ""
        
        # Button wieder aktivieren
        self.btn_record_hotkey.setEnabled(True)
    
    def cancel_hotkey_recording(self):
        """Bricht die Hotkey-Aufnahme ab"""
        if self.recording_field is None:
            return
        
        # Listener stoppen
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        # Feld leeren und Style zurücksetzen
        self.txt_hotkey.setText("")
        self.txt_hotkey.setStyleSheet("")  # Zurück zu Standard-Style
        
        # Aufnahme-Status zurücksetzen
        self.recording_field = None
        self.pressed_keys.clear()
        
        # Button wieder aktivieren
        self.btn_record_hotkey.setEnabled(True)
    
    def _key_to_string(self, key) -> str:
        """Konvertiert ein Key-Objekt zu einem String"""
        try:
            # Normale Zeichen
            return key.char.lower()
        except AttributeError:
            # Spezielle Tasten
            key_name = str(key).replace('Key.', '')
            return key_name.lower()
    
    def _mouse_button_to_string(self, button) -> str:
        """Konvertiert ein Mouse-Button-Objekt zu einem String"""
        try:
            button_map = {
                mouse.Button.left: 'mouse_left',
                mouse.Button.right: 'mouse_right',
                mouse.Button.middle: 'mouse_middle',
                mouse.Button.x1: 'mouse_x1',
                mouse.Button.x2: 'mouse_x2',
            }
            return button_map.get(button, None)
        except:
            button_str = str(button).lower()
            if 'button' in button_str:
                return f'mouse_{button_str}'
            return None
    
    def closeEvent(self, event):
        """Wird beim Schließen des Dialogs aufgerufen"""
        # Hotkey-Listener stoppen, falls noch aktiv
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        event.accept()
    
    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        return {
            'profile_id': self.combo_profile.currentData(),
            'name': self.txt_name.text(),
            'description': self.txt_description.toPlainText(),
            'hotkey': self.txt_hotkey.text(),
            'loop_count': self.spin_loops.value(),
            'loop_infinite': self.chk_infinite.isChecked(),
            'delay_between_loops': self.spin_delay.value(),
            'window_filter': self.txt_window_filter.text()
        }

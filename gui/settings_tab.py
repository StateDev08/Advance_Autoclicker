"""
Einstellungs Tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QLineEdit, QCheckBox, QSpinBox,
                              QDoubleSpinBox, QGroupBox, QComboBox, QMessageBox,
                              QFormLayout, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from database import DatabaseManager
from core import HotkeyManager, WindowDetector
from pynput import keyboard, mouse
import json
from pathlib import Path


class SettingsTab(QWidget):
    """Tab für Einstellungen"""

    # Wird aus einem anderen Thread (HotkeyManager) emit-tet, um die UI zu aktualisieren
    hotkey_debug_signal = pyqtSignal(str)

    def __init__(self, db: DatabaseManager, hotkey_manager: HotkeyManager):
        super().__init__()
        self.db = db
        self.hotkey_manager = hotkey_manager
        self.hotkey_listener = None
        self.mouse_listener = None
        self.recording_field = None  # Speichert, welches Feld gerade aufnimmt
        self.pressed_keys = set()
        self.last_hotkey = ""  # Speichert den zuletzt aufgenommenen Hotkey

        # Label für Hotkey-Debug
        self.lbl_hotkey_debug = None

        # Signal mit Slot verbinden
        self.hotkey_debug_signal.connect(self._set_hotkey_debug_label)

        self.init_ui()
        self.load_settings()
    
    def closeEvent(self, event):
        """Wird beim Schließen des Widgets aufgerufen"""
        # Hotkey-Listener stoppen, falls noch aktiv
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        event.accept()
    
    def init_ui(self):
        """Initialisiert die UI"""
        layout = QVBoxLayout(self)
        
        # Allgemeine Einstellungen
        general_group = QGroupBox("Allgemeine Einstellungen")
        general_layout = QFormLayout()
        
        self.chk_autostart = QCheckBox("Beim Windows-Start automatisch starten")
        general_layout.addRow("Autostart:", self.chk_autostart)
        
        self.chk_minimize_tray = QCheckBox("In System-Tray minimieren")
        general_layout.addRow("System-Tray:", self.chk_minimize_tray)
        
        self.chk_show_notifications = QCheckBox("Benachrichtigungen anzeigen")
        self.chk_show_notifications.setChecked(True)
        general_layout.addRow("Benachrichtigungen:", self.chk_show_notifications)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Aufnahme-Einstellungen
        recording_group = QGroupBox("Aufnahme-Einstellungen")
        recording_layout = QFormLayout()
        
        self.spin_mouse_threshold = QSpinBox()
        self.spin_mouse_threshold.setMinimum(10)
        self.spin_mouse_threshold.setMaximum(500)
        self.spin_mouse_threshold.setValue(50)
        self.spin_mouse_threshold.setSuffix(" ms")
        recording_layout.addRow("Mausbewegung-Schwelle:", self.spin_mouse_threshold)
        
        self.chk_record_mouse_moves = QCheckBox("Mausbewegungen aufzeichnen")
        self.chk_record_mouse_moves.setChecked(True)
        recording_layout.addRow("Mausbewegungen:", self.chk_record_mouse_moves)
        
        self.chk_record_keyboard = QCheckBox("Tastatur aufzeichnen")
        self.chk_record_keyboard.setChecked(True)
        recording_layout.addRow("Tastatur:", self.chk_record_keyboard)
        
        recording_group.setLayout(recording_layout)
        layout.addWidget(recording_group)
        
        # Wiedergabe-Einstellungen
        playback_group = QGroupBox("Wiedergabe-Einstellungen")
        playback_layout = QFormLayout()
        
        self.spin_default_speed = QDoubleSpinBox()
        self.spin_default_speed.setMinimum(0.1)
        self.spin_default_speed.setMaximum(10.0)
        self.spin_default_speed.setSingleStep(0.1)
        self.spin_default_speed.setValue(1.0)
        self.spin_default_speed.setSuffix("x")
        playback_layout.addRow("Standard-Geschwindigkeit:", self.spin_default_speed)
        
        self.chk_stop_on_error = QCheckBox("Bei Fehler stoppen")
        self.chk_stop_on_error.setChecked(True)
        playback_layout.addRow("Fehlerbehandlung:", self.chk_stop_on_error)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        # Hotkey-Einstellungen
        hotkey_group = QGroupBox("Globale Hotkey-Einstellungen")
        hotkey_layout = QFormLayout()
        
        hotkey_info = QLabel(
            "<small>Format: <b>ctrl+shift+taste</b>, <b>alt+taste</b>, <b>f1</b> oder <b>mouse_x1</b><br>"
            "Beispiele: ctrl+shift+r, alt+f9, f1, mouse_x1 (Gaming-Maus)<br>"
            "<b>Tipp:</b> Nutzen Sie den '🎙️ Aufnahme'-Button um Tasten/Maustasten zu erfassen!</small>"
        )
        hotkey_info.setWordWrap(True)
        hotkey_layout.addRow("", hotkey_info)
        
        # Aufnahme starten Hotkey
        record_start_layout = QHBoxLayout()
        self.txt_hotkey_record_start = QLineEdit()
        self.txt_hotkey_record_start.setPlaceholderText("z.B. ctrl+shift+r")
        record_start_layout.addWidget(self.txt_hotkey_record_start)
        self.btn_record_start = QPushButton("🎙️ Aufnahme")
        self.btn_record_start.setMaximumWidth(100)
        self.btn_record_start.clicked.connect(lambda: self.start_hotkey_recording(self.txt_hotkey_record_start))
        record_start_layout.addWidget(self.btn_record_start)
        hotkey_layout.addRow("🎙️ Aufnahme starten:", record_start_layout)
        
        # Wiedergabe starten Hotkey
        play_start_layout = QHBoxLayout()
        self.txt_hotkey_play_start = QLineEdit()
        self.txt_hotkey_play_start.setPlaceholderText("z.B. f8 oder ctrl+shift+p")
        play_start_layout.addWidget(self.txt_hotkey_play_start)
        self.btn_play_start = QPushButton("🎙️ Aufnahme")
        self.btn_play_start.setMaximumWidth(100)
        self.btn_play_start.clicked.connect(lambda: self.start_hotkey_recording(self.txt_hotkey_play_start))
        play_start_layout.addWidget(self.btn_play_start)
        hotkey_layout.addRow("▶️ Wiedergabe starten:", play_start_layout)
        
        # Aufnahme stoppen Hotkey
        record_stop_layout = QHBoxLayout()
        self.txt_hotkey_record_stop = QLineEdit()
        self.txt_hotkey_record_stop.setPlaceholderText("z.B. ctrl+shift+s")
        record_stop_layout.addWidget(self.txt_hotkey_record_stop)
        self.btn_record_stop = QPushButton("🎙️ Aufnahme")
        self.btn_record_stop.setMaximumWidth(100)
        self.btn_record_stop.clicked.connect(lambda: self.start_hotkey_recording(self.txt_hotkey_record_stop))
        record_stop_layout.addWidget(self.btn_record_stop)
        hotkey_layout.addRow("⏹️ Aufnahme stoppen:", record_stop_layout)
        
        # Wiedergabe stoppen Hotkey
        play_stop_layout = QHBoxLayout()
        self.txt_hotkey_play_stop = QLineEdit()
        self.txt_hotkey_play_stop.setPlaceholderText("z.B. ctrl+shift+x")
        play_stop_layout.addWidget(self.txt_hotkey_play_stop)
        self.btn_play_stop = QPushButton("🎙️ Aufnahme")
        self.btn_play_stop.setMaximumWidth(100)
        self.btn_play_stop.clicked.connect(lambda: self.start_hotkey_recording(self.txt_hotkey_play_stop))
        play_stop_layout.addWidget(self.btn_play_stop)
        hotkey_layout.addRow("⏹️ Wiedergabe stoppen:", play_stop_layout)
        
        # Notfall-Stop Hotkey
        emergency_layout = QHBoxLayout()
        self.txt_emergency_stop = QLineEdit()
        self.txt_emergency_stop.setPlaceholderText("z.B. ctrl+shift+esc")
        emergency_layout.addWidget(self.txt_emergency_stop)
        self.btn_emergency = QPushButton("🎙️ Aufnahme")
        self.btn_emergency.setMaximumWidth(100)
        self.btn_emergency.clicked.connect(lambda: self.start_hotkey_recording(self.txt_emergency_stop))
        emergency_layout.addWidget(self.btn_emergency)
        hotkey_layout.addRow("⚠️ Notfall-Stop (Alles):", emergency_layout)
        
        # Overlay-Toggle Hotkey
        overlay_layout = QHBoxLayout()
        self.txt_overlay_toggle = QLineEdit()
        self.txt_overlay_toggle.setPlaceholderText("z.B. ctrl+shift+o")
        overlay_layout.addWidget(self.txt_overlay_toggle)
        self.btn_overlay_toggle = QPushButton("🎙️ Aufnahme")
        self.btn_overlay_toggle.setMaximumWidth(100)
        self.btn_overlay_toggle.clicked.connect(lambda: self.start_hotkey_recording(self.txt_overlay_toggle))
        overlay_layout.addWidget(self.btn_overlay_toggle)
        hotkey_layout.addRow("🎮 Gaming-Overlay ein/aus:", overlay_layout)
        
        self.chk_global_hotkeys = QCheckBox("Globale Hotkeys aktivieren")
        self.chk_global_hotkeys.setChecked(True)
        hotkey_layout.addRow("", self.chk_global_hotkeys)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)

        # Debug-Bereich für Hotkeys
        debug_group = QGroupBox("Hotkey-Debug")
        debug_layout = QFormLayout()

        self.chk_hotkey_debug = QCheckBox("Hotkey-Debug aktivieren")
        self.chk_hotkey_debug.stateChanged.connect(self.on_hotkey_debug_toggled)
        debug_layout.addRow(self.chk_hotkey_debug)

        self.lbl_hotkey_debug = QLabel("<small>Letzte Kombination: -</small>")
        self.lbl_hotkey_debug.setWordWrap(True)
        debug_layout.addRow("", self.lbl_hotkey_debug)

        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        # Datenverwaltung
        data_group = QGroupBox("Datenverwaltung")
        data_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        
        self.btn_export = QPushButton("📤 Exportieren")
        self.btn_export.clicked.connect(self.export_data)
        btn_layout.addWidget(self.btn_export)
        
        self.btn_import = QPushButton("📥 Importieren")
        self.btn_import.clicked.connect(self.import_data)
        btn_layout.addWidget(self.btn_import)
        
        self.btn_backup = QPushButton("💾 Backup erstellen")
        self.btn_backup.clicked.connect(self.create_backup)
        btn_layout.addWidget(self.btn_backup)
        
        data_layout.addLayout(btn_layout)
        
        # Diagnose-Button für Fenster-Erkennung
        diagnose_layout =  QHBoxLayout()
        self.btn_test_window = QPushButton("🧪 Fenster-Erkennung testen")
        self.btn_test_window.clicked.connect(self.test_window_detection)
        diagnose_layout.addWidget(self.btn_test_window)
        diagnose_layout.addStretch()
        data_layout.addLayout(diagnose_layout)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Speichern-Button
        layout.addStretch()
        
        btn_save_layout = QHBoxLayout()
        btn_save_layout.addStretch()
        
        self.btn_save = QPushButton("💾 Einstellungen speichern")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_save.setStyleSheet("QPushButton { font-size: 12pt; padding: 10px; }")
        btn_save_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_save_layout)
    
    def load_settings(self):
        """Lädt gespeicherte Einstellungen"""
        settings = self.db.get_all_settings()
        
        # Allgemein
        self.chk_autostart.setChecked(settings.get('autostart', 'false') == 'true')
        self.chk_minimize_tray.setChecked(settings.get('minimize_tray', 'false') == 'true')
        self.chk_show_notifications.setChecked(settings.get('show_notifications', 'true') == 'true')
        
        # Aufnahme
        self.spin_mouse_threshold.setValue(int(settings.get('mouse_threshold', '50')))
        self.chk_record_mouse_moves.setChecked(settings.get('record_mouse_moves', 'true') == 'true')
        self.chk_record_keyboard.setChecked(settings.get('record_keyboard', 'true') == 'true')
        
        # Wiedergabe
        self.spin_default_speed.setValue(float(settings.get('default_speed', '1.0')))
        self.chk_stop_on_error.setChecked(settings.get('stop_on_error', 'true') == 'true')
        
        # Hotkeys
        self.txt_hotkey_record_start.setText(settings.get('hotkey_record_start', ''))
        self.txt_hotkey_play_start.setText(settings.get('hotkey_play_start', ''))
        self.txt_hotkey_record_stop.setText(settings.get('hotkey_record_stop', ''))
        self.txt_hotkey_play_stop.setText(settings.get('hotkey_play_stop', ''))
        self.txt_emergency_stop.setText(settings.get('emergency_stop_hotkey', ''))
        self.txt_overlay_toggle.setText(settings.get('overlay_toggle_hotkey', 'ctrl+shift+o'))
        self.chk_global_hotkeys.setChecked(settings.get('global_hotkeys', 'true') == 'true')
    
    def save_settings(self):
        """Speichert Einstellungen"""
        # Allgemein
        self.db.set_setting('autostart', 'true' if self.chk_autostart.isChecked() else 'false')
        self.db.set_setting('minimize_tray', 'true' if self.chk_minimize_tray.isChecked() else 'false')
        self.db.set_setting('show_notifications', 'true' if self.chk_show_notifications.isChecked() else 'false')
        
        # Aufnahme
        self.db.set_setting('mouse_threshold', str(self.spin_mouse_threshold.value()))
        self.db.set_setting('record_mouse_moves', 'true' if self.chk_record_mouse_moves.isChecked() else 'false')
        self.db.set_setting('record_keyboard', 'true' if self.chk_record_keyboard.isChecked() else 'false')
        
        # Wiedergabe
        self.db.set_setting('default_speed', str(self.spin_default_speed.value()))
        self.db.set_setting('stop_on_error', 'true' if self.chk_stop_on_error.isChecked() else 'false')
        
        # Hotkeys
        self.db.set_setting('hotkey_record_start', self.txt_hotkey_record_start.text())
        self.db.set_setting('hotkey_play_start', self.txt_hotkey_play_start.text())
        self.db.set_setting('hotkey_record_stop', self.txt_hotkey_record_stop.text())
        self.db.set_setting('hotkey_play_stop', self.txt_hotkey_play_stop.text())
        self.db.set_setting('emergency_stop_hotkey', self.txt_emergency_stop.text())
        self.db.set_setting('overlay_toggle_hotkey', self.txt_overlay_toggle.text())
        self.db.set_setting('global_hotkeys', 'true' if self.chk_global_hotkeys.isChecked() else 'false')
        
        QMessageBox.information(self, "Erfolg", "Einstellungen gespeichert!\n\nBitte starten Sie die Anwendung neu, damit die Hotkeys aktiv werden.")

    # --- Hotkey-Debug ---

    def on_hotkey_debug_toggled(self, state: int):
        """Aktiviert/Deaktiviert das Live-Hotkey-Debugging."""
        enabled = state == Qt.CheckState.Checked.value

        if enabled:
            # Debug-Callback im HotkeyManager registrieren
            if self.hotkey_manager:
                self.hotkey_manager.set_debug_callback(self._debug_callback)
        else:
            # Debug-Callback entfernen
            if self.hotkey_manager:
                self.hotkey_manager.set_debug_callback(None)
            self._set_hotkey_debug_label("")

    def _debug_callback(self, combo: str):
        """Wird aus dem HotkeyManager-Thread aufgerufen -> nur Signal emittieren."""
        self.hotkey_debug_signal.emit(combo)

    def _set_hotkey_debug_label(self, combo: str):
        """Aktualisiert das Debug-Label im UI-Thread."""
        text = combo or "-"
        if self.lbl_hotkey_debug is not None:
            self.lbl_hotkey_debug.setText(f"<small>Letzte Kombination: <b>{text}</b></small>")

    def start_hotkey_recording(self, target_field: QLineEdit):
        """Startet die Aufnahme einer Tastenkombination"""
        if self.recording_field is not None:
            # Es läuft bereits eine Aufnahme
            QMessageBox.warning(self, "Hinweis", "Es läuft bereits eine Hotkey-Aufnahme!")
            return
        
        self.recording_field = target_field
        self.pressed_keys.clear()
        
        # Feld visuell markieren
        target_field.setStyleSheet("QLineEdit { background-color: #ffffcc; border: 2px solid #ff6600; }")
        target_field.setText("Drücken Sie die gewünschte Tastenkombination... (ESC zum Abbrechen)")
        
        # Alle Aufnahme-Buttons deaktivieren
        self.btn_record_start.setEnabled(False)
        self.btn_play_start.setEnabled(False)
        self.btn_record_stop.setEnabled(False)
        self.btn_play_stop.setEnabled(False)
        self.btn_emergency.setEnabled(False)
        self.btn_overlay_toggle.setEnabled(False)
        
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
            # Taste gedrückt
            self.pressed_keys.add(button_str)
            # Aktualisiere das Feld live
            current_combo = '+'.join(sorted(self.pressed_keys))
            self.last_hotkey = current_combo
            self.recording_field.setText(current_combo)
        else:
            # Taste losgelassen
            had_keys = len(self.pressed_keys) >= 1
            
            if button_str in self.pressed_keys:
                self.pressed_keys.discard(button_str)
            
            # Wenn alle Tasten losgelassen wurden
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
            self.recording_field.setText(current_combo)
    
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
        self.recording_field.setText(self.last_hotkey)
        self.recording_field.setStyleSheet("")  # Zurück zu Standard-Style
        
        # Aufnahme-Status zurücksetzen
        self.recording_field = None
        self.pressed_keys.clear()
        self.last_hotkey = ""
        
        # Buttons wieder aktivieren
        self.btn_record_start.setEnabled(True)
        self.btn_play_start.setEnabled(True)
        self.btn_record_stop.setEnabled(True)
        self.btn_play_stop.setEnabled(True)
        self.btn_emergency.setEnabled(True)
        self.btn_overlay_toggle.setEnabled(True)
        self.btn_overlay_toggle.setEnabled(True)

        self.btn_emergency.setEnabled(True)
    
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
        self.recording_field.setText("")
        self.recording_field.setStyleSheet("")  # Zurück zu Standard-Style
        
        # Aufnahme-Status zurücksetzen
        self.recording_field = None
        self.pressed_keys.clear()
        
        # Buttons wieder aktivieren
        self.btn_record_start.setEnabled(True)
        self.btn_record_stop.setEnabled(True)
        self.btn_play_stop.setEnabled(True)
        self.btn_emergency.setEnabled(True)
    
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
                mouse.Button.x1: 'mouse_x1',  # Gaming-Maus Taste 4
                mouse.Button.x2: 'mouse_x2',  # Gaming-Maus Taste 5
            }
            return button_map.get(button, None)
        except:
            # Für unbekannte Maustasten
            button_str = str(button).lower()
            if 'button' in button_str:
                return f'mouse_{button_str}'
            return None
    
    def export_data(self):
        """Exportiert Profile und Makros"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Daten exportieren",
            "autoclicker_export.json",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            data = {
                'profiles': self.db.get_profiles(),
                'macros': self.db.get_macros(),
                'settings': self.db.get_all_settings()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Erfolg", "Daten erfolgreich exportiert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Exportieren: {str(e)}")
    
    def import_data(self):
        """Importiert Profile und Makros"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Daten importieren",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        reply = QMessageBox.question(
            self,
            "Daten importieren",
            "Möchten Sie die Daten wirklich importieren?\n"
            "Bestehende Daten mit gleichen Namen werden überschrieben!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Profile importieren
            for profile in data.get('profiles', []):
                try:
                    self.db.create_profile(profile['name'], profile.get('description', ''))
                except:
                    pass  # Profil existiert bereits
            
            # Makros importieren
            for macro in data.get('macros', []):
                try:
                    # Profil-ID ermitteln
                    profiles = self.db.get_profiles()
                    profile_id = None
                    for p in profiles:
                        if p['id'] == macro['profile_id']:
                            profile_id = p['id']
                            break
                    
                    if profile_id:
                        self.db.create_macro(
                            profile_id,
                            macro['name'],
                            macro['actions'],
                            macro.get('description', ''),
                            macro.get('hotkey', ''),
                            macro.get('loop_count', 1),
                            macro.get('loop_infinite', False),
                            macro.get('delay_between_loops', 0.0),
                            macro.get('window_filter', '')
                        )
                except:
                    pass  # Makro konnte nicht importiert werden
            
            QMessageBox.information(self, "Erfolg", "Daten erfolgreich importiert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Importieren: {str(e)}")
    
    def create_backup(self):
        """Erstellt ein Backup der Datenbank"""
        from datetime import datetime
        
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"autoclicker_backup_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db.db_path, backup_path)
            
            QMessageBox.information(
                self,
                "Erfolg",
                f"Backup erstellt!\n\nPfad: {backup_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen des Backups: {str(e)}")

    def test_window_detection(self):
        """Zeigt Informationen zum aktuell aktiven Fenster an (Diagnose)."""
        try:
            info = WindowDetector.get_active_window_info()
            title = info.get("pretend_title", None) or info.get("title", "")
            cls = info.get("class", "")
            proc = info.get("process", "")

            if not any([title, cls, proc]):
                msg = (
                    "Es konnten keine Informationen zum aktiven Fenster gelesen werden.\n\n"
                    "Mögliche Ursachen:\n"
                    "- Das aktive Fenster hat keinen Titel (z.B. manche Vollbild-Spiele).\n"
                    "- Das Spiel/Programm blockiert den Zugriff auf Fenster-/Prozessinfos.\n"
                    "- Die Anwendung hat nicht genügend Rechte (ggf. als Administrator starten)."
                )
            else:
                msg = (
                    f"<b>Titel:</b> {title or '-'}<br>"
                    f"<b>Fensterklasse:</b> {cls or '-'}<br>"
                    f"<b>Prozess:</b> {proc or '-'}<br>"
                )

            QMessageBox.information(self, "Fenster-Erkennung", msg)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler bei der Fenster-Erkennung",
                f"Beim Abfragen des aktiven Fensters ist ein Fehler aufgetreten:\n{e}"
            )

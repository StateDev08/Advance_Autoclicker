"""
Makro-Verwaltungs Tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QListWidget, QListWidgetItem, QLabel, QLineEdit,
                              QTextEdit, QDialog, QDialogButtonBox, QMessageBox,
                              QGroupBox, QSpinBox, QCheckBox, QDoubleSpinBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QProgressBar, QComboBox, QApplication)
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path
import json
from database import DatabaseManager
from core import HotkeyManager, WindowDetector, MacroPlayer
from core.webhook_notify import notify_macro_finished
from gui.action_editor import MacroEditorWidget
from pynput import keyboard, mouse


def _load_game_filters():
    """Lädt vordefinierte Fenster-Filter aus data/game_filters.json."""
    path = Path(__file__).resolve().parent.parent / "data" / "game_filters.json"
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

class MacroTab(QWidget):
    """Tab für Makro-Verwaltung"""
    
    playback_started = pyqtSignal(str)  # macro_name
    playback_stopped = pyqtSignal()
    playback_progress = pyqtSignal(float, int, int)  # progress_percent, loop, action
    macro_list_changed = pyqtSignal()  # wenn Makro-Liste sich geändert hat (für Hotkey-Aktualisierung)

    def __init__(self, db: DatabaseManager, hotkey_manager: HotkeyManager, 
                 window_detector: WindowDetector):
        super().__init__()
        self.db = db
        self.hotkey_manager = hotkey_manager
        self.window_detector = window_detector
        self.player = MacroPlayer()
        
        self.current_profile_id = None
        self.current_macro_id = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI"""
        layout = QHBoxLayout(self)
        
        # Linke Seite - Makro-Liste
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("<b>Makros:</b>"))
        
        self.macro_list = QListWidget()
        self.macro_list.itemClicked.connect(self.on_macro_clicked)
        left_layout.addWidget(self.macro_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_new = QPushButton("➕ Neu")
        self.btn_new.clicked.connect(self.create_macro)
        self.btn_new.setEnabled(False)
        button_layout.addWidget(self.btn_new)
        
        self.btn_edit = QPushButton("✏️ Bearbeiten")
        self.btn_edit.clicked.connect(self.edit_macro)
        self.btn_edit.setEnabled(False)
        button_layout.addWidget(self.btn_edit)
        
        self.btn_edit_actions = QPushButton("🔧 Aktionen")
        self.btn_edit_actions.clicked.connect(self.edit_actions)
        self.btn_edit_actions.setEnabled(False)
        self.btn_edit_actions.setToolTip("Erweiteter Action-Editor mit Drag & Drop")
        button_layout.addWidget(self.btn_edit_actions)
        
        self.btn_delete = QPushButton("🗑️ Löschen")
        self.btn_delete.clicked.connect(self.delete_macro)
        self.btn_delete.setEnabled(False)
        button_layout.addWidget(self.btn_delete)
        
        left_layout.addLayout(button_layout)
        
        # Rechte Seite - Makro-Details und Steuerung
        right_layout = QVBoxLayout()
        
        # Details
        details_group = QGroupBox("Makro-Details")
        details_layout = QVBoxLayout()
        
        self.lbl_name = QLabel("<i>Kein Makro ausgewählt</i>")
        self.lbl_name.setWordWrap(True)
        self.lbl_name.setStyleSheet("font-size: 14pt; color: palette(accent); font-weight: bold;")
        details_layout.addWidget(self.lbl_name)
        
        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("color: palette(text); font-size: 10pt;")
        details_layout.addWidget(self.lbl_info)
        
        details_group.setLayout(details_layout)
        right_layout.addWidget(details_group)
        
        # Steuerung
        control_group = QGroupBox("Wiedergabe-Steuerung")
        control_layout = QVBoxLayout()
        
        # Endlos-Option
        endlos_layout = QHBoxLayout()
        self.chk_play_infinite = QCheckBox("🔁 Endlos-Schleife (bis manuell gestoppt)")
        self.chk_play_infinite.setStyleSheet("QCheckBox { font-weight: bold; }")
        endlos_layout.addWidget(self.chk_play_infinite)
        endlos_layout.addStretch()
        control_layout.addLayout(endlos_layout)
        
        btn_control_layout = QHBoxLayout()
        
        self.btn_play = QPushButton("▶️ Abspielen")
        self.btn_play.setObjectName("btn_play")
        self.btn_play.clicked.connect(self.play_macro)
        self.btn_play.setEnabled(False)
        btn_control_layout.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton("⏹️ Stoppen")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.clicked.connect(self.stop_macro)
        self.btn_stop.setEnabled(False)
        btn_control_layout.addWidget(self.btn_stop)
        
        control_layout.addLayout(btn_control_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        self.lbl_progress = QLabel("")
        self.lbl_progress.setVisible(False)
        control_layout.addWidget(self.lbl_progress)
        
        control_group.setLayout(control_layout)
        right_layout.addWidget(control_group)
        
        right_layout.addStretch()
        
        # Layouts zusammenfügen
        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 2)
    
    def load_profile(self, profile_id: int):
        """Lädt Makros für ein Profil"""
        self.current_profile_id = profile_id
        self.btn_new.setEnabled(True)
        self.refresh_macros()
    
    def refresh_macros(self):
        """Aktualisiert die Makro-Liste"""
        self.macro_list.clear()
        
        if not self.current_profile_id:
            return
        
        macros = self.db.get_macros(self.current_profile_id)
        
        for macro in macros:
            item = QListWidgetItem(f"{macro['name']}")
            item.setData(Qt.ItemDataRole.UserRole, macro['id'])
            self.macro_list.addItem(item)
        self.macro_list_changed.emit()
    
    def on_macro_clicked(self, item: QListWidgetItem):
        """Callback wenn ein Makro angeklickt wurde"""
        macro_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_macro_id = macro_id
        
        self.btn_edit.setEnabled(True)
        self.btn_edit_actions.setEnabled(True)
        self.btn_delete.setEnabled(True)
        self.btn_play.setEnabled(True)
        
        # Details anzeigen
        macro = self.db.get_macro(macro_id)
        if macro:
            self.lbl_name.setText(f"<h2>{macro['name']}</h2>")
            
            info_parts = []
            if macro['description']:
                info_parts.append(f"<b>Beschreibung:</b> {macro['description']}")
            
            info_parts.append(f"<b>Aktionen:</b> {len(macro['actions'])}")
            
            if macro['hotkey']:
                info_parts.append(f"<b>Hotkey:</b> {macro['hotkey']}")
            
            if macro['loop_infinite']:
                info_parts.append(f"<b>Wiederholung:</b> Unendlich")
            else:
                info_parts.append(f"<b>Wiederholung:</b> {macro['loop_count']}x")
            
            if macro['window_filter']:
                info_parts.append(f"<b>Fenster-Filter:</b> {macro['window_filter']}")
            
            self.lbl_info.setText("<br>".join(info_parts))
    
    def create_macro(self):
        """Erstellt ein neues Makro"""
        if not self.current_profile_id:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie zuerst ein Profil aus!")
            return
        
        dialog = MacroDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.create_macro(
                    self.current_profile_id,
                    data['name'],
                    data['actions'],
                    data['description'],
                    data['hotkey'],
                    data['loop_count'],
                    data['loop_infinite'],
                    data['delay_between_loops'],
                    data['window_filter']
                )
                self.refresh_macros()
                QMessageBox.information(self, "Erfolg", "Makro erstellt!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen: {str(e)}")
    
    def edit_macro(self):
        """Bearbeitet das ausgewählte Makro"""
        if not self.current_macro_id:
            return
        
        macro = self.db.get_macro(self.current_macro_id)
        if not macro:
            return
        
        dialog = MacroDialog(self, macro)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.update_macro(
                    self.current_macro_id,
                    data['name'],
                    data['actions'],
                    data['description'],
                    data['hotkey'],
                    data['loop_count'],
                    data['loop_infinite'],
                    data['delay_between_loops'],
                    data['window_filter']
                )
                self.refresh_macros()
                QMessageBox.information(self, "Erfolg", "Makro aktualisiert!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren: {str(e)}")
    
    def delete_macro(self):
        """Löscht das ausgewählte Makro"""
        if not self.current_macro_id:
            return
        
        macro = self.db.get_macro(self.current_macro_id)
        if not macro:
            return
        
        reply = QMessageBox.question(
            self,
            "Makro löschen",
            f"Möchten Sie das Makro '{macro['name']}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_macro(self.current_macro_id)
                self.current_macro_id = None
                self.refresh_macros()
                self.lbl_name.setText("<i>Kein Makro ausgewählt</i>")
                self.lbl_info.setText("")
                self.btn_edit.setEnabled(False)
                self.btn_edit_actions.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen: {str(e)}")
    
    def edit_actions(self):
        """Öffnet den erweiterten Action-Editor"""
        if not self.current_macro_id:
            return
        
        macro = self.db.get_macro(self.current_macro_id)
        if not macro:
            return
        
        # Dialog erstellen
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Aktionen bearbeiten - {macro['name']}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Editor Widget
        editor = MacroEditorWidget()
        editor.set_actions(macro['actions'])
        layout.addWidget(editor)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("💾 Speichern")
        btn_save.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # Dialog anzeigen
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Aktualisierte Aktionen speichern
            new_actions = editor.get_actions()
            
            try:
                self.db.update_macro(
                    self.current_macro_id,
                    macro['name'],
                    new_actions,
                    macro['description'],
                    macro['hotkey'],
                    macro['loop_count'],
                    macro['loop_infinite'],
                    macro['delay_between_loops'],
                    macro['window_filter']
                )
                self.refresh_macros()
                QMessageBox.information(self, "Erfolg", "Aktionen aktualisiert!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}")
                self.btn_delete.setEnabled(False)
                self.btn_play.setEnabled(False)
                QMessageBox.information(self, "Erfolg", "Makro gelöscht!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen: {str(e)}")
    
    def play_macro_by_id(self, macro_id: int, skip_window_check: bool = False):
        """Spielt ein Makro per ID ab (z. B. für Tray, Scheduler, API)."""
        macro = self.db.get_macro(macro_id)
        if not macro:
            return
        self.current_macro_id = macro_id
        self.btn_edit.setEnabled(True)
        self.btn_edit_actions.setEnabled(True)
        self.btn_delete.setEnabled(True)
        self.btn_play.setEnabled(True)
        if not skip_window_check and macro.get("window_filter"):
            if not self.window_detector.matches_filter(macro["window_filter"]):
                return  # Stille Ablehnung für API/Tray
        self._run_macro(macro)

    def _run_macro(self, macro: dict):
        """Führt die Wiedergabe für ein Makro-Dict aus (von play_macro und play_macro_by_id)."""
        self._last_played_macro_id = macro["id"]
        self._last_played_macro_name = macro["name"]
        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.lbl_progress.setVisible(True)
        is_infinite = self.chk_play_infinite.isChecked() or macro["loop_infinite"]
        self.playback_started.emit(macro["name"])
        # Anti-Erkennung aus Einstellungen
        self.player.humanize_click_offset = self.db.get_setting("humanize_click_offset", "false") == "true"
        if self.db.get_setting("humanize_delay_enabled", "false") == "true":
            min_ms = int(self.db.get_setting("humanize_delay_min_ms", "0"))
            max_ms = int(self.db.get_setting("humanize_delay_max_ms", "150"))
            self.player.humanize_delay_before_action = (min_ms / 1000.0, max_ms / 1000.0)
        else:
            self.player.humanize_delay_before_action = None
        speed_str = self.db.get_setting("default_speed", "1.0")
        try:
            speed = float(speed_str)
        except Exception:
            speed = 1.0
        self.player.play(
            macro["actions"],
            macro["loop_count"],
            is_infinite,
            macro["delay_between_loops"],
            speed,
            on_progress=self.on_playback_progress,
            on_complete=self.on_playback_complete,
        )

    def play_macro(self):
        """Spielt das ausgewählte Makro ab"""
        if not self.current_macro_id:
            return
        
        macro = self.db.get_macro(self.current_macro_id)
        if not macro:
            return
        
        # Window-Filter prüfen
        if macro['window_filter']:
            current_window = self.window_detector.get_active_window_info()
            if not self.window_detector.matches_filter(macro['window_filter']):
                reply = QMessageBox.warning(
                    self,
                    "⚠️ Fenster-Filter aktiv",
                    f"Das Makro ist für ein anderes Fenster konfiguriert!\n\n"
                    f"Erforderlich: <b>{macro['window_filter']}</b>\n"
                    f"Aktuell: <b>{current_window['title']}</b> ({current_window['process']})\n\n"
                    f"Möchten Sie das Makro trotzdem ausführen?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        self._run_macro(macro)
    
    def stop_macro(self):
        """Stoppt die Makro-Wiedergabe"""
        if getattr(self, "current_macro_id", None) is not None and self.db.get_setting("outgoing_webhook_enabled", "false") == "true":
            url = self.db.get_setting("outgoing_webhook_url", "").strip()
            if url:
                macro = self.db.get_macro(self.current_macro_id)
                if macro:
                    notify_macro_finished(url, macro["id"], macro["name"], status="stopped")
        self.player.stop()
        self.playback_stopped.emit()
    
    def toggle_pause_resume(self):
        """Pausiert oder setzt die Wiedergabe fort (für globalen Pause/Resume-Hotkey)."""
        if self.player.is_playing:
            self.player.paused = not self.player.paused
    
    def on_playback_progress(self, progress: float, loop: int, action: int):
        """Callback für Wiedergabe-Fortschritt"""
        self.progress_bar.setValue(int(progress))
        self.lbl_progress.setText(f"Loop {loop}, Aktion {action}")
        self.playback_progress.emit(progress, loop, action)
    
    def on_playback_complete(self):
        """Callback wenn Wiedergabe abgeschlossen ist"""
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.lbl_progress.setVisible(False)
        self.playback_stopped.emit()
        if getattr(self, "_last_played_macro_id", None) is not None and self.db.get_setting("outgoing_webhook_enabled", "false") == "true":
            url = self.db.get_setting("outgoing_webhook_url", "").strip()
            if url:
                notify_macro_finished(url, self._last_played_macro_id, self._last_played_macro_name, status="completed")

class MacroDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten von Makros"""
    
    def __init__(self, parent=None, macro=None):
        super().__init__(parent)
        self.setWindowTitle("Neues Makro" if not macro else "Makro bearbeiten")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.hotkey_listener = None
        self.mouse_listener = None
        self.recording_field = None
        self.pressed_keys = set()
        self.last_hotkey = ""  # Speichert den zuletzt aufgenommenen Hotkey
        
        self.macro = macro or {
            'name': '',
            'description': '',
            'actions': [],
            'hotkey': '',
            'loop_count': 1,
            'loop_infinite': False,
            'delay_between_loops': 0.0,
            'window_filter': ''
        }
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI"""
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.txt_name = QLineEdit(self.macro['name'])
        layout.addWidget(self.txt_name)
        
        # Beschreibung
        layout.addWidget(QLabel("Beschreibung:"))
        self.txt_description = QTextEdit(self.macro['description'])
        self.txt_description.setMaximumHeight(60)
        layout.addWidget(self.txt_description)
        
        # Hotkey
        hotkey_layout = QHBoxLayout()
        hotkey_label = QLabel("Hotkey:")
        hotkey_layout.addWidget(hotkey_label, 1)
        
        hotkey_input_layout = QHBoxLayout()
        self.txt_hotkey = QLineEdit(self.macro['hotkey'])
        self.txt_hotkey.setPlaceholderText("z.B. ctrl+shift+a")
        hotkey_input_layout.addWidget(self.txt_hotkey)
        
        self.btn_record_hotkey = QPushButton("🎙️ Aufnahme")
        self.btn_record_hotkey.setMaximumWidth(100)
        self.btn_record_hotkey.clicked.connect(self.start_hotkey_recording)
        hotkey_input_layout.addWidget(self.btn_record_hotkey)
        
        hotkey_layout.addLayout(hotkey_input_layout, 3)
        layout.addLayout(hotkey_layout)
        
        # Wiederholung
        repeat_layout = QHBoxLayout()
        
        self.chk_infinite = QCheckBox("Unendlich wiederholen")
        self.chk_infinite.setChecked(self.macro['loop_infinite'])
        self.chk_infinite.stateChanged.connect(self.on_infinite_changed)
        repeat_layout.addWidget(self.chk_infinite)
        
        repeat_layout.addWidget(QLabel("Wiederholungen:"))
        self.spin_loops = QSpinBox()
        self.spin_loops.setMinimum(1)
        self.spin_loops.setMaximum(99999)
        self.spin_loops.setValue(self.macro['loop_count'])
        self.spin_loops.setEnabled(not self.macro['loop_infinite'])
        repeat_layout.addWidget(self.spin_loops)
        
        repeat_layout.addWidget(QLabel("Verzögerung (s):"))
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setMinimum(0)
        self.spin_delay.setMaximum(3600)
        self.spin_delay.setSingleStep(0.1)
        self.spin_delay.setValue(self.macro['delay_between_loops'])
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
        
        # Vordefinierte Fenster-Filter (Spiele/Apps), gruppiert nach Kategorie
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Vordefiniert:"))
        self.combo_window_preset = QComboBox()
        self.combo_window_preset.addItem("— Kein vordefinierter Filter —", "")
        filters_by_cat = {}
        for item in _load_game_filters():
            cat = item.get("category") or "Sonstige"
            filters_by_cat.setdefault(cat, []).append(item)
        for cat in sorted(filters_by_cat.keys()):
            for item in filters_by_cat[cat]:
                label = f"{cat} › {item['name']}" if cat != "Sonstige" else item["name"]
                self.combo_window_preset.addItem(label, item["filter"])
        self.combo_window_preset.currentIndexChanged.connect(self._on_window_preset_changed)
        preset_layout.addWidget(self.combo_window_preset, 1)
        layout.addLayout(preset_layout)
        
        self.txt_window_filter = QLineEdit(self.macro['window_filter'])
        self.txt_window_filter.setPlaceholderText("Leer = Alle Fenster | z.B. 'Notepad' oder 'chrome.exe'")
        self.txt_window_filter.textChanged.connect(self._on_window_filter_text_changed)
        layout.addWidget(self.txt_window_filter)
        idx = self.combo_window_preset.findData(self.macro.get('window_filter') or '')
        if idx >= 0:
            self.combo_window_preset.blockSignals(True)
            self.combo_window_preset.setCurrentIndex(idx)
            self.combo_window_preset.blockSignals(False)
        
        # Fenster-Info anzeigen
        from core import WindowDetector
        window_info = WindowDetector.get_active_window_info()
        info_text = f"<small>Aktuell: <b>{window_info['title']}</b> ({window_info['process']})</small>"
        self.lbl_current_window = QLabel(info_text)
        self.lbl_current_window.setWordWrap(True)
        layout.addWidget(self.lbl_current_window)
        
        # Aktionen-Tabelle
        layout.addWidget(QLabel(f"Aktionen ({len(self.macro['actions'])}):"))
        
        self.table_actions = QTableWidget()
        self.table_actions.setColumnCount(3)
        self.table_actions.setHorizontalHeaderLabels(["Typ", "Details", "Verzögerung (s)"])
        self.table_actions.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_actions.setMaximumHeight(150)
        
        self.load_actions()
        layout.addWidget(self.table_actions)
        
        # Info-Text
        info_label = QLabel(
            "<small><i>Hinweis: Verwenden Sie den Aufnahme-Tab um Aktionen aufzuzeichnen.</i></small>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_actions(self):
        """Lädt Aktionen in die Tabelle"""
        self.table_actions.setRowCount(len(self.macro['actions']))
        
        for i, action in enumerate(self.macro['actions']):
            # Typ
            type_item = QTableWidgetItem(action.get('type', ''))
            self.table_actions.setItem(i, 0, type_item)
            
            # Details
            details = []
            for key, value in action.items():
                if key not in ['type', 'delay', 'timestamp']:
                    details.append(f"{key}={value}")
            details_item = QTableWidgetItem(", ".join(details))
            self.table_actions.setItem(i, 1, details_item)
            
            # Verzögerung
            delay_item = QTableWidgetItem(f"{action.get('delay', 0):.3f}")
            self.table_actions.setItem(i, 2, delay_item)
    
    def on_infinite_changed(self, state):
        """Callback wenn Unendlich-Checkbox geändert wird"""
        self.spin_loops.setEnabled(state != Qt.CheckState.Checked.value)
    
    def detect_current_window(self):
        """Erfasst das aktuell aktive Fenster"""
        from core import WindowDetector
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
    
    def _on_window_preset_changed(self, index: int):
        data = self.combo_window_preset.currentData()
        if data is not None and data != "":
            self.txt_window_filter.blockSignals(True)
            self.txt_window_filter.setText(data)
            self.txt_window_filter.blockSignals(False)
    
    def _on_window_filter_text_changed(self, text: str):
        idx = self.combo_window_preset.findData(text)
        if idx >= 0:
            self.combo_window_preset.blockSignals(True)
            self.combo_window_preset.setCurrentIndex(idx)
            self.combo_window_preset.blockSignals(False)
        elif self.combo_window_preset.currentIndex() != 0:
            self.combo_window_preset.blockSignals(True)
            self.combo_window_preset.setCurrentIndex(0)
            self.combo_window_preset.blockSignals(False)
    
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
            'name': self.txt_name.text(),
            'description': self.txt_description.toPlainText(),
            'actions': self.macro['actions'],
            'hotkey': self.txt_hotkey.text(),
            'loop_count': self.spin_loops.value(),
            'loop_infinite': self.chk_infinite.isChecked(),
            'delay_between_loops': self.spin_delay.value(),
            'window_filter': self.txt_window_filter.text()
        }

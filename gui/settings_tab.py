"""
Einstellungs Tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QLineEdit, QCheckBox, QSpinBox,
                              QDoubleSpinBox, QGroupBox, QComboBox, QMessageBox,
                              QFormLayout, QFileDialog, QApplication, QScrollArea, QFrame,
                              QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from database import DatabaseManager
from core import HotkeyManager, WindowDetector
from gui.themes import THEME_IDS, get_theme_display_name, apply_theme, DEFAULT_THEME
from pynput import keyboard, mouse
import json
from pathlib import Path


class SettingsTab(QWidget):
    """Tab für Einstellungen"""

    # Wird aus einem anderen Thread (HotkeyManager) emit-tet, um die UI zu aktualisieren
    hotkey_debug_signal = pyqtSignal(str)
    settings_saved = pyqtSignal()

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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Tab-Widget für Unterkategorien
        self.sub_tabs = QTabWidget()
        main_layout.addWidget(self.sub_tabs)

        # --- Tab 1: Allgemein & Design ---
        general_tab = QWidget()
        general_tab_layout = QVBoxLayout(general_tab)
        
        scroll_general = QScrollArea()
        scroll_general.setWidgetResizable(True)
        scroll_general.setFrameShape(QFrame.Shape.NoFrame)
        general_container = QWidget()
        general_vbox = QVBoxLayout(general_container)

        # Allgemeine Einstellungen
        general_group = QGroupBox("Allgemeine Einstellungen")
        general_layout = QFormLayout()
        
        self.chk_autostart = QCheckBox("Beim Windows-Start automatisch starten")
        general_layout.addRow("Autostart:", self.chk_autostart)
        
        self.chk_minimize_tray = QCheckBox("In System-Tray minimieren")
        self.chk_game_mode = QCheckBox("Spiel-Modus (Overlay-Updates reduzieren, weniger CPU)")
        general_layout.addRow("System-Tray:", self.chk_minimize_tray)
        
        self.chk_show_notifications = QCheckBox("Benachrichtigungen anzeigen")
        self.chk_show_notifications.setChecked(True)
        general_layout.addRow("Benachrichtigungen:", self.chk_show_notifications)
        general_layout.addRow("Spiel-Modus:", self.chk_game_mode)
        self.chk_sound_on_macro_end = QCheckBox("Sound bei Makro-Ende (Overlay)")
        general_layout.addRow("Sound bei Ende:", self.chk_sound_on_macro_end)
        
        general_group.setLayout(general_layout)
        general_vbox.addWidget(general_group)
        
        # Design / Theme
        design_group = QGroupBox("Design")
        design_layout = QFormLayout()
        self.combo_theme = QComboBox()
        for tid in THEME_IDS:
            self.combo_theme.addItem(get_theme_display_name(tid), tid)
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        design_layout.addRow("Theme:", self.combo_theme)
        design_group.setLayout(design_layout)
        general_vbox.addWidget(design_group)
        
        general_vbox.addStretch()
        scroll_general.setWidget(general_container)
        general_tab_layout.addWidget(scroll_general)
        self.sub_tabs.addTab(general_tab, "🏠 Allgemein")

        # --- Tab 2: Aufnahme & Wiedergabe ---
        rec_play_tab = QWidget()
        rec_play_layout = QVBoxLayout(rec_play_tab)
        
        scroll_rec = QScrollArea()
        scroll_rec.setWidgetResizable(True)
        scroll_rec.setFrameShape(QFrame.Shape.NoFrame)
        rec_container = QWidget()
        rec_vbox = QVBoxLayout(rec_container)

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
        rec_vbox.addWidget(recording_group)
        
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
        rec_vbox.addWidget(playback_group)

        # Anti-Erkennung
        antidetect_group = QGroupBox("Anti-Erkennung")
        antidetect_layout = QFormLayout()
        self.chk_humanize_click_offset = QCheckBox("Klick-Zufalls-Offset (einige Pixel Abweichung)")
        antidetect_layout.addRow("", self.chk_humanize_click_offset)
        self.chk_humanize_delay_enabled = QCheckBox("Zufalls-Delay vor jeder Aktion")
        antidetect_layout.addRow("", self.chk_humanize_delay_enabled)
        humanize_delay_layout = QHBoxLayout()
        self.spin_humanize_delay_min_ms = QSpinBox()
        self.spin_humanize_delay_min_ms.setRange(0, 2000)
        self.spin_humanize_delay_min_ms.setValue(0)
        self.spin_humanize_delay_min_ms.setSuffix(" ms")
        humanize_delay_layout.addWidget(self.spin_humanize_delay_min_ms)
        humanize_delay_layout.addWidget(QLabel("–"))
        self.spin_humanize_delay_max_ms = QSpinBox()
        self.spin_humanize_delay_max_ms.setRange(0, 2000)
        self.spin_humanize_delay_max_ms.setValue(150)
        self.spin_humanize_delay_max_ms.setSuffix(" ms")
        humanize_delay_layout.addWidget(self.spin_humanize_delay_max_ms)
        antidetect_layout.addRow("Delay-Bereich:", humanize_delay_layout)
        antidetect_group.setLayout(antidetect_layout)
        rec_vbox.addWidget(antidetect_group)
        
        rec_vbox.addStretch()
        scroll_rec.setWidget(rec_container)
        rec_play_layout.addWidget(scroll_rec)
        self.sub_tabs.addTab(rec_play_tab, "🎙️ Aufnahme & Wiedergabe")

        # --- Tab 3: Hotkeys ---
        hotkeys_tab = QWidget()
        hotkeys_tab_layout = QVBoxLayout(hotkeys_tab)
        
        scroll_hk = QScrollArea()
        scroll_hk.setWidgetResizable(True)
        scroll_hk.setFrameShape(QFrame.Shape.NoFrame)
        hk_container = QWidget()
        hk_vbox = QVBoxLayout(hk_container)

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
        pause_resume_layout = QHBoxLayout()
        self.txt_pause_resume_hotkey = QLineEdit()
        self.txt_pause_resume_hotkey.setPlaceholderText("Pause/Resume Makro")
        pause_resume_layout.addWidget(self.txt_pause_resume_hotkey)
        self.btn_pause_resume_hk = QPushButton("🎙️ Aufnahme")
        self.btn_pause_resume_hk.setMaximumWidth(100)
        self.btn_pause_resume_hk.clicked.connect(lambda: self.start_hotkey_recording(self.txt_pause_resume_hotkey))
        pause_resume_layout.addWidget(self.btn_pause_resume_hk)
        hotkey_layout.addRow("⏸️ Pause/Resume Makro:", pause_resume_layout)
        
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
        
        # Screenshot Hotkey
        screenshot_hk_layout = QHBoxLayout()
        self.txt_screenshot_hotkey = QLineEdit()
        self.txt_screenshot_hotkey.setPlaceholderText("z.B. ctrl+shift+s")
        screenshot_hk_layout.addWidget(self.txt_screenshot_hotkey)
        self.btn_screenshot_hk = QPushButton("🎙️ Aufnahme")
        self.btn_screenshot_hk.setMaximumWidth(100)
        self.btn_screenshot_hk.clicked.connect(lambda: self.start_hotkey_recording(self.txt_screenshot_hotkey))
        screenshot_hk_layout.addWidget(self.btn_screenshot_hk)
        hotkey_layout.addRow("📷 Screenshot (Vollbild):", screenshot_hk_layout)
        
        # Makro-Kette
        chain_layout = QHBoxLayout()
        self.txt_macro_chain_ids = QLineEdit()
        self.txt_macro_chain_ids.setPlaceholderText("Makro-IDs kommagetrennt, z.B. 1,2,3")
        chain_layout.addWidget(self.txt_macro_chain_ids)
        hotkey_layout.addRow("Makro-Kette (IDs):", chain_layout)
        chain_hk_layout = QHBoxLayout()
        self.txt_macro_chain_hotkey = QLineEdit()
        self.txt_macro_chain_hotkey.setPlaceholderText("Hotkey für Kette")
        chain_hk_layout.addWidget(self.txt_macro_chain_hotkey)
        self.btn_chain_hk = QPushButton("🎙️ Aufnahme")
        self.btn_chain_hk.setMaximumWidth(100)
        self.btn_chain_hk.clicked.connect(lambda: self.start_hotkey_recording(self.txt_macro_chain_hotkey))
        chain_hk_layout.addWidget(self.btn_chain_hk)
        hotkey_layout.addRow("Kette-Hotkey:", chain_hk_layout)
        # Toggle-Makro
        toggle_layout = QHBoxLayout()
        self.txt_toggle_macro_id = QLineEdit()
        self.txt_toggle_macro_id.setPlaceholderText("Makro-ID (ein Makro)")
        toggle_layout.addWidget(self.txt_toggle_macro_id)
        hotkey_layout.addRow("Toggle-Makro (ID):", toggle_layout)
        toggle_hk_layout = QHBoxLayout()
        self.txt_toggle_macro_hotkey = QLineEdit()
        self.txt_toggle_macro_hotkey.setPlaceholderText("Gleicher Hotkey startet/stoppt")
        toggle_hk_layout.addWidget(self.txt_toggle_macro_hotkey)
        self.btn_toggle_hk = QPushButton("🎙️ Aufnahme")
        self.btn_toggle_hk.setMaximumWidth(100)
        self.btn_toggle_hk.clicked.connect(lambda: self.start_hotkey_recording(self.txt_toggle_macro_hotkey))
        toggle_hk_layout.addWidget(self.btn_toggle_hk)
        hotkey_layout.addRow("Toggle-Hotkey:", toggle_hk_layout)
        
        self.chk_global_hotkeys = QCheckBox("Globale Hotkeys aktivieren")
        self.chk_global_hotkeys.setChecked(True)
        hotkey_layout.addRow("", self.chk_global_hotkeys)
        
        # Hilfe-Text für Ingame-Nutzung
        ingame_info = QLabel(
            "<div style='background-color: rgba(255, 165, 0, 0.1); border: 1px solid orange; padding: 10px; border-radius: 5px;'>"
            "<b>🎮 Ingame-Hinweise:</b><br>"
            "1. Starten Sie das Programm immer als <b>Administrator</b>.<br>"
            "2. Nutzen Sie den <b>'Fenster-Modus (Rahmenlos)'</b> (Borderless Windowed), damit das Overlay sichtbar bleibt.<br>"
            "3. Bei Anti-Cheat-Problemen aktivieren Sie 'Anti-Erkennung' oben."
            "</div>"
        )
        ingame_info.setWordWrap(True)
        hotkey_layout.addRow("", ingame_info)

        hotkey_group.setLayout(hotkey_layout)
        hk_vbox.addWidget(hotkey_group)

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
        hk_vbox.addWidget(debug_group)
        
        hk_vbox.addStretch()
        scroll_hk.setWidget(hk_container)
        hotkeys_tab_layout.addWidget(scroll_hk)
        self.sub_tabs.addTab(hotkeys_tab, "⌨️ Hotkeys")

        # --- Tab 4: API & Daten ---
        api_tab = QWidget()
        api_tab_layout = QVBoxLayout(api_tab)
        
        scroll_api = QScrollArea()
        scroll_api.setWidgetResizable(True)
        scroll_api.setFrameShape(QFrame.Shape.NoFrame)
        api_container = QWidget()
        api_vbox = QVBoxLayout(api_container)

        # API & Integrationen
        api_group = QGroupBox("API & Integrationen")
        api_layout = QFormLayout()
        api_info = QLabel(
            "<small>Lokale HTTP-API für Browser-Erweiterung, OBS, Stream Deck, Scripts. "
            "Läuft nur auf 127.0.0.1. Nach Änderung Anwendung neu starten.</small>"
        )
        api_info.setWordWrap(True)
        api_layout.addRow("", api_info)
        self.chk_api_enabled = QCheckBox("Lokale API aktivieren")
        api_layout.addRow("", self.chk_api_enabled)
        self.spin_api_port = QSpinBox()
        self.spin_api_port.setRange(1024, 65535)
        self.spin_api_port.setValue(5847)
        api_layout.addRow("Port:", self.spin_api_port)
        self.txt_webhook_token = QLineEdit()
        self.txt_webhook_token.setPlaceholderText("Optional: Token für POST /api/trigger")
        self.txt_webhook_token.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Webhook-Token:", self.txt_webhook_token)
        self.chk_outgoing_webhook = QCheckBox("Beim Makro-Ende HTTP-POST senden (Outgoing)")
        api_layout.addRow("", self.chk_outgoing_webhook)
        self.txt_outgoing_webhook_url = QLineEdit()
        self.txt_outgoing_webhook_url.setPlaceholderText("z.B. http://localhost:9000/macro-done")
        api_layout.addRow("Outgoing-URL:", self.txt_outgoing_webhook_url)
        self.txt_obs_status_file = QLineEdit()
        self.txt_obs_status_file.setPlaceholderText("Leer = aus. Pfad für OBS „Text from file“ (z.B. C:/obs/status.txt)")
        api_layout.addRow("OBS-Status-Datei:", self.txt_obs_status_file)
        api_group.setLayout(api_layout)
        api_vbox.addWidget(api_group)

        # Screenshot
        screenshot_group = QGroupBox("Screenshot")
        screenshot_layout = QFormLayout()
        self.txt_screenshot_folder = QLineEdit()
        self.txt_screenshot_folder.setPlaceholderText("Leer = data/screenshots")
        screenshot_layout.addRow("Speicherordner:", self.txt_screenshot_folder)
        screenshot_group.setLayout(screenshot_layout)
        api_vbox.addWidget(screenshot_group)

        # Video-Aufnahme
        video_group = QGroupBox("Video-Aufnahme")
        video_layout = QFormLayout()
        self.txt_video_folder = QLineEdit()
        self.txt_video_folder.setPlaceholderText("Leer = data/recordings")
        video_layout.addRow("Speicherordner:", self.txt_video_folder)
        self.spin_video_fps = QSpinBox()
        self.spin_video_fps.setRange(1, 60)
        self.spin_video_fps.setValue(30)
        self.spin_video_fps.setSuffix(" FPS")
        video_layout.addRow("FPS:", self.spin_video_fps)
        video_start_hk = QHBoxLayout()
        self.txt_video_start_hotkey = QLineEdit()
        video_start_hk.addWidget(self.txt_video_start_hotkey)
        self.btn_video_start_hk = QPushButton("🎙️ Aufnahme")
        self.btn_video_start_hk.setMaximumWidth(100)
        self.btn_video_start_hk.clicked.connect(lambda: self.start_hotkey_recording(self.txt_video_start_hotkey))
        video_start_hk.addWidget(self.btn_video_start_hk)
        video_layout.addRow("Hotkey Start:", video_start_hk)
        video_stop_hk = QHBoxLayout()
        self.txt_video_stop_hotkey = QLineEdit()
        video_stop_hk.addWidget(self.txt_video_stop_hotkey)
        self.btn_video_stop_hk = QPushButton("🎙️ Aufnahme")
        self.btn_video_stop_hk.setMaximumWidth(100)
        self.btn_video_stop_hk.clicked.connect(lambda: self.start_hotkey_recording(self.txt_video_stop_hotkey))
        video_stop_hk.addWidget(self.btn_video_stop_hk)
        video_layout.addRow("Hotkey Stopp:", video_stop_hk)
        video_group.setLayout(video_layout)
        api_vbox.addWidget(video_group)
        
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
        diagnose_layout =  QHBoxLayout()
        self.btn_test_window = QPushButton("🧪 Fenster-Erkennung testen")
        self.btn_test_window.clicked.connect(self.test_window_detection)
        diagnose_layout.addWidget(self.btn_test_window)
        diagnose_layout.addStretch()
        data_layout.addLayout(diagnose_layout)
        data_group.setLayout(data_layout)
        api_vbox.addWidget(data_group)

        api_vbox.addStretch()
        scroll_api.setWidget(api_container)
        api_tab_layout.addWidget(scroll_api)
        self.sub_tabs.addTab(api_tab, "📊 API & Daten")

        # --- Speichern-Button ---
        btn_save_layout = QHBoxLayout()
        btn_save_layout.addStretch()
        self.btn_save = QPushButton("💾 Einstellungen speichern")
        self.btn_save.setObjectName("btn_play") # Nutzt das grüne Design
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_save.setMinimumHeight(40)
        btn_save_layout.addWidget(self.btn_save)
        main_layout.addLayout(btn_save_layout)
    
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
        self.chk_humanize_click_offset.setChecked(settings.get('humanize_click_offset', 'false') == 'true')
        self.chk_humanize_delay_enabled.setChecked(settings.get('humanize_delay_enabled', 'false') == 'true')
        self.spin_humanize_delay_min_ms.setValue(int(settings.get('humanize_delay_min_ms', '0')))
        self.spin_humanize_delay_max_ms.setValue(int(settings.get('humanize_delay_max_ms', '150')))
        
        # Hotkeys
        self.txt_hotkey_record_start.setText(settings.get('hotkey_record_start', ''))
        self.txt_hotkey_play_start.setText(settings.get('hotkey_play_start', ''))
        self.txt_hotkey_record_stop.setText(settings.get('hotkey_record_stop', ''))
        self.txt_hotkey_play_stop.setText(settings.get('hotkey_play_stop', ''))
        self.txt_emergency_stop.setText(settings.get('emergency_stop_hotkey', ''))
        self.txt_pause_resume_hotkey.setText(settings.get('pause_resume_hotkey', ''))
        self.txt_overlay_toggle.setText(settings.get('overlay_toggle_hotkey', 'ctrl+shift+o'))
        self.txt_screenshot_hotkey.setText(settings.get('screenshot_hotkey', ''))
        self.txt_macro_chain_ids.setText(settings.get('macro_chain_ids', ''))
        self.txt_macro_chain_hotkey.setText(settings.get('macro_chain_hotkey', ''))
        self.txt_toggle_macro_id.setText(settings.get('toggle_macro_id', ''))
        self.txt_toggle_macro_hotkey.setText(settings.get('toggle_macro_hotkey', ''))
        self.chk_global_hotkeys.setChecked(settings.get('global_hotkeys', 'true') == 'true')
        self.chk_game_mode.setChecked(settings.get('game_mode', 'false') == 'true')
        self.chk_sound_on_macro_end.setChecked(settings.get('sound_on_macro_end', 'false') == 'true')
        # API
        self.chk_api_enabled.setChecked(settings.get('api_enabled', 'false') == 'true')
        self.spin_api_port.setValue(int(settings.get('api_port', '5847')))
        self.txt_webhook_token.setText(settings.get('webhook_token', ''))
        self.chk_outgoing_webhook.setChecked(settings.get('outgoing_webhook_enabled', 'false') == 'true')
        self.txt_outgoing_webhook_url.setText(settings.get('outgoing_webhook_url', ''))
        self.txt_obs_status_file.setText(settings.get('obs_status_file', ''))
        self.txt_screenshot_folder.setText(settings.get('screenshot_folder', ''))
        self.txt_video_folder.setText(settings.get('video_folder', ''))
        self.spin_video_fps.setValue(int(settings.get('video_fps', '30')))
        self.txt_video_start_hotkey.setText(settings.get('video_start_hotkey', ''))
        self.txt_video_stop_hotkey.setText(settings.get('video_stop_hotkey', ''))
        # Theme
        theme_id = settings.get('theme_id', DEFAULT_THEME)
        idx = self.combo_theme.findData(theme_id)
        if idx >= 0:
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(idx)
            self.combo_theme.blockSignals(False)
    
    def _on_theme_changed(self):
        """Theme sofort anwenden wenn Nutzer die ComboBox ändert."""
        theme_id = self.combo_theme.currentData()
        if theme_id:
            app = QApplication.instance()
            apply_theme(app, theme_id)
    
    def save_settings(self):
        """Speichert Einstellungen"""
        # Allgemein
        self.db.set_setting('autostart', 'true' if self.chk_autostart.isChecked() else 'false')
        self.db.set_setting('minimize_tray', 'true' if self.chk_minimize_tray.isChecked() else 'false')
        self.db.set_setting('show_notifications', 'true' if self.chk_show_notifications.isChecked() else 'false')
        theme_id = self.combo_theme.currentData()
        if theme_id:
            self.db.set_setting('theme_id', theme_id)
        
        # Aufnahme
        self.db.set_setting('mouse_threshold', str(self.spin_mouse_threshold.value()))
        self.db.set_setting('record_mouse_moves', 'true' if self.chk_record_mouse_moves.isChecked() else 'false')
        self.db.set_setting('record_keyboard', 'true' if self.chk_record_keyboard.isChecked() else 'false')
        
        # Wiedergabe
        self.db.set_setting('default_speed', str(self.spin_default_speed.value()))
        self.db.set_setting('stop_on_error', 'true' if self.chk_stop_on_error.isChecked() else 'false')
        self.db.set_setting('humanize_click_offset', 'true' if self.chk_humanize_click_offset.isChecked() else 'false')
        self.db.set_setting('humanize_delay_enabled', 'true' if self.chk_humanize_delay_enabled.isChecked() else 'false')
        self.db.set_setting('humanize_delay_min_ms', str(self.spin_humanize_delay_min_ms.value()))
        self.db.set_setting('humanize_delay_max_ms', str(self.spin_humanize_delay_max_ms.value()))
        
        # Hotkeys
        self.db.set_setting('hotkey_record_start', self.txt_hotkey_record_start.text())
        self.db.set_setting('hotkey_play_start', self.txt_hotkey_play_start.text())
        self.db.set_setting('hotkey_record_stop', self.txt_hotkey_record_stop.text())
        self.db.set_setting('hotkey_play_stop', self.txt_hotkey_play_stop.text())
        self.db.set_setting('emergency_stop_hotkey', self.txt_emergency_stop.text())
        self.db.set_setting('pause_resume_hotkey', self.txt_pause_resume_hotkey.text())
        self.db.set_setting('overlay_toggle_hotkey', self.txt_overlay_toggle.text())
        self.db.set_setting('screenshot_hotkey', self.txt_screenshot_hotkey.text())
        self.db.set_setting('macro_chain_ids', self.txt_macro_chain_ids.text().strip())
        self.db.set_setting('macro_chain_hotkey', self.txt_macro_chain_hotkey.text())
        self.db.set_setting('toggle_macro_id', self.txt_toggle_macro_id.text().strip())
        self.db.set_setting('toggle_macro_hotkey', self.txt_toggle_macro_hotkey.text())
        self.db.set_setting('global_hotkeys', 'true' if self.chk_global_hotkeys.isChecked() else 'false')
        self.db.set_setting('game_mode', 'true' if self.chk_game_mode.isChecked() else 'false')
        self.db.set_setting('sound_on_macro_end', 'true' if self.chk_sound_on_macro_end.isChecked() else 'false')
        # API
        self.db.set_setting('api_enabled', 'true' if self.chk_api_enabled.isChecked() else 'false')
        self.db.set_setting('api_port', str(self.spin_api_port.value()))
        self.db.set_setting('webhook_token', self.txt_webhook_token.text())
        self.db.set_setting('outgoing_webhook_enabled', 'true' if self.chk_outgoing_webhook.isChecked() else 'false')
        self.db.set_setting('outgoing_webhook_url', self.txt_outgoing_webhook_url.text().strip())
        self.db.set_setting('obs_status_file', self.txt_obs_status_file.text().strip())
        self.db.set_setting('screenshot_folder', self.txt_screenshot_folder.text().strip())
        self.db.set_setting('video_folder', self.txt_video_folder.text().strip())
        self.db.set_setting('video_fps', str(self.spin_video_fps.value()))
        self.db.set_setting('video_start_hotkey', self.txt_video_start_hotkey.text())
        self.db.set_setting('video_stop_hotkey', self.txt_video_stop_hotkey.text())
        
        self.settings_saved.emit()
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
            "advanced_gaming_export.json",
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
        backup_path = backup_dir / f"advanced_gaming_backup_{timestamp}.db"
        
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

"""
Hauptfenster der Anwendung
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QTabWidget, QPushButton, QToolBar, QStatusBar,
                              QMessageBox, QLabel, QFileDialog, QApplication,
                              QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QCloseEvent

import sys
from pathlib import Path
import subprocess

from gui.profile_tab import ProfileTab
from gui.macro_tab import MacroTab
from gui.recorder_tab import RecorderTab
from gui.settings_tab import SettingsTab
from gui.overlay import GamingOverlay
from gui.action_editor import MacroEditorWidget
from gui.log_viewer import LogViewerWidget
from gui.template_manager import TemplateManagerWidget
from gui.scheduler_tab import SchedulerTab
from gui.statistics_tab import StatisticsTab
from gui.tools_tab import ToolsTab
from database import DatabaseManager
from core import HotkeyManager, WindowDetector
from core.logging_system import LogManager
from core.api_server import APIServer
from core.screenshot import capture_fullscreen, get_screenshot_folder
from core.system_tray import SystemTrayManager
from core.version import APP_NAME, APP_VERSION, APP_COPYRIGHT, UPDATE_BASE_URL
from gui.themes import apply_theme, DEFAULT_THEME
from core.updater import get_update_info, download_file

class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung"""
    
    def __init__(self):
        super().__init__()
        
        # Logging initialisieren (als erstes!)
        self.log_manager = LogManager()
        self.log_manager.info(f"{APP_NAME} v{APP_VERSION} gestartet")
        
        # Manager initialisieren
        self.db = DatabaseManager()
        self.hotkey_manager = HotkeyManager()
        self.window_detector = WindowDetector()
        
        # Tabs initialisieren (vor init_ui!)
        self.profile_tab = ProfileTab(self.db, self.hotkey_manager)
        self.macro_tab = MacroTab(self.db, self.hotkey_manager, self.window_detector)
        self.recorder_tab = RecorderTab(self.db)
        self.log_viewer_tab = LogViewerWidget()
        self.scheduler_tab = SchedulerTab(self.db)
        self.statistics_tab = StatisticsTab(self.db)
        self.template_manager_tab = TemplateManagerWidget()
        self.tools_tab = ToolsTab(self.db)
        self.settings_tab = SettingsTab(self.db, self.hotkey_manager)
        
        # Gaming-Overlay (nach Tabs initialisieren, da Verbindungen zu macro_tab bestehen)
        self.overlay = GamingOverlay(self.db)
        self.overlay.stop_all_requested.connect(self.emergency_stop)
        self.overlay.pause_requested.connect(self.macro_tab.player.pause)
        self.overlay.resume_requested.connect(self.macro_tab.player.resume)
        self.overlay.play_macro_requested.connect(self.on_hotkey_play_start)
        self.overlay.video_record_requested.connect(self.toggle_video_recording)
        self.overlay.add_macro_requested.connect(self.add_macro_from_overlay)
        self.overlay.screenshot_requested.connect(self.take_screenshot)
        
        # System Tray
        self.system_tray = SystemTrayManager(self)
        self.system_tray.show_window.connect(self.show_from_tray)
        self.system_tray.quit_app.connect(self.close)
        self.system_tray.execute_macro.connect(self.execute_macro_from_tray)
        self.system_tray.show()
        self._registered_macro_hotkeys = []
        self._macro_chain_queue = []
        
        self.init_ui()
        self.setup_statusbar()
        self.load_settings()
        self.overlay.set_game_mode(self.db.get_setting('game_mode', 'false') == 'true')
        self.overlay.set_sound_on_end(self.db.get_setting('sound_on_macro_end', 'false') == 'true')
        self.settings_tab.settings_saved.connect(self.on_settings_saved)
        
        # Hotkey-Manager starten
        self.hotkey_manager.start()
        
        # Globale System-Hotkeys registrieren
        self.register_global_hotkeys()
        
        # Lokale API starten (falls aktiviert)
        self.api_server = None
        self.start_api_server()
        
        # Window-Überwachung starten
        self.window_detector.start_monitoring(
            on_window_change=self.on_window_changed
        )
        
        # Periodischer Update für Overlay-Scheduler-Info
        self.scheduler_update_timer = QTimer(self)
        self.scheduler_update_timer.timeout.connect(self._update_overlay_scheduler_info)
        self.scheduler_update_timer.start(30000) # Alle 30 Sekunden
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - Professional Macro & Game Tool")
        
        # Bildschirmgröße ermitteln für responsives Design
        screen = QApplication.primaryScreen().geometry()
        width = min(1200, int(screen.width() * 0.8))
        height = min(800, int(screen.height() * 0.8))
        self.resize(width, height)
        
        # Zentrale Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Haupt-Layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab-Widget erstellen
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Tabs hinzufügen (bereits initialisiert im __init__)
        self.tabs.addTab(self.profile_tab, "📁 Profile")
        self.tabs.addTab(self.macro_tab, "⚡ Makros")
        self.tabs.addTab(self.recorder_tab, "🎙️ Aufnahme")
        self.tabs.addTab(self.scheduler_tab, "⏰ Scheduler")
        self.tabs.addTab(self.log_viewer_tab, "📋 Logs")
        self.tabs.addTab(self.statistics_tab, "📊 Statistiken")
        self.tabs.addTab(self.template_manager_tab, "🖼️ Templates")
        self.tabs.addTab(self.tools_tab, "🔧 Tools")
        self.tabs.addTab(self.settings_tab, "⚙️ Einstellungen")
        
        # UI Modernisierung: Icons vergrößern und Abstände anpassen
        self.tabs.setIconSize(self.tabs.iconSize() * 1.2)
        
        layout.addWidget(self.tabs)
        
        # Toolbar erstellen (nach den Tabs!)
        self.create_toolbar()
        
        # Verbindungen
        self.profile_tab.profile_selected.connect(self.on_profile_selected)
        self.recorder_tab.macro_saved.connect(self.macro_tab.refresh_macros)
        self.macro_tab.macro_list_changed.connect(self.refresh_macro_hotkeys)
        
        # Overlay-Verbindungen
        self.recorder_tab.recording_started.connect(lambda: self.overlay.set_recording(True))
        self.recorder_tab.recording_stopped.connect(lambda: self.overlay.set_recording(False))
        self.macro_tab.playback_started.connect(self.on_playback_started)
        self.macro_tab.playback_stopped.connect(self.on_playback_stopped)
        self.macro_tab.playback_progress.connect(self.overlay.set_playback_progress)
        self.macro_tab.player.on_complete_callback = self.overlay.set_macro_stopped
        self.macro_tab.player.on_action_event_callback = self._on_player_action_event
        
        # Log-Weiterleitung an Overlay
        self.log_manager.signal_handler.log_message.connect(self._on_log_message_for_overlay)
        
        # Scheduler-Verbindungen
        self.scheduler_tab.execute_macro.connect(self.execute_scheduled_macro)
        self.recorder_tab.macro_saved.connect(self.macro_tab.refresh_macros)
        
        # Overlay-Verbindungen
        self.recorder_tab.recording_started.connect(lambda: self.overlay.set_recording(True))
        self.recorder_tab.recording_stopped.connect(lambda: self.overlay.set_recording(False))
        self.macro_tab.playback_started.connect(self.on_playback_started)
        self.macro_tab.playback_stopped.connect(self.on_playback_stopped)
        self.macro_tab.playback_progress.connect(self.overlay.set_playback_progress)
    
    def create_toolbar(self):
        """Erstellt die Toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setIconSize(self.tabs.iconSize()) # Standardgröße
        self.addToolBar(toolbar)
        
        # Spacer für Zentrierung oder Abstände
        def add_spacer():
            spacer = QWidget()
            spacer.setFixedWidth(10)
            toolbar.addWidget(spacer)

        add_spacer()

        # Neues Profil
        new_profile_action = QAction("📁 Neues Profil", self)
        new_profile_action.setShortcut(QKeySequence("Ctrl+N"))
        new_profile_action.triggered.connect(self.profile_tab.create_profile)
        toolbar.addAction(new_profile_action)
        
        add_spacer()
        toolbar.addSeparator()
        add_spacer()
        
        # Neues Makro
        new_macro_action = QAction("⚡ Neues Makro", self)
        new_macro_action.setShortcut(QKeySequence("Ctrl+M"))
        new_macro_action.triggered.connect(self.macro_tab.create_macro)
        toolbar.addAction(new_macro_action)
        
        add_spacer()
        
        # Aufnahme starten
        record_action = QAction("🎙️ Aufnahme", self)
        record_action.setShortcut(QKeySequence("Ctrl+R"))
        record_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.recorder_tab))
        toolbar.addAction(record_action)
        
        add_spacer()
        toolbar.addSeparator()
        add_spacer()
        
        # Screenshot
        screenshot_action = QAction("📷 Screenshot", self)
        screenshot_action.setToolTip("Vollbild-Screenshot speichern")
        screenshot_action.triggered.connect(self.take_screenshot)
        toolbar.addAction(screenshot_action)

        # Flexibler Spacer um Einstellungen nach rechts zu schieben
        right_spacer = QWidget()
        from PyQt6.QtWidgets import QSizePolicy
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(right_spacer)
        
        # Gaming-Overlay
        overlay_action = QAction("🎮 Overlay", self)
        overlay_action.setToolTip("Overlay an/aus")
        overlay_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        overlay_action.triggered.connect(self.toggle_overlay)
        toolbar.addAction(overlay_action)

        add_spacer()

        # Hotkeys anzeigen
        hotkeys_action = QAction("⌨️ Hotkeys", self)
        hotkeys_action.triggered.connect(self.show_hotkeys)
        toolbar.addAction(hotkeys_action)

        add_spacer()

        # Update prüfen / herunterladen
        update_action = QAction("🔄 Update", self)
        update_action.triggered.connect(self.check_for_update)
        toolbar.addAction(update_action)

        add_spacer()

        # Einstellungen
        settings_action = QAction("⚙️ Einstellungen", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.settings_tab))
        toolbar.addAction(settings_action)
        
        add_spacer()
    
    def setup_statusbar(self):
        """Richtet die Statusleiste ein"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Aktives Fenster anzeigen
        self.window_label = QLabel("Fenster: -")
        self.statusbar.addPermanentWidget(self.window_label)
        
        # Status
        self.statusbar.showMessage("Bereit")
    
    def on_window_changed(self, window_info: dict):
        """Callback wenn sich das aktive Fenster ändert"""
        title = window_info.get('title', '-')
        process = window_info.get('process', '-')
        self.window_label.setText(f"Fenster: {title} ({process})")
        if hasattr(self, 'overlay'):
            self.overlay.set_active_window(title, process)
    
    def on_profile_selected(self, profile_id: int):
        """Callback wenn ein Profil ausgewählt wurde"""
        self.macro_tab.load_profile(profile_id)
        self.refresh_macro_hotkeys()
        profile = self.db.get_profile(profile_id)
        if profile:
            self.statusbar.showMessage(f"Profil geladen: {profile['name']}")
    
    def refresh_macro_hotkeys(self):
        """Makro-Hotkeys für das aktuelle Profil registrieren (alte abmelden, neue anmelden)."""
        for norm in getattr(self, "_registered_macro_hotkeys", []):
            self.hotkey_manager.unregister_hotkey(norm)
        self._registered_macro_hotkeys = []
        profile_id = self.profile_tab.get_selected_profile()
        if not profile_id:
            return
        macros = self.db.get_macros(profile_id)
        for macro in macros:
            hotkey = (macro.get("hotkey") or "").strip()
            if not hotkey:
                continue
            normalized = self.hotkey_manager.parse_hotkey(hotkey)
            macro_id = macro["id"]
            self.hotkey_manager.register_hotkey(
                normalized,
                lambda mid=macro_id: self.macro_tab.play_macro_by_id(mid),
            )
            self._registered_macro_hotkeys.append(normalized)
    
    def _on_log_message_for_overlay(self, level: str, msg: str):
        """Leitet wichtige Log-Nachrichten an das Overlay weiter."""
        if level in ("INFO", "WARNING", "ERROR"):
            # Bereinigen (Zeitstempel etc. entfernen falls im msg)
            clean_msg = msg.split('|')[-1].strip() if '|' in msg else msg
            self.overlay.set_mini_log(clean_msg)

    def _on_player_action_event(self, event_type: str, status: str, details: Any):
        """Behandelt Ereignisse vom MacroPlayer für visuelles Feedback."""
        if event_type in ('image_recognition', 'pixel_recognition'):
            if status == 'success':
                self.overlay.flash_success()
                self._session_success_count = getattr(self, "_session_success_count", 0) + 1
            elif status == 'fail':
                self.overlay.flash_error()
                self._session_fail_count = getattr(self, "_session_fail_count", 0) + 1
            
            # Statistik im Overlay aktualisieren
            self.overlay.set_session_stats(
                getattr(self, "_session_success_count", 0),
                getattr(self, "_session_fail_count", 0)
            )
        elif event_type == 'skill_rotation' and status == 'update':
            self.overlay.set_skill_rotation(details)
        elif event_type == 'status_bar' and status == 'update':
            # details erwartet hier (percent, color_str)
            if isinstance(details, (list, tuple)) and len(details) >= 2:
                self.overlay.set_status_bar(details[0], details[1])
            else:
                self.overlay.set_status_bar(details)

    def _write_obs_status(self, text: str):
        """Schreibt Status-Text in OBS-Status-Datei (für OBS „Text from file“)."""
        path = self.db.get_setting('obs_status_file', '').strip()
        if not path:
            return
        try:
            Path(path).write_text(text, encoding='utf-8')
        except Exception:
            pass

    def on_playback_started(self, macro_name: str):
        """Wird aufgerufen, wenn Makro-Wiedergabe startet"""
        self.overlay.set_macro_running(macro_name)
        self._write_obs_status("Läuft: " + macro_name)
        
        # Scheduler-Info im Overlay aktualisieren
        self._update_overlay_scheduler_info()
    
    def _update_overlay_scheduler_info(self):
        """Sendet Info über das nächste geplante Makro an das Overlay."""
        next_macro = self.scheduler_tab.scheduler.get_next_scheduled_macro()
        if next_macro:
            name = next_macro.macro_name
            next_run = next_macro.next_run
            import datetime
            now = datetime.datetime.now()
            diff = next_run - now
            
            # Formatieren
            if diff.total_seconds() < 3600:
                time_str = f"{int(max(0, diff.total_seconds()) // 60)}m"
            else:
                time_str = next_run.strftime("%H:%M")
            self.overlay.set_next_schedule(f"{name} ({time_str})")
        else:
            self.overlay.set_next_schedule("")

    def load_settings(self):
        """Lädt gespeicherte Einstellungen"""
        # Fensterposition und -größe laden
        geometry = self.db.get_setting('window_geometry', '')
        if geometry:
            try:
                x, y, w, h = map(int, geometry.split(','))
                self.setGeometry(x, y, w, h)
            except:
                pass
        
        # Letztes aktives Profil laden
        last_profile = self.db.get_setting('last_profile', '')
        if last_profile:
            try:
                profile_id = int(last_profile)
                self.profile_tab.select_profile(profile_id)
            except:
                pass
        
        # Theme anwenden (gespeichertes Design)
        theme_id = self.db.get_setting('theme_id', DEFAULT_THEME)
        app = QApplication.instance()
        if app:
            apply_theme(app, theme_id)
    
    def register_global_hotkeys(self):
        """Registriert globale System-Hotkeys"""
        # Prüfen ob globale Hotkeys aktiviert sind
        if self.db.get_setting('global_hotkeys', 'true') != 'true':
            return
        
        # Aufnahme starten
        hotkey_record_start = self.db.get_setting('hotkey_record_start', '')
        if hotkey_record_start:
            normalized = self.hotkey_manager.parse_hotkey(hotkey_record_start)
            self.hotkey_manager.register_hotkey(normalized, self.on_hotkey_record_start)

        # Wiedergabe starten
        hotkey_play_start = self.db.get_setting('hotkey_play_start', '')
        if hotkey_play_start:
            normalized = self.hotkey_manager.parse_hotkey(hotkey_play_start)
            self.hotkey_manager.register_hotkey(normalized, self.on_hotkey_play_start)
        
        # Aufnahme stoppen
        hotkey_record_stop = self.db.get_setting('hotkey_record_stop', '')
        if hotkey_record_stop:
            normalized = self.hotkey_manager.parse_hotkey(hotkey_record_stop)
            self.hotkey_manager.register_hotkey(normalized, self.on_hotkey_record_stop)
        
        # Wiedergabe stoppen
        hotkey_play_stop = self.db.get_setting('hotkey_play_stop', '')
        if hotkey_play_stop:
            normalized = self.hotkey_manager.parse_hotkey(hotkey_play_stop)
            self.hotkey_manager.register_hotkey(normalized, self.on_hotkey_play_stop)
        
        # Notfall-Stop (alles stoppen)
        emergency_stop = self.db.get_setting('emergency_stop_hotkey', '')
        if emergency_stop:
            normalized = self.hotkey_manager.parse_hotkey(emergency_stop)
            self.hotkey_manager.register_hotkey(normalized, self.on_hotkey_emergency_stop)
        pause_resume_hk = self.db.get_setting('pause_resume_hotkey', '')
        if pause_resume_hk:
            normalized = self.hotkey_manager.parse_hotkey(pause_resume_hk)
            self.hotkey_manager.register_hotkey(normalized, self.macro_tab.toggle_pause_resume)
        
        # Overlay-Toggle
        overlay_hotkey = self.db.get_setting('overlay_toggle_hotkey', 'ctrl+shift+o')
        if overlay_hotkey:
            normalized = self.hotkey_manager.parse_hotkey(overlay_hotkey)
            self.hotkey_manager.register_hotkey(normalized, self.toggle_overlay)
        screenshot_hotkey = self.db.get_setting('screenshot_hotkey', '')
        if screenshot_hotkey:
            normalized = self.hotkey_manager.parse_hotkey(screenshot_hotkey)
            self.hotkey_manager.register_hotkey(normalized, self.take_screenshot)
        chain_hk = self.db.get_setting('macro_chain_hotkey', '')
        if chain_hk:
            normalized = self.hotkey_manager.parse_hotkey(chain_hk)
            self.hotkey_manager.register_hotkey(normalized, self.start_macro_chain)
        toggle_hk = self.db.get_setting('toggle_macro_hotkey', '')
        if toggle_hk:
            normalized = self.hotkey_manager.parse_hotkey(toggle_hk)
            self.hotkey_manager.register_hotkey(normalized, self.toggle_macro)
        video_start_hk = self.db.get_setting('video_start_hotkey', '')
        if video_start_hk:
            normalized = self.hotkey_manager.parse_hotkey(video_start_hk)
            self.hotkey_manager.register_hotkey(normalized, self.start_video_recording)
        video_stop_hk = self.db.get_setting('video_stop_hotkey', '')
        if video_stop_hk:
            normalized = self.hotkey_manager.parse_hotkey(video_stop_hk)
            self.hotkey_manager.register_hotkey(normalized, self.stop_video_recording)
    
    def start_video_recording(self):
        """Startet Bildschirm-Video (Hotkey oder von außen)."""
        if hasattr(self, 'tools_tab'):
            self.tools_tab.start_video()
            if hasattr(self, 'overlay'):
                self.overlay.set_video_recording(True)
    
    def stop_video_recording(self):
        """Stoppt Bildschirm-Video."""
        if hasattr(self, 'tools_tab'):
            self.tools_tab.stop_video()
            if hasattr(self, 'overlay'):
                self.overlay.set_video_recording(False)

    def toggle_video_recording(self, start: bool):
        """Umschalten der Videoaufnahme vom Overlay aus"""
        if start:
            self.start_video_recording()
        else:
            self.stop_video_recording()

    def add_macro_from_overlay(self):
        """Öffnet den Dialog zum Erstellen eines neuen Makros (vom Overlay aus)"""
        self.show_from_tray()
        self.tabs.setCurrentWidget(self.macro_tab)
        self.macro_tab.create_macro()
    
    def take_screenshot(self):
        """Vollbild-Screenshot speichern (Toolbar oder Hotkey)."""
        save_dir = get_screenshot_folder(self.db.get_setting('screenshot_folder', ''))
        path = capture_fullscreen(save_dir)
        if path:
            msg = f"Screenshot gespeichert: {path.name}"
            self.statusbar.showMessage(msg, 5000)
            if hasattr(self, 'overlay'):
                self.overlay.set_mini_log("📸 Screenshot gespeichert")
            if self.db.get_setting('show_notifications', 'true') == 'true':
                self.system_tray.show_message("Screenshot", msg)
        else:
            self.statusbar.showMessage("Screenshot fehlgeschlagen.", 3000)
            if hasattr(self, 'overlay'):
                self.overlay.set_mini_log("❌ Screenshot Fehler")
    
    def start_macro_chain(self):
        """Startet die konfigurierte Makro-Kette (Hotkey)."""
        ids_str = self.db.get_setting('macro_chain_ids', '').strip()
        if not ids_str:
            return
        try:
            self._macro_chain_queue = [int(x.strip()) for x in ids_str.split(',') if x.strip()]
        except ValueError:
            return
        if not self._macro_chain_queue:
            return
        first_id = self._macro_chain_queue.pop(0)
        self.macro_tab.play_macro_by_id(first_id, skip_window_check=True)
    
    def on_playback_stopped(self):
        """Wird aufgerufen, wenn Makro-Wiedergabe stoppt. OBS-Status, Overlay, ggf. Makro-Kette."""
        self._write_obs_status("Bereit")
        self.overlay.set_macro_stopped()
        self.on_playback_stopped_chain()

    def on_playback_stopped_chain(self):
        """Führt die nächste Makro-ID aus der Kette aus (nach playback_stopped)."""
        if not self._macro_chain_queue:
            return
        next_id = self._macro_chain_queue.pop(0)
        self.macro_tab.play_macro_by_id(next_id, skip_window_check=True)
    
    def toggle_macro(self):
        """Toggle-Makro: Wenn Wiedergabe läuft stoppen, sonst konfiguriertes Makro starten."""
        toggle_id_str = self.db.get_setting('toggle_macro_id', '').strip()
        if not toggle_id_str:
            return
        try:
            toggle_id = int(toggle_id_str)
        except ValueError:
            return
        if self.macro_tab.player.is_playing:
            self.macro_tab.stop_macro()
        else:
            self.macro_tab.play_macro_by_id(toggle_id, skip_window_check=True)
    
    def on_settings_saved(self):
        """Wird nach Speichern der Einstellungen aufgerufen (z. B. Spiel-Modus, Sound bei Ende)."""
        self.overlay.set_game_mode(self.db.get_setting('game_mode', 'false') == 'true')
        self.overlay.set_sound_on_end(self.db.get_setting('sound_on_macro_end', 'false') == 'true')
    
    def start_api_server(self):
        """Startet die lokale API falls in Einstellungen aktiviert."""
        if self.db.get_setting('api_enabled', 'false') != 'true':
            return
        try:
            port = int(self.db.get_setting('api_port', '5847'))
        except ValueError:
            port = 5847
        try:
            self.api_server = APIServer(
                port=port,
                get_status=self._api_get_status,
                get_profiles=self._api_get_profiles,
                get_macros=self._api_get_macros,
                start_macro=self._api_start_macro,
                stop_playback=self._api_stop_playback,
                trigger=self._api_trigger,
            )
            self.api_server.start()
            self.log_manager.info(f"Lokale API gestartet auf http://127.0.0.1:{port}")
        except OSError as e:
            self.log_manager.warning(f"API konnte nicht gestartet werden (Port {port}): {e}")
            self.api_server = None
    
    def stop_api_server(self):
        """Stoppt die lokale API."""
        if getattr(self, 'api_server', None) and self.api_server.is_running():
            self.api_server.stop()
            self.api_server = None
    
    def _api_get_status(self):
        profile_id = self.profile_tab.get_selected_profile()
        is_playing = self.macro_tab.player.is_playing
        current_macro_name = None
        if is_playing and hasattr(self.overlay, 'current_macro'):
            current_macro_name = self.overlay.current_macro
        is_recording = getattr(self.recorder_tab, 'is_recording', False)
        return {
            "running": True,
            "current_profile_id": profile_id,
            "current_macro_name": current_macro_name,
            "is_playing": is_playing,
            "is_recording": is_recording,
        }
    
    def _api_get_profiles(self):
        return [{"id": p["id"], "name": p["name"]} for p in self.db.get_profiles()]
    
    def _api_get_macros(self, profile_id=None):
        macros = self.db.get_macros(profile_id)
        return [{"id": m["id"], "name": m["name"], "profile_id": m["profile_id"]} for m in macros]
    
    def _api_start_macro(self, macro_id: int, loop_infinite: bool = False):
        self.macro_tab.play_macro_by_id(macro_id, skip_window_check=True)
    
    def _api_stop_playback(self):
        self.emergency_stop()
    
    def _api_trigger(self, macro_id: int, token: str) -> bool:
        expected = self.db.get_setting('webhook_token', '')
        if not expected or token != expected:
            return False
        self._api_start_macro(macro_id)
        return True
    
    def on_hotkey_record_start(self):
        """Hotkey-Callback: Aufnahme starten"""
        if not self.recorder_tab.is_recording:
            self.tabs.setCurrentWidget(self.recorder_tab)
            self.recorder_tab.start_recording()
    
    def on_hotkey_record_stop(self):
        """Hotkey-Callback: Aufnahme stoppen"""
        if self.recorder_tab.is_recording:
            self.recorder_tab.stop_recording()

    def on_hotkey_play_start(self, macro_id: int = -1):
        """Hotkey-Callback oder Overlay-Request: Wiedergabe starten. 
        Falls macro_id -1 ist, wird das aktuell ausgewählte Makro gestartet."""
        # Nur starten, wenn aktuell keine Wiedergabe läuft
        if not self.macro_tab.player.is_playing:
            if macro_id != -1:
                self.macro_tab.play_macro_by_id(macro_id)
            else:
                self.tabs.setCurrentWidget(self.macro_tab)
                self.macro_tab.play_macro()
        
    def on_hotkey_play_stop(self):
        """Hotkey-Callback: Wiedergabe stoppen"""
        if self.macro_tab.player.is_playing:
            self.macro_tab.stop_macro()
    
    def on_hotkey_emergency_stop(self):
        """Hotkey-Callback: Notfall-Stop (alles stoppen)"""
        self.emergency_stop()
    
    def emergency_stop(self):
        """Notfall-Stop: Stoppt alles"""
        # Aufnahme stoppen
        if self.recorder_tab.is_recording:
            self.recorder_tab.stop_recording()
        
        # Wiedergabe stoppen
        if self.macro_tab.player.is_playing:
            self.macro_tab.stop_macro()
        
        # Overlay aktualisieren
        self.overlay.set_macro_stopped()
        
        # Statusmeldung
        self.statusbar.showMessage("⚠️ NOTFALL-STOP aktiviert - Alle Aktionen gestoppt!", 5000)
    
    def toggle_overlay(self):
        """Togglet die Sichtbarkeit des Gaming-Overlays"""
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.set_click_through_off()
            self.overlay.show()
            self.overlay.raise_()
            self.overlay.activateWindow()
    
    def save_settings(self):
        """Speichert Einstellungen"""
        # Fensterposition und -größe speichern
        geo = self.geometry()
        self.db.set_setting('window_geometry', 
                           f"{geo.x()},{geo.y()},{geo.width()},{geo.height()}")
        
        # Aktives Profil speichern
        current_profile = self.profile_tab.get_selected_profile()
        if current_profile:
            self.db.set_setting('last_profile', str(current_profile))
    
    def show_hotkeys(self):
        """Zeigt Übersicht aller aktiven Hotkeys (global + Makros), Doppelte markiert."""
        from core.hotkey_manager import HotkeyManager
        entries = []  # (normalized, label)
        # Globale
        for key, label in [
            ("hotkey_record_start", "🎙️ Aufnahme starten"),
            ("hotkey_play_start", "▶️ Wiedergabe starten"),
            ("hotkey_record_stop", "⏹️ Aufnahme stoppen"),
            ("hotkey_play_stop", "⏹️ Wiedergabe stoppen"),
            ("emergency_stop_hotkey", "⚠️ Notfall-Stop"),
            ("pause_resume_hotkey", "⏸️ Pause/Resume"),
            ("overlay_toggle_hotkey", "🎮 Overlay ein/aus"),
            ("screenshot_hotkey", "📷 Screenshot"),
            ("macro_chain_hotkey", "⛓ Makro-Kette"),
            ("toggle_macro_hotkey", "🔄 Toggle-Makro"),
            ("video_start_hotkey", "▶ Video starten"),
            ("video_stop_hotkey", "⏹ Video stoppen"),
        ]:
            h = self.db.get_setting(key, "").strip()
            if h:
                entries.append((self.hotkey_manager.parse_hotkey(h), label))
        # Makro-Hotkeys (aktuelles Profil)
        profile_id = self.profile_tab.get_selected_profile()
        if profile_id:
            for macro in self.db.get_macros(profile_id):
                h = (macro.get("hotkey") or "").strip()
                if h:
                    entries.append((self.hotkey_manager.parse_hotkey(h), f"⚡ Makro: {macro['name']}"))
        # Duplikate finden
        seen = {}
        for norm, label in entries:
            seen[norm] = seen.get(norm, []) + [label]
        duplicates = {n for n, labels in seen.items() if len(labels) > 1}
        # HTML ausgeben
        html = "<h3>⌨️ Hotkey-Übersicht</h3><table style='margin-top:8px'>"
        for norm, label in entries:
            disp = HotkeyManager.format_hotkey_display(norm)
            warn = " <span style='color:red'>(mehrfach belegt!)</span>" if norm in duplicates else ""
            html += f"<tr><td>{label}</td><td><b>{disp}</b>{warn}</td></tr>"
        html += "</table><p style='margin-top:12px'><small>Globale Hotkeys wirken auch im Hintergrund. Nach Änderungen ggf. App neu starten.</small></p>"
        QMessageBox.information(self, "Hotkey-Übersicht", html)
    
    def show_about(self):
        """Zeigt Über-Dialog"""
        QMessageBox.about(
            self,
            f"Über {APP_NAME}",
            "<h2>" + APP_NAME + "</h2>"
            f"<p>Version {APP_VERSION}</p>"
            "<p>Professionelles Makro-Tool für Windows</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Aufnahme von Maus- und Tastaturaktionen</li>"
            "<li>Makro-Editor mit manueller Bearbeitung</li>"
            "<li>Mehrere Profile und Makros</li>"
            "<li>Globale Hotkeys</li>"
            "<li>Window-Detection für selektive Ausführung</li>"
            "<li>Schleifenwiederholung und Geschwindigkeitskontrolle</li>"
            "</ul>"
            f"<p>{APP_COPYRIGHT}</p>"
        )

    def check_for_update(self):
        """Prüft auf neue Version, zeigt bei Bedarf Fortschrittsdialog und lädt Update herunter."""
        update_available, server_version, download_url = get_update_info()

        frozen = getattr(sys, "frozen", False)
        if frozen:
            current_exe = Path(sys.executable)
            default_dir = current_exe.parent
            default_name = current_exe.name.replace(".exe", "_Update.exe")
        else:
            current_exe = None
            default_dir = Path.cwd()
            default_name = "AdvancedGaming_Update.exe"

        if not update_available:
            if server_version is None:
                msg = (
                    "Die Update-Prüfung ist fehlgeschlagen (Netzwerk oder Server nicht erreichbar).\n\n"
                    "Möchten Sie trotzdem die aktuelle EXE von der Webseite herunterladen?"
                )
            else:
                msg = (
                    f"Sie haben bereits die aktuelle Version (v{APP_VERSION}).\n\n"
                    "Möchten Sie die EXE trotzdem erneut herunterladen?"
                )
            reply = QMessageBox.question(
                self,
                "Update",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        else:
            reply = QMessageBox.question(
                self,
                "Update verfügbar",
                f"Version {server_version} ist verfügbar (Sie haben {APP_VERSION}).\n\nJetzt herunterladen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        default_path = default_dir / default_name
        save_path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Update herunterladen",
            str(default_path),
            "EXE Dateien (*.exe)",
        )
        if not save_path_str:
            return
        save_path = Path(save_path_str)

        # Fortschrittsdialog
        progress = QProgressDialog("Update wird heruntergeladen...", "Abbrechen", 0, 100, self)
        progress.setWindowTitle("Update")
        progress.setMinimumDuration(0)
        progress.setValue(0)

        class DownloadWorker(QObject):
            progress = pyqtSignal(int, int)
            finished = pyqtSignal(object)  # Optional[str] = Fehlermeldung oder None

            def run(self):
                err = download_file(
                    download_url,
                    save_path,
                    progress_callback=lambda loaded, total: self.progress.emit(loaded, total or 0),
                )
                self.finished.emit(err)

        thread = QThread()
        worker = DownloadWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(lambda loaded, total: self._update_progress_dialog(progress, loaded, total))
        worker.finished.connect(lambda err: self._on_download_finished(progress, thread, save_path, current_exe, frozen, err))
        worker.finished.connect(thread.quit)
        thread.start()

    def _update_progress_dialog(self, progress: QProgressDialog, loaded: int, total: int):
        if total > 0:
            progress.setMaximum(total)
            progress.setValue(loaded)
        else:
            progress.setMaximum(0)
            progress.setValue(0)

    def _on_download_finished(self, progress: QProgressDialog, thread: QThread, save_path: Path, current_exe, frozen: bool, error_msg):
        progress.close()
        thread.wait(2000)
        if error_msg:
            self.statusbar.showMessage("Fehler beim Update-Download", 5000)
            QMessageBox.critical(
                self,
                "Update fehlgeschlagen",
                f"Beim Herunterladen ist ein Fehler aufgetreten:\n{error_msg}\n\nBitte später erneut versuchen oder die EXE manuell von der Webseite laden.",
            )
            return
        self.statusbar.showMessage("Update-Download abgeschlossen", 5000)
        if not frozen:
            QMessageBox.information(
                self,
                "Update heruntergeladen",
                f"Die Datei wurde heruntergeladen.\n\nPfad: {save_path}\n\nDie Selbst-Aktualisierung funktioniert nur mit der EXE-Version.",
            )
            return
        if current_exe and save_path.parent != current_exe.parent:
            QMessageBox.information(
                self,
                "Update heruntergeladen",
                f"Die Datei wurde heruntergeladen.\n\nPfad: {save_path}\n\nFür die automatische Aktualisierung bitte in denselben Ordner wie die aktuelle EXE speichern.",
            )
            return
        # Selbst-Aktualisierung: Batch erstellen und starten
        updater_path = current_exe.parent / "advanced_gaming_updater.bat"
        batch_content = r"""@echo off
setlocal
set "OLD_EXE=%~1"
set "NEW_EXE=%~2"
:wait_move
move /Y "%NEW_EXE%" "%OLD_EXE%" >nul 2>&1
if errorlevel 1 (
  ping 127.0.0.1 -n 2 >nul
  goto wait_move
)
start "" "%OLD_EXE%"
del "%~f0"
endlocal
exit /b
"""
        try:
            updater_path.write_text(batch_content, encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Updater", f"Update-Hilfsdatei konnte nicht erstellt werden:\n{e}")
            return
        reply = QMessageBox.question(
            self,
            "Update anwenden",
            "Das Update wurde heruntergeladen. Jetzt installieren und neu starten?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", str(updater_path), str(current_exe), str(save_path)],
                shell=False,
            )
        except Exception as e:
            QMessageBox.critical(self, "Updater", f"Automatische Aktualisierung konnte nicht gestartet werden:\n{e}")
            return
        QMessageBox.information(
            self,
            "Update wird angewendet",
            "Die Anwendung wird für das Update geschlossen und startet anschließend neu.",
        )
        self.close()
    
    def closeEvent(self, event: QCloseEvent):
        """Wird beim Schließen des Fensters aufgerufen"""
        # Einstellungen speichern
        self.save_settings()
        
        # System Tray: Minimiere statt schließen (wenn aktiviert)
        minimize_to_tray = self.db.get_setting('minimize_to_tray', 'false') == 'true'
        
        if minimize_to_tray and not event.spontaneous():
            event.ignore()
            self.hide()
            self.system_tray.show_message(
                "Minimiert zur Taskleiste",
                "Advanced Gaming läuft im Hintergrund weiter",
                duration=2000
            )
            return
        
        # Overlay schließen
        self.overlay.close()
        
        # System Tray verstecken
        self.system_tray.hide()
        
        # API-Server stoppen
        self.stop_api_server()
        
        # Hotkey-Manager stoppen
        self.hotkey_manager.stop()
        
        # Window-Detector stoppen
        self.window_detector.stop_monitoring()
        
        # Scheduler stoppen
        self.scheduler_tab.scheduler.stop()
        
        # Video-Aufnahme stoppen
        if getattr(self, 'tools_tab', None) and getattr(self.tools_tab.recorder, 'is_recording', False):
            self.tools_tab.stop_video()
        
        # Statistiken speichern
        self.statistics_tab.stats_manager.save_statistics()
        
        self.log_manager.info("Anwendung beendet")
        
        event.accept()
    
    def show_from_tray(self):
        """Zeigt Fenster vom System-Tray"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def execute_macro_from_tray(self, macro_id: int, macro_name: str):
        """Führt Makro vom System-Tray aus"""
        # Zeige Notification
        self.system_tray.notify_macro_started(macro_name)
        
        # Führe Makro aus (über Macro-Tab)
        self.macro_tab.play_macro_by_id(macro_id)
    
    def execute_scheduled_macro(self, macro_id: int, macro_name: str):
        """Führt geplantes Makro vom Scheduler aus"""
        self.log_manager.info(f"Führe geplantes Makro aus: {macro_name}")
        self.system_tray.notify_macro_started(macro_name)
        
        # TODO: Implementiere direkte Makro-Ausführung
        # Aktuell über Macro-Tab
        self.macro_tab.play_macro_by_id(macro_id)
        if hasattr(self, 'overlay'):
            self.overlay.close()
        
        # Manager stoppen
        self.hotkey_manager.stop()
        self.window_detector.stop_monitoring()
        
        # Recorder stoppen falls aktiv
        if hasattr(self.recorder_tab, 'recorder') and self.recorder_tab.recorder.is_recording:
            self.recorder_tab.stop_recording()
        
        # Player stoppen falls aktiv
        if hasattr(self.macro_tab, 'player') and self.macro_tab.player.is_playing:
            self.macro_tab.player.stop()

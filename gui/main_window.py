"""
Hauptfenster der Anwendung
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QTabWidget, QPushButton, QToolBar, QStatusBar,
                              QMessageBox, QLabel, QFileDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QCloseEvent

import sys
from pathlib import Path
import urllib.request
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
from database import DatabaseManager
from core import HotkeyManager, WindowDetector
from core.logging_system import LogManager
from core.system_tray import SystemTrayManager
from core.version import APP_NAME, APP_VERSION, APP_COPYRIGHT

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
        
        # Gaming-Overlay
        self.overlay = GamingOverlay()
        self.overlay.stop_all_requested.connect(self.emergency_stop)
        
        # Tabs initialisieren (vor init_ui!)
        self.profile_tab = ProfileTab(self.db, self.hotkey_manager)
        self.macro_tab = MacroTab(self.db, self.hotkey_manager, self.window_detector)
        self.recorder_tab = RecorderTab(self.db)
        self.log_viewer_tab = LogViewerWidget()
        self.scheduler_tab = SchedulerTab(self.db)
        self.statistics_tab = StatisticsTab(self.db)
        self.template_manager_tab = TemplateManagerWidget()
        self.settings_tab = SettingsTab(self.db, self.hotkey_manager)
        
        # System Tray
        self.system_tray = SystemTrayManager(self)
        self.system_tray.show_window.connect(self.show_from_tray)
        self.system_tray.quit_app.connect(self.close)
        self.system_tray.execute_macro.connect(self.execute_macro_from_tray)
        self.system_tray.show()
        
        self.init_ui()
        self.setup_statusbar()
        self.load_settings()
        
        # Hotkey-Manager starten
        self.hotkey_manager.start()
        
        # Globale System-Hotkeys registrieren
        self.register_global_hotkeys()
        
        # Window-Überwachung starten
        self.window_detector.start_monitoring(
            on_window_change=self.on_window_changed
        )
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - Professional Macro Tool")
        self.setGeometry(100, 100, 1200, 800)
        
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
        self.tabs.addTab(self.settings_tab, "⚙️ Einstellungen")
        
        layout.addWidget(self.tabs)
        
        # Toolbar erstellen (nach den Tabs!)
        self.create_toolbar()
        
        # Verbindungen
        self.profile_tab.profile_selected.connect(self.on_profile_selected)
        self.recorder_tab.macro_saved.connect(self.macro_tab.refresh_macros)
        
        # Overlay-Verbindungen
        self.recorder_tab.recording_started.connect(lambda: self.overlay.set_recording(True))
        self.recorder_tab.recording_stopped.connect(lambda: self.overlay.set_recording(False))
        self.macro_tab.playback_started.connect(self.on_playback_started)
        self.macro_tab.playback_stopped.connect(lambda: self.overlay.set_macro_stopped())
        
        # Scheduler-Verbindungen
        self.scheduler_tab.execute_macro.connect(self.execute_scheduled_macro)
        self.recorder_tab.macro_saved.connect(self.macro_tab.refresh_macros)
        
        # Overlay-Verbindungen
        self.recorder_tab.recording_started.connect(lambda: self.overlay.set_recording(True))
        self.recorder_tab.recording_stopped.connect(lambda: self.overlay.set_recording(False))
        self.macro_tab.playback_started.connect(self.on_playback_started)
        self.macro_tab.playback_stopped.connect(lambda: self.overlay.set_macro_stopped())
    
    def create_toolbar(self):
        """Erstellt die Toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Neues Profil
        new_profile_action = QAction("📁 Neues Profil", self)
        new_profile_action.setShortcut(QKeySequence("Ctrl+N"))
        new_profile_action.triggered.connect(self.profile_tab.create_profile)
        toolbar.addAction(new_profile_action)
        
        toolbar.addSeparator()
        
        # Neues Makro
        new_macro_action = QAction("⚡ Neues Makro", self)
        new_macro_action.setShortcut(QKeySequence("Ctrl+M"))
        new_macro_action.triggered.connect(self.macro_tab.create_macro)
        toolbar.addAction(new_macro_action)
        
        # Aufnahme starten
        record_action = QAction("🎙️ Aufnahme", self)
        record_action.setShortcut(QKeySequence("Ctrl+R"))
        record_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.recorder_tab))
        toolbar.addAction(record_action)
        
        toolbar.addSeparator()
        
        # Einstellungen
        settings_action = QAction("⚙️ Einstellungen", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.settings_tab))
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        # Gaming-Overlay
        overlay_action = QAction("🎮 Overlay", self)
        overlay_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        overlay_action.triggered.connect(self.toggle_overlay)
        toolbar.addAction(overlay_action)
        
        # Hotkeys anzeigen
        hotkeys_action = QAction("⌨️ Hotkeys", self)
        hotkeys_action.triggered.connect(self.show_hotkeys)
        toolbar.addAction(hotkeys_action)
        
        # Über
        about_action = QAction("ℹ️ Über", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

        toolbar.addSeparator()

        # Update prüfen / herunterladen
        update_action = QAction("🔄 Update", self)
        update_action.triggered.connect(self.check_for_update)
        toolbar.addAction(update_action)
    
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
    
    def on_profile_selected(self, profile_id: int):
        """Callback wenn ein Profil ausgewählt wurde"""
        self.macro_tab.load_profile(profile_id)
        profile = self.db.get_profile(profile_id)
        if profile:
            self.statusbar.showMessage(f"Profil geladen: {profile['name']}")
    
    def on_playback_started(self, macro_name: str):
        """Wird aufgerufen, wenn Makro-Wiedergabe startet"""
        self.overlay.set_macro_running(macro_name)
    
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
        
        # Overlay-Toggle
        overlay_hotkey = self.db.get_setting('overlay_toggle_hotkey', 'ctrl+shift+o')
        if overlay_hotkey:
            normalized = self.hotkey_manager.parse_hotkey(overlay_hotkey)
            self.hotkey_manager.register_hotkey(normalized, self.toggle_overlay)
    
    def on_hotkey_record_start(self):
        """Hotkey-Callback: Aufnahme starten"""
        if not self.recorder_tab.is_recording:
            self.tabs.setCurrentWidget(self.recorder_tab)
            self.recorder_tab.start_recording()
    
    def on_hotkey_record_stop(self):
        """Hotkey-Callback: Aufnahme stoppen"""
        if self.recorder_tab.is_recording:
            self.recorder_tab.stop_recording()

    def on_hotkey_play_start(self):
        """Hotkey-Callback: Wiedergabe starten"""
        # Nur starten, wenn aktuell keine Wiedergabe läuft
        if not self.macro_tab.player.is_playing:
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
        """Zeigt aktive Hotkeys an"""
        hotkeys_info = "<h3>⌨️ Aktive Globale Hotkeys</h3>"
        
        hotkey_record_start = self.db.get_setting('hotkey_record_start', '')
        hotkey_play_start = self.db.get_setting('hotkey_play_start', '')
        hotkey_record_stop = self.db.get_setting('hotkey_record_stop', '')
        hotkey_play_stop = self.db.get_setting('hotkey_play_stop', '')
        emergency_stop = self.db.get_setting('emergency_stop_hotkey', '')
        
        if not any([hotkey_record_start, hotkey_play_start, hotkey_record_stop, hotkey_play_stop, emergency_stop]):
            hotkeys_info += "<p><i>Keine globalen Hotkeys konfiguriert.</i></p>"
            hotkeys_info += "<p>Gehen Sie zu <b>Einstellungen</b> um Hotkeys zu konfigurieren.</p>"
        else:
            hotkeys_info += "<table style='margin-top: 10px;'>"
            
            if hotkey_record_start:
                hotkeys_info += f"<tr><td>🎙️ Aufnahme starten:</td><td><b>{hotkey_record_start}</b></td></tr>"

            if hotkey_play_start:
                hotkeys_info += f"<tr><td>▶️ Wiedergabe starten:</td><td><b>{hotkey_play_start}</b></td></tr>"
            
            if hotkey_record_stop:
                hotkeys_info += f"<tr><td>⏹️ Aufnahme stoppen:</td><td><b>{hotkey_record_stop}</b></td></tr>"
            
            if hotkey_play_stop:
                hotkeys_info += f"<tr><td>⏹️ Wiedergabe stoppen:</td><td><b>{hotkey_play_stop}</b></td></tr>"
            
            if emergency_stop:
                hotkeys_info += f"<tr><td>⚠️ Notfall-Stop (Alles):</td><td><b>{emergency_stop}</b></td></tr>"
            
            hotkeys_info += "</table>"
            
            hotkeys_info += "<p style='margin-top: 15px;'><small><b>Hinweis:</b> Diese Hotkeys funktionieren global, auch wenn die Anwendung nicht im Vordergrund ist.</small></p>"
        
        QMessageBox.information(self, "Globale Hotkeys", hotkeys_info)
    
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
        """Lädt die aktuelle Version von der festen Update-URL herunter.

        Wenn die Anwendung als EXE läuft und in denselben Ordner heruntergeladen
        wird, kann sie sich nach dem Download selbst aktualisieren und neu
        starten.
        """
        UPDATE_URL = "https://drenor.de/programme/autoclicker/AdvancedAutoClicker.exe"

        # Prüfen, ob wir als PyInstaller-EXE laufen
        frozen = getattr(sys, "frozen", False)
        if frozen:
            current_exe = Path(sys.executable)
            default_dir = current_exe.parent
            default_name = current_exe.name.replace(".exe", "_Update.exe")
        else:
            # Entwicklungsmodus: in aktuelles Verzeichnis laden
            current_exe = None
            default_dir = Path.cwd()
            default_name = "AdvancedAutoClicker_Update.exe"

        default_path = default_dir / default_name
        save_path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Update herunterladen",
            str(default_path),
            "EXE Dateien (*.exe)"
        )

        if not save_path_str:
            return  # Benutzer hat abgebrochen

        save_path = Path(save_path_str)

        try:
            self.statusbar.showMessage("Lade Update herunter...")
            # Einfacher Download ohne Fortschrittsbalken
            urllib.request.urlretrieve(UPDATE_URL, save_path)
            self.statusbar.showMessage("Update-Download abgeschlossen", 5000)
        except Exception as e:
            self.statusbar.showMessage("Fehler beim Update-Download", 5000)
            QMessageBox.critical(
                self,
                "Update fehlgeschlagen",
                f"Beim Herunterladen des Updates ist ein Fehler aufgetreten:\n{e}"
            )
            return

        # Wenn nicht als EXE (Entwicklungsmodus): nur informieren
        if not frozen:
            QMessageBox.information(
                self,
                "Update heruntergeladen",
                f"Die aktuelle Version wurde erfolgreich heruntergeladen.\n\n"
                f"Pfad: {save_path}\n\n"
                f"Die Selbst-Aktualisierung funktioniert nur mit der EXE-Version."
            )
            return

        # Ab hier: EXE-Version -> Selbst-Aktualisierung nur, wenn in selben Ordner
        if save_path.parent != current_exe.parent:
            QMessageBox.information(
                self,
                "Update heruntergeladen",
                f"Die aktuelle Version wurde erfolgreich heruntergeladen.\n\n"
                f"Pfad: {save_path}\n\n"
                f"Für die automatische Aktualisierung bitte in denselben Ordner wie die aktuelle EXE speichern."
            )
            return

        # Updater-Skript im gleichen Ordner erstellen
        updater_path = current_exe.parent / "autoclicker_updater.bat"

        batch_content = r"""@echo off
setlocal
set "OLD_EXE=%~1"
set "NEW_EXE=%~2"

:wait_move
move /Y "%NEW_EXE%" "%OLD_EXE%" >nul 2>&1
if errorlevel 1 (
  REM Datei ist wahrscheinlich noch gesperrt -> kurz warten und erneut versuchen
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
            QMessageBox.critical(
                self,
                "Updater konnte nicht erstellt werden",
                f"Die Update-Hilfsdatei konnte nicht erstellt werden:\n{e}"
            )
            return

        # Benutzer informieren und Updater starten
        reply = QMessageBox.question(
            self,
            "Update anwenden",
            "Das Update wurde heruntergeladen und kann jetzt installiert werden.\n\n"
            "Das Programm wird geschlossen und mit der neuen Version neu gestartet.\n\n"
            "Möchten Sie fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Updater-Batch in eigenem Prozess starten
            subprocess.Popen(
                ["cmd", "/c", "start", "", str(updater_path), str(current_exe), str(save_path)],
                shell=False,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Updater konnte nicht gestartet werden",
                f"Die automatische Aktualisierung konnte nicht gestartet werden:\n{e}"
            )
            return

        # Anwendung beenden, damit der Updater die EXE ersetzen kann
        QMessageBox.information(
            self,
            "Update wird angewendet",
            "Die Anwendung wird jetzt für das Update geschlossen.\n"
            "Sie startet anschließend automatisch neu."
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
                "Advanced Auto Clicker läuft im Hintergrund weiter",
                duration=2000
            )
            return
        
        # Overlay schließen
        self.overlay.close()
        
        # System Tray verstecken
        self.system_tray.hide()
        
        # Hotkey-Manager stoppen
        self.hotkey_manager.stop()
        
        # Window-Detector stoppen
        self.window_detector.stop_monitoring()
        
        # Scheduler stoppen
        self.scheduler_tab.scheduler.stop()
        
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
        
        event.accept()

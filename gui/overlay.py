"""
Gaming-Overlay – Transparentes Overlay mit Echtzeit-Status und neuen Funktionen
Neu: Fortschrittsanzeige, Kompakt-Modus, Pin-Position, Click-through, Letzte Ausführung
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSlider, QProgressBar, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QFont, QFontDatabase, QPaintEvent
import time


class GamingOverlay(QWidget):
    """Transparentes Overlay: Makro-Status, Fortschritt, Quick-Actions, Kompakt-Modus, Pin, Click-through"""

    toggle_visibility = pyqtSignal()
    stop_all_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.is_dragging = False
        self.drag_position = QPoint()
        self.current_macro = None
        self.macro_start_time = None
        self.opacity_level = 0.92
        self.is_compact = False
        self.click_through = False
        self.pinned_corner = None  # None, 'tl', 'tr', 'bl', 'br'
        self.last_run_name = None
        self.last_run_duration = 0.0

        # Fortschritt
        self.playback_progress = 0.0
        self.playback_loop = 0
        self.playback_action = 0

        # FPS + Ressourcen
        self._fps_frame_count = 0
        self._fps_last_time = time.perf_counter()
        self.current_fps = 0
        self._resource_timer = 0.0
        self.current_cpu = 0
        self.current_ram = 0

        self.game_mode = False  # Weniger Updates (2–5 Hz) für bessere Performance
        self.is_paused = False
        self.countdown_seconds = 0
        self._countdown_last_tick = 0.0
        self.is_minimal = False
        self.skill_rotation_list = []  # Nächste N Aktionen/Skills (Strings)
        self.status_bar_percent = None  # 0–100 oder None (aus)
        self.status_bar_color = "0,200,100"
        self.sound_on_end = False

        self.init_ui()
        self.setup_timer()

    # Mindesthöhe, damit auf Displays mit großer Rahmenhöhe (z. B. TV) keine setGeometry-Warnung entsteht
    SAFE_MIN_HEIGHT = 360

    def init_ui(self):
        self.setMinimumSize(280, self.SAFE_MIN_HEIGHT)
        self.setMaximumSize(480, 420)
        self.resize(340, self.SAFE_MIN_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName("overlayContainer")
        self.container.setCursor(Qt.CursorShape.ArrowCursor)
        self.update_style()

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 10, 12, 10)
        self.content_layout.setSpacing(8)

        self.sep1 = QFrame()
        self.sep1.setFrameShape(QFrame.Shape.HLine)
        self.sep1.setFixedHeight(1)
        self.sep1.setStyleSheet("background-color: rgba(255,255,255,0.15);")
        self.content_layout.addWidget(self.sep1)

        # ---- Status ----
        self.status_label = QLabel("Bereit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        self.status_label.setFont(f)
        self.content_layout.addWidget(self.status_label)

        self.macro_label = QLabel("Kein Makro aktiv")
        self.macro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.macro_label.setObjectName("macroLabel")
        self.macro_label.setWordWrap(True)
        self.content_layout.addWidget(self.macro_label)

        # ---- Fortschritt (neu) ----
        self.progress_widget = QFrame()
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 4, 0, 4)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(0,200,200,0.4);
                border-radius: 4px;
                text-align: center;
                background: rgba(0,0,0,0.4);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00cccc, stop:1 #0088aa);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        self.lbl_loop_action = QLabel("Loop 0, Aktion 0")
        self.lbl_loop_action.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loop_action.setStyleSheet("color: rgba(255,220,100,0.95); font-size: 9pt; font-family: monospace;")
        progress_layout.addWidget(self.lbl_loop_action)
        self.progress_widget.setVisible(False)
        self.content_layout.addWidget(self.progress_widget)

        # ---- Timer + Letzte Ausführung (neu) ----
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setObjectName("timerLabel")
        self.content_layout.addWidget(self.timer_label)

        self.last_run_label = QLabel("")
        self.last_run_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_run_label.setStyleSheet("color: rgba(180,180,180,0.9); font-size: 8pt;")
        self.last_run_label.setWordWrap(True)
        self.content_layout.addWidget(self.last_run_label)

        # ---- FPS + Ressourcen (dezent) ----
        self.perf_label = QLabel("")
        self.perf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.perf_label.setStyleSheet("color: rgba(140,140,140,0.8); font-size: 7pt; font-family: monospace;")
        self.content_layout.addWidget(self.perf_label)

        # ---- Letzter Log (neu) ----
        self.mini_log_label = QLabel("")
        self.mini_log_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mini_log_label.setStyleSheet("color: rgba(0, 200, 255, 0.7); font-size: 7pt; font-style: italic;")
        self.mini_log_label.setWordWrap(True)
        self.mini_log_label.setMaximumHeight(30)
        self.content_layout.addWidget(self.mini_log_label)

        # ---- Countdown (Cooldown/Skill) ----
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("color: rgba(255,200,100,0.95); font-size: 9pt;")
        self.countdown_label.setVisible(False)
        self.content_layout.addWidget(self.countdown_label)

        # ---- Skill-Rotation (nächste N Aktionen) ----
        self.skill_rotation_label = QLabel("")
        self.skill_rotation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.skill_rotation_label.setStyleSheet("color: rgba(200,220,255,0.9); font-size: 8pt;")
        self.skill_rotation_label.setWordWrap(True)
        self.skill_rotation_label.setVisible(False)
        self.content_layout.addWidget(self.skill_rotation_label)

        # ---- Optionale farbige Status-Leiste (z. B. HP) ----
        self.status_bar_widget = QProgressBar()
        self.status_bar_widget.setFixedHeight(6)
        self.status_bar_widget.setMinimum(0)
        self.status_bar_widget.setMaximum(100)
        self.status_bar_widget.setValue(100)
        self.status_bar_widget.setTextVisible(False)
        self.status_bar_widget.setStyleSheet("""
            QProgressBar { background: rgba(0,0,0,0.5); border-radius: 3px; }
            QProgressBar::chunk { background: rgba(0,200,100,0.9); border-radius: 2px; }
        """)
        self.status_bar_widget.setVisible(False)
        self.content_layout.addWidget(self.status_bar_widget)

        # ---- Aktives Fenster ----
        self.window_label = QLabel("Fenster: —")
        self.window_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window_label.setStyleSheet("color: rgba(160,160,160,0.85); font-size: 8pt;")
        self.window_label.setWordWrap(True)
        self.content_layout.addWidget(self.window_label)

        self.sep2 = QFrame()
        self.sep2.setFrameShape(QFrame.Shape.HLine)
        self.sep2.setFixedHeight(1)
        self.sep2.setStyleSheet("background-color: rgba(255,255,255,0.15);")
        self.content_layout.addWidget(self.sep2)

        # ---- Quick-Actions ----
        self.quick_frame = self.create_quick_buttons()
        self.content_layout.addWidget(self.quick_frame)

        # ---- Optionen: Transparenz, Kompakt, Pin, Click-through ----
        self.options_frame = self.create_options()
        self.content_layout.addWidget(self.options_frame)

        self.content_layout.addStretch()
        layout.addWidget(self.container)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        header = self.create_header()
        self.container_layout.addWidget(header)
        self.container_layout.addWidget(self.content)

        self.apply_styles()

    def create_header(self):
        header = QFrame()
        header.setObjectName("overlayHeader")
        header.setCursor(Qt.CursorShape.SizeAllCursor)
        header.setFixedHeight(36)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(10, 6, 8, 6)
        lay.setSpacing(8)

        title = QLabel("Advanced Gaming")
        title.setStyleSheet("color: rgba(0,255,255,0.95); font-weight: bold; font-size: 10pt;")
        lay.addWidget(title)
        lay.addStretch()

        self.btn_compact = QPushButton("▸")
        self.btn_compact.setFixedSize(26, 26)
        self.btn_compact.setToolTip("Kompakt-Modus")
        self.btn_compact.clicked.connect(self.toggle_compact)
        lay.addWidget(self.btn_compact)

        self.btn_minimal = QPushButton("M")
        self.btn_minimal.setFixedSize(26, 26)
        self.btn_minimal.setToolTip("Minimal (nur Status)")
        self.btn_minimal.setCheckable(True)
        self.btn_minimal.clicked.connect(self.toggle_minimal)
        lay.addWidget(self.btn_minimal)

        btn_min = QPushButton("−")
        btn_min.setFixedSize(26, 26)
        btn_min.setToolTip("Minimieren")
        btn_min.clicked.connect(self.hide)
        lay.addWidget(btn_min)

        btn_close = QPushButton("×")
        btn_close.setFixedSize(26, 26)
        btn_close.setToolTip("Schließen")
        btn_close.clicked.connect(self.hide)
        lay.addWidget(btn_close)

        header.mousePressEvent = self.start_drag
        header.mouseMoveEvent = self.do_drag
        header.mouseReleaseEvent = self.end_drag
        return header

    def create_quick_buttons(self):
        frame = QFrame()
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 6, 0, 4)
        lay.setSpacing(8)

        self.btn_pause = QPushButton("⏸ PAUSE")
        self.btn_pause.setObjectName("pauseButton")
        self.btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_pause.setVisible(False)
        lay.addWidget(self.btn_pause)

        btn_stop = QPushButton("⏹ STOP")
        btn_stop.setObjectName("stopButton")
        btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stop.clicked.connect(self.stop_all_requested.emit)
        lay.addWidget(btn_stop)

        return frame

    def _on_pause_clicked(self):
        if self.is_paused:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()

    def set_paused(self, paused: bool):
        self.is_paused = paused
        if paused:
            self.status_label.setText("Pausiert")
            self.status_label.setStyleSheet("color: rgba(255, 200, 0, 0.95); padding: 4px; font-weight: bold;")
            self.btn_pause.setText("▶ WEITER")
        else:
            if self.current_macro:
                self.status_label.setText("Läuft")
                self.status_label.setStyleSheet("color: rgba(0, 255, 150, 0.95); padding: 4px; font-weight: bold;")
            self.btn_pause.setText("⏸ PAUSE")

    def create_options(self):
        frame = QFrame()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(6)

        # Transparenz
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Transparenz:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(40)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self.opacity_level * 100))
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        row1.addWidget(self.opacity_slider)
        lay.addLayout(row1)

        # Pin + Click-through
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Pin:"))
        self.pin_buttons = {}
        for corner, tip in [("tl", "Oben links"), ("tr", "Oben rechts"), ("bl", "Unten links"), ("br", "Unten rechts")]:
            btn = QPushButton(corner.upper())
            btn.setFixedSize(28, 22)
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=corner: self.pin_to_corner(c))
            self.pin_buttons[corner] = btn
            row2.addWidget(btn)
        row2.addStretch()
        self.chk_click_through = QPushButton("Durchklicken")
        self.chk_click_through.setCheckable(True)
        self.chk_click_through.setToolTip("Mausklicks durchlassen (zum Deaktivieren Overlay-Hotkey nutzen)")
        self.chk_click_through.clicked.connect(self.toggle_click_through)
        row2.addWidget(self.chk_click_through)
        lay.addLayout(row2)

        return frame

    def apply_styles(self):
        self.container.setStyleSheet(f"""
            #overlayContainer {{
                background-color: rgba(18, 22, 28, {self.opacity_level});
                border: 1px solid rgba(0, 220, 220, 0.35);
                border-radius: 12px;
            }}
            #overlayHeader {{
                background-color: rgba(0, 0, 0, 0.35);
                border-radius: 10px 10px 0 0;
            }}
            #statusLabel {{ color: rgba(0, 255, 200, 0.95); padding: 4px; }}
            #macroLabel {{ color: rgba(255, 255, 255, 0.9); font-size: 10pt; }}
            #timerLabel {{ color: rgba(255, 200, 80, 0.95); font-size: 11pt; font-family: monospace; }}
            #pauseButton {{
                background-color: rgba(200, 150, 0, 0.85);
                color: white;
                border: 1px solid rgba(255, 220, 0, 0.6);
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 9pt;
            }}
            #pauseButton:hover {{ background-color: rgba(220, 170, 0, 0.95); }}
            #stopButton {{
                background-color: rgba(200, 50, 50, 0.85);
                color: white;
                border: 1px solid rgba(255,80,80,0.6);
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 9pt;
            }}
            #stopButton:hover {{ background-color: rgba(220, 60, 60, 0.95); }}
            QPushButton {{
                background-color: rgba(60, 70, 90, 0.8);
                color: rgba(220, 220, 220, 0.95);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                min-height: 20px;
            }}
            QPushButton:hover {{ background-color: rgba(80, 90, 110, 0.9); }}
            QPushButton:checked {{ background-color: rgba(0, 180, 200, 0.5); }}
            QSlider::groove:horizontal {{
                border: none;
                height: 5px;
                background: rgba(255,255,255,0.15);
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: rgba(0, 220, 220, 0.9);
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
        """)

    def update_style(self):
        self.apply_styles()

    def setup_timer(self):
        # Normal: ~60 Hz; Spiel-Modus: ~5 Hz (weniger CPU-Last)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self._start_timer()

    def _start_timer(self):
        interval = 200 if self.game_mode else 16
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
            self.update_timer.start(interval)

    def set_game_mode(self, enabled: bool):
        """Spiel-Modus: Overlay-Updates auf 2–5 Hz reduzieren (weniger CPU)."""
        self.game_mode = enabled
        self._start_timer()

    def set_countdown(self, seconds: int):
        """Countdown-Anzeige (z. B. Cooldown): Zeigt 'Nächster Skill in Xs' bis 0."""
        self.countdown_seconds = max(0, int(seconds))
        self._countdown_last_tick = time.time()
        if self.countdown_seconds > 0:
            self.countdown_label.setText(f"Nächster Skill in {self.countdown_seconds}s")
            self.countdown_label.setVisible(True)
        else:
            self.countdown_label.setVisible(False)

    def set_active_window(self, title: str, process: str = ""):
        """Aktives Fenster/Spiel für Overlay-Anzeige setzen."""
        text = title or "—"
        if process:
            suffix = " (" + process + ")"
            text = (text[:40] + suffix) if len(text) > 40 else (text + suffix)
        self.window_label.setText("Fenster: " + text)

    def set_skill_rotation(self, action_names: list):
        """Nächste N Aktionen/Skills für die Anzeige setzen (z. B. ['Skill 1', 'Skill 2', 'Skill 3'])."""
        self.skill_rotation_list = list(action_names)[:10]
        if self.skill_rotation_list:
            self.skill_rotation_label.setText("Nächste: " + " → ".join(self.skill_rotation_list[:5]))
            self.skill_rotation_label.setVisible(not self.is_minimal)
        else:
            self.skill_rotation_label.setVisible(False)

    def set_status_bar(self, percent: float, color: str = "0,200,100"):
        """Optionale farbige Status-Leiste (0–100). Bei percent None ausblenden."""
        if percent is None:
            self.status_bar_percent = None
            self.status_bar_widget.setVisible(False)
            return
        self.status_bar_percent = max(0, min(100, float(percent)))
        self.status_bar_color = color
        self.status_bar_widget.setValue(int(self.status_bar_percent))
        self.status_bar_widget.setStyleSheet(f"""
            QProgressBar {{ background: rgba(0,0,0,0.5); border-radius: 3px; }}
            QProgressBar::chunk {{ background: rgba({color},0.9); border-radius: 2px; }}
        """)
        self.status_bar_widget.setVisible(not self.is_minimal)

    def set_sound_on_end(self, enabled: bool):
        """Sound bei Makro-Ende aktivieren/deaktivieren."""
        self.sound_on_end = bool(enabled)

    def paintEvent(self, event: QPaintEvent):
        """Zählt jede tatsächliche Bildaktualisierung für echte FPS."""
        self._fps_frame_count += 1
        super().paintEvent(event)

    def update_display(self):
        if self.macro_start_time is not None and not self.is_paused:
            elapsed = time.time() - self.macro_start_time
            m, s = int(elapsed // 60), int(elapsed % 60)
            self.timer_label.setText(f"{m:02d}:{s:02d}")

        # Countdown: jede Sekunde dekrementieren
        t = time.time()
        if self.countdown_seconds > 0 and t - self._countdown_last_tick >= 1.0:
            self._countdown_last_tick = t
            self.countdown_seconds -= 1
            if self.countdown_seconds <= 0:
                self.countdown_label.setVisible(False)
            else:
                self.countdown_label.setText(f"Nächster Skill in {self.countdown_seconds}s")
                self.countdown_label.setVisible(True)
        elif self.countdown_seconds > 0:
            self.countdown_label.setText(f"Nächster Skill in {self.countdown_seconds}s")
            self.countdown_label.setVisible(True)

        # FPS: alle 1 s aus gemalten Frames berechnen
        t_perf = time.perf_counter()
        if t_perf - self._fps_last_time >= 1.0:
            self.current_fps = self._fps_frame_count
            self._fps_frame_count = 0
            self._fps_last_time = t_perf
            
            # Ressourcen-Check (CPU/RAM) alle 2 Sekunden
            if t_perf - self._resource_timer >= 2.0:
                self._resource_timer = t_perf
                try:
                    import os
                    if hasattr(os, 'getloadavg'): # Linux/macOS
                        self.current_cpu = int(os.getloadavg()[0] * 10) 
                    else:
                        # Windows Alternative: sehr einfach (nur Platzhalter oder echte API falls nötig)
                        # Wir lassen es bei 0 oder nutzen eine einfache Methode falls psutil fehlt
                        pass
                except Exception:
                    pass

        perf_text = f"FPS: {self.current_fps}"
        if self.current_cpu > 0:
            perf_text += f" | CPU: {self.current_cpu}%"
        self.perf_label.setText(perf_text if self.current_fps else "")
        
        if self.isVisible():
            self.update()

    def set_mini_log(self, message: str):
        """Zeigt eine kurze Nachricht (Log) im Overlay."""
        self.mini_log_label.setText(message[:50] + ("..." if len(message) > 50 else ""))
        QTimer.singleShot(3000, lambda: self.mini_log_label.setText("") if self.mini_log_label.text() == message[:50] else None)

    def set_macro_running(self, macro_name: str):
        self.current_macro = macro_name
        self.macro_start_time = time.time()
        self.status_label.setText("Läuft")
        self.status_label.setStyleSheet("color: rgba(0, 255, 150, 0.95); padding: 4px; font-weight: bold;")
        self.macro_label.setText(macro_name)
        self.progress_bar.setValue(0)
        self.lbl_loop_action.setText("Loop 0, Aktion 0")
        self.progress_widget.setVisible(not self.is_minimal)
        self.btn_pause.setVisible(True)
        self.set_paused(False)
        self.set_mini_log(f"Starte: {macro_name}")

    def set_playback_progress(self, progress: float, loop: int, action: int):
        self.playback_progress = progress
        self.playback_loop = loop
        self.playback_action = action
        self.progress_bar.setValue(int(progress))
        self.lbl_loop_action.setText(f"Loop {loop}, Aktion {action}")
        self.btn_pause.setVisible(True)

    def set_macro_stopped(self):
        if self.current_macro and self.macro_start_time is not None:
            self.last_run_name = self.current_macro
            self.last_run_duration = time.time() - self.macro_start_time
            m, s = int(self.last_run_duration // 60), int(self.last_run_duration % 60)
            self.last_run_label.setText(f"Letztes: {self.last_run_name} – {m:02d}:{s:02d}")
            if self.sound_on_end:
                try:
                    import sys
                    if sys.platform == "win32":
                        import winsound
                        winsound.Beep(440, 150)
                except Exception:
                    pass
        self.current_macro = None
        self.macro_start_time = None
        self.status_label.setText("Bereit")
        self.status_label.setStyleSheet("color: rgba(0, 255, 220, 0.95); padding: 4px; font-weight: bold;")
        self.macro_label.setText("Kein Makro aktiv")
        self.timer_label.setText("00:00")
        self.progress_widget.setVisible(False)
        self.progress_bar.setValue(0)
        self.lbl_loop_action.setText("Loop 0, Aktion 0")
        self.btn_pause.setVisible(False)
        self.set_paused(False)

    def set_recording(self, is_recording: bool):
        if is_recording:
            self.status_label.setText("Aufnahme")
            self.status_label.setStyleSheet("color: rgba(255, 80, 80, 0.95); padding: 4px; font-weight: bold;")
            self.macro_label.setText("Makro wird aufgenommen…")
            self.macro_start_time = time.time()
            self.progress_widget.setVisible(False)
        else:
            self.set_macro_stopped()

    def on_opacity_changed(self, value: int):
        self.opacity_level = value / 100.0
        self.update_style()

    def toggle_compact(self):
        if self.is_minimal:
            self.toggle_minimal()
        self.is_compact = not self.is_compact
        if self.is_compact:
            self.content.setVisible(False)
            self.setMaximumHeight(48)
            self.resize(self.width(), 48)
        else:
            self.setMaximumHeight(420)
            self.resize(self.width(), self.SAFE_MIN_HEIGHT)
            self.content.setVisible(True)
            self._update_minimal_visibility()
        if hasattr(self, 'btn_compact'):
            self.btn_compact.setText("▾" if self.is_compact else "▸")

    def toggle_minimal(self):
        """Minimal-Ansicht: nur Status, Makroname und Countdown."""
        self.is_minimal = not self.is_minimal
        if hasattr(self, 'btn_minimal'):
            self.btn_minimal.setChecked(self.is_minimal)
        if self.is_minimal:
            self.setMaximumWidth(400)
            self.resize(min(self.width(), 400), self.height())
        else:
            self.setMaximumWidth(480)
        self._update_minimal_visibility()

    def _update_minimal_visibility(self):
        if not hasattr(self, 'progress_widget'):
            return
        show = not self.is_minimal
        self.sep1.setVisible(show)
        self.progress_widget.setVisible(show and self.current_macro is not None)
        self.timer_label.setVisible(show)
        self.last_run_label.setVisible(show)
        self.perf_label.setVisible(show)
        self.window_label.setVisible(show)
        self.sep2.setVisible(show)
        self.quick_frame.setVisible(show)
        self.options_frame.setVisible(show)
        self.countdown_label.setVisible(self.countdown_seconds > 0)
        self.skill_rotation_label.setVisible(show and len(self.skill_rotation_list) > 0)
        self.status_bar_widget.setVisible(show and self.status_bar_percent is not None)

    def pin_to_corner(self, corner: str):
        self.pinned_corner = corner if self.pinned_corner != corner else None
        for c, btn in self.pin_buttons.items():
            btn.setChecked(c == self.pinned_corner)
        self.update_pin_position()

    def update_pin_position(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        margin = 16
        x, y = self.x(), self.y()
        if self.pinned_corner == "tl":
            x, y = margin, margin
        elif self.pinned_corner == "tr":
            x, y = screen.width() - self.width() - margin, margin
        elif self.pinned_corner == "bl":
            x, y = margin, screen.height() - self.height() - margin
        elif self.pinned_corner == "br":
            x, y = screen.width() - self.width() - margin, screen.height() - self.height() - margin
        if self.pinned_corner:
            self.move(x, y)

    def toggle_click_through(self):
        self.click_through = self.chk_click_through.isChecked()
        if self.click_through:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def set_click_through_off(self):
        """Vom Hauptfenster aufrufbar (z. B. beim Overlay-Hotkey anzeigen)."""
        self.click_through = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        if hasattr(self, 'chk_click_through'):
            self.chk_click_through.setChecked(False)

    def start_drag(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def do_drag(self, event):
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def end_drag(self, event):
        self.is_dragging = False
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        if self.pos().x() == 0 and self.pos().y() == 0:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            self.move(screen.width() - self.width() - 24, 24)
        self.update_pin_position()

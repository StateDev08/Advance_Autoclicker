"""
Gaming-Overlay – Transparentes Overlay mit Echtzeit-Status und neuen Funktionen
Neu: Fortschrittsanzeige, Kompakt-Modus, Pin-Position, Click-through, Letzte Ausführung
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSlider, QProgressBar, QScrollArea, QSizePolicy, QMenu, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QFontDatabase, QPaintEvent, QAction, QColor
import time
import os

try:
    import psutil
except ImportError:
    psutil = None


class GamingOverlay(QWidget):
    """Transparentes Overlay: Makro-Status, Fortschritt, Quick-Actions, Kompakt-Modus, Pin, Click-through"""

    play_macro_requested = pyqtSignal(int)
    stop_all_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    video_record_requested = pyqtSignal(bool) # True = Start, False = Stop
    add_macro_requested = pyqtSignal()
    screenshot_requested = pyqtSignal()

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
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
        self.is_video_recording = False

        self.init_ui()
        self.setup_timer()

    # Mindesthöhe, damit auf Displays mit großer Rahmenhöhe (z. B. TV) keine setGeometry-Warnung entsteht
    SAFE_MIN_HEIGHT = 360
    SAFE_MAX_HEIGHT = 800
    SAFE_MAX_WIDTH = 600

    def init_ui(self):
        self.setMinimumSize(280, 48)
        self.setMaximumSize(self.SAFE_MAX_WIDTH, self.SAFE_MAX_HEIGHT)
        self.resize(340, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10) # Platz für Schatten
        layout.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName("overlayContainer")
        self.container.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Schatten-Effekt für mehr Tiefe
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        # Header
        header = self.create_header()
        self.container_layout.addWidget(header)

        # Scrollbare Area für Content (falls er zu groß wird)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.content = QWidget()
        self.content.setObjectName("contentWidget")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(15, 10, 15, 10)
        self.content_layout.setSpacing(12)

        # ---- Status Bereich ----
        status_box = QFrame()
        status_box.setObjectName("statusBox")
        status_box_layout = QVBoxLayout(status_box)
        status_box_layout.setContentsMargins(0, 0, 0, 0)
        status_box_layout.setSpacing(0)

        self.status_label = QLabel("BEREIT")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        f_status = QFont()
        f_status.setPointSize(12)
        f_status.setBold(True)
        f_status.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        self.status_label.setFont(f_status)
        status_box_layout.addWidget(self.status_label)

        self.macro_label = QLabel("Kein Makro aktiv")
        self.macro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.macro_label.setObjectName("macroLabel")
        self.macro_label.setWordWrap(True)
        status_box_layout.addWidget(self.macro_label)
        
        self.content_layout.addWidget(status_box)

        # Trenner
        self.sep1 = QFrame()
        self.sep1.setFrameShape(QFrame.Shape.HLine)
        self.sep1.setFixedHeight(1)
        self.sep1.setStyleSheet("background-color: rgba(137, 180, 250, 0.2);")
        self.content_layout.addWidget(self.sep1)

        # ---- Fortschritt & Statistik ----
        self.progress_widget = QFrame()
        self.progress_widget.setObjectName("progressWidget")
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(5, 5, 5, 5)
        progress_layout.setSpacing(8)
        
        # Loop / Action Info in schönerer Darstellung
        info_row = QHBoxLayout()
        self.lbl_loop_action = QLabel("Loop 0 · Action 0")
        self.lbl_loop_action.setStyleSheet("color: #fab387; font-size: 9pt; font-family: 'JetBrains Mono', monospace; font-weight: bold;")
        info_row.addWidget(self.lbl_loop_action)
        info_row.addStretch()
        
        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("timerLabel")
        info_row.addWidget(self.timer_label)
        progress_layout.addLayout(info_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_widget.setVisible(False)
        self.content_layout.addWidget(self.progress_widget)

        # ---- Skill Rotation / Next Actions ----
        self.rotation_container = QFrame()
        self.rotation_container.setObjectName("rotationContainer")
        rotation_layout = QVBoxLayout(self.rotation_container)
        rotation_layout.setContentsMargins(8, 8, 8, 8)
        
        rot_title = QLabel("NÄCHSTE AKTIONEN")
        rot_title.setStyleSheet("color: rgba(137, 180, 250, 0.6); font-size: 7pt; font-weight: bold; margin-bottom: 2px;")
        rotation_layout.addWidget(rot_title)

        self.skill_rotation_label = QLabel("")
        self.skill_rotation_label.setWordWrap(True)
        self.skill_rotation_label.setStyleSheet("color: rgba(205, 214, 244, 0.9); font-size: 8.5pt;")
        rotation_layout.addWidget(self.skill_rotation_label)
        
        self.rotation_container.setVisible(False)
        self.content_layout.addWidget(self.rotation_container)

        # ---- Ressourcen & Stats (Modernized) ----
        self.res_frame = QFrame()
        res_layout = QHBoxLayout(self.res_frame)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setSpacing(10)

        def create_res_item(label_text, color):
            box = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {color}; font-size: 7pt; font-weight: bold;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val = QLabel("0%")
            val.setStyleSheet("color: white; font-size: 8.5pt; font-family: 'JetBrains Mono', monospace;")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.addWidget(lbl)
            box.addWidget(val)
            return box, val

        self.cpu_box, self.lbl_cpu_val = create_res_item("CPU", "#f38ba8")
        self.ram_box, self.lbl_ram_val = create_res_item("RAM", "#fab387")
        self.fps_box, self.lbl_fps_val = create_res_item("FPS", "#a6e3a1")
        
        res_layout.addLayout(self.cpu_box)
        res_layout.addLayout(self.ram_box)
        res_layout.addLayout(self.fps_box)
        
        self.content_layout.addWidget(self.res_frame)

        # ---- Session Quick Stats ----
        self.stats_row = QHBoxLayout()
        self.lbl_stats_ok = QLabel("✅ 0")
        self.lbl_stats_err = QLabel("❌ 0")
        self.lbl_stats_ok.setStyleSheet("color: #a6e3a1; font-size: 8.5pt; font-weight: bold;")
        self.lbl_stats_err.setStyleSheet("color: #f38ba8; font-size: 8.5pt; font-weight: bold;")
        self.stats_row.addStretch()
        self.stats_row.addWidget(self.lbl_stats_ok)
        self.stats_row.addWidget(self.lbl_stats_err)
        self.stats_row.addStretch()
        self.content_layout.addLayout(self.stats_row)

        # ---- Mini Log & Action Feedback ----
        self.mini_log_container = QFrame()
        self.mini_log_container.setObjectName("logContainer")
        log_layout = QVBoxLayout(self.mini_log_container)
        log_layout.setContentsMargins(10, 8, 10, 8)
        
        self.mini_log_label = QLabel("System bereit")
        self.mini_log_label.setWordWrap(True)
        self.mini_log_label.setStyleSheet("color: #89dceb; font-size: 7.5pt; font-style: italic;")
        log_layout.addWidget(self.mini_log_label)
        self.content_layout.addWidget(self.mini_log_container)

        # ---- Scheduler / Countdown Info ----
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("background: rgba(249, 226, 175, 0.1); color: #f9e2af; padding: 5px; border-radius: 5px; font-size: 8.5pt;")
        self.countdown_label.setVisible(False)
        self.content_layout.addWidget(self.countdown_label)

        # ---- Status Bar (HP) ----
        self.status_bar_widget = QProgressBar()
        self.status_bar_widget.setFixedHeight(6)
        self.status_bar_widget.setTextVisible(False)
        self.status_bar_widget.setVisible(False)
        self.content_layout.addWidget(self.status_bar_widget)

        # Trenner 2
        self.sep2 = QFrame()
        self.sep2.setFrameShape(QFrame.Shape.HLine)
        self.sep2.setFixedHeight(1)
        self.sep2.setStyleSheet("background-color: rgba(137, 180, 250, 0.1);")
        self.content_layout.addWidget(self.sep2)

        # ---- Quick-Actions & Options ----
        self.quick_frame = self.create_quick_buttons()
        self.content_layout.addWidget(self.quick_frame)

        self.options_frame = self.create_options()
        self.content_layout.addWidget(self.options_frame)

        # Footer mit Fenster-Info
        self.window_label = QLabel("Fenster: —")
        self.window_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window_label.setStyleSheet("color: rgba(166, 173, 200, 0.5); font-size: 7.5pt;")
        self.content_layout.addWidget(self.window_label)

        self.scroll_area.setWidget(self.content)
        self.container_layout.addWidget(self.scroll_area)
        
        layout.addWidget(self.container)
        self.update_style()

    def create_header(self):
        header = QFrame()
        header.setObjectName("overlayHeader")
        header.setCursor(Qt.CursorShape.SizeAllCursor)
        header.setFixedHeight(40)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)

        # Icon-Platzhalter (Emoji)
        icon = QLabel("🎮")
        icon.setStyleSheet("font-size: 14pt;")
        lay.addWidget(icon)

        title = QLabel("Advanced Gaming")
        title.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 11pt;")
        lay.addWidget(title)
        lay.addStretch()

        # Modernere Buttons im Header
        button_style = """
            QPushButton {
                background-color: transparent;
                color: #a6adc8;
                border: none;
                border-radius: 13px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #cdd6f4;
            }
        """

        self.btn_compact = QPushButton("󰅂") # Unicode Pfeil (Chevron) oder einfaches Zeichen
        if self.btn_compact.font().family() != "Segoe UI Symbol":
             self.btn_compact.setText("›")
        self.btn_compact.setFixedSize(26, 26)
        self.btn_compact.setToolTip("Kompakt-Modus")
        self.btn_compact.setStyleSheet(button_style)
        self.btn_compact.clicked.connect(self.toggle_compact)
        lay.addWidget(self.btn_compact)

        self.btn_minimal = QPushButton("󰈈")
        if self.btn_minimal.font().family() != "Segoe UI Symbol":
             self.btn_minimal.setText("M")
        self.btn_minimal.setFixedSize(26, 26)
        self.btn_minimal.setToolTip("Minimal (nur Status)")
        self.btn_minimal.setCheckable(True)
        self.btn_minimal.setStyleSheet(button_style)
        self.btn_minimal.clicked.connect(self.toggle_minimal)
        lay.addWidget(self.btn_minimal)

        btn_min = QPushButton("󰖰")
        if btn_min.font().family() != "Segoe UI Symbol":
             btn_min.setText("−")
        btn_min.setFixedSize(26, 26)
        btn_min.setToolTip("Minimieren")
        btn_min.setStyleSheet(button_style)
        btn_min.clicked.connect(self.hide)
        lay.addWidget(btn_min)

        btn_close = QPushButton("󰅙")
        if btn_close.font().family() != "Segoe UI Symbol":
             btn_close.setText("×")
        btn_close.setFixedSize(26, 26)
        btn_close.setToolTip("Schließen")
        btn_close.setStyleSheet(button_style + "QPushButton:hover { background-color: #f38ba8; color: #11111b; }")
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

        self.btn_play_pause = QPushButton("▶ PLAY")
        self.btn_play_pause.setObjectName("playButton")
        self.btn_play_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_pause.clicked.connect(self._on_play_pause_clicked)
        lay.addWidget(self.btn_play_pause)

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

        self.btn_quick = QPushButton("⚡")
        self.btn_quick.setFixedSize(32, 32)
        self.btn_quick.setToolTip("Schnellstart (Makros)")
        self.btn_quick.clicked.connect(self.show_quick_menu)
        lay.addWidget(self.btn_quick)

        self.btn_add_macro = QPushButton("➕")
        self.btn_add_macro.setFixedSize(32, 32)
        self.btn_add_macro.setToolTip("Makro hinzufügen")
        self.btn_add_macro.clicked.connect(self.add_macro_requested.emit)
        lay.addWidget(self.btn_add_macro)

        self.btn_screenshot = QPushButton("📷")
        self.btn_screenshot.setFixedSize(32, 32)
        self.btn_screenshot.setToolTip("Screenshot aufnehmen")
        self.btn_screenshot.clicked.connect(self.screenshot_requested.emit)
        lay.addWidget(self.btn_screenshot)

        self.btn_video = QPushButton("🎥")
        self.btn_video.setFixedSize(32, 32)
        self.btn_video.setToolTip("Videoaufnahme starten/stoppen")
        self.btn_video.setCheckable(True)
        self.btn_video.clicked.connect(self._on_video_clicked)
        lay.addWidget(self.btn_video)

        return frame

    def _on_video_clicked(self, checked):
        self.video_record_requested.emit(checked)

    def show_quick_menu(self):
        """Zeigt ein Menü mit den letzten/favorisierten Makros."""
        if not self.db:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; }
            QMenu::item:selected { background-color: #89b4fa; color: #11111b; }
        """)
        
        # Makros aus DB laden (vereinfacht: alle aus aktuellem Profil oder Top 5)
        try:
            # Wir nehmen einfach die letzten 8 Makros
            macros = self.db.get_macros()[:8]
            if not macros:
                menu.addAction("Keine Makros gefunden")
            else:
                for m in macros:
                    action = QAction(f"▶ {m['name']}", self)
                    action.triggered.connect(lambda checked, mid=m['id']: self.play_macro_requested.emit(mid))
                    menu.addAction(action)
        except Exception:
            menu.addAction("Fehler beim Laden")
            
        menu.exec(self.btn_quick.mapToGlobal(QPoint(0, self.btn_quick.height())))

    def _on_play_pause_clicked(self):
        """Behandelt den Klick auf den Play/Start-Button."""
        if self.current_macro:
            # Falls ein Makro läuft, aber pausiert ist -> Weiter
            if self.is_paused:
                self.resume_requested.emit()
        else:
            # Falls kein Makro läuft -> Starte das letzte oder ein Standard-Makro
            # In diesem Fall senden wir das Signal zum Abspielen ohne ID (oder -1),
            # das MainWindow entscheidet dann, was zu tun ist.
            self.play_macro_requested.emit(-1)

    def _on_pause_clicked(self):
        if self.is_paused:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()

    def set_paused(self, paused: bool):
        self.is_paused = paused
        if paused:
            self.status_label.setText("Pausiert")
            self.btn_play_pause.setText("▶ WEITER")
            self.btn_play_pause.setVisible(True)
            self.btn_pause.setVisible(False)
        else:
            if self.current_macro:
                self.status_label.setText("Läuft")
                self.btn_play_pause.setVisible(False)
                self.btn_pause.setVisible(True)
                self.btn_pause.setText("⏸ PAUSE")
        # Style-Update für Farben (Gelb/Grün)
        self.update_style()

    def create_options(self):
        frame = QFrame()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(6)

        # Transparenz
        row1 = QHBoxLayout()
        lbl_trans = QLabel("Tr:")
        lbl_trans.setFixedWidth(20)
        lbl_trans.setStyleSheet("font-size: 7pt;")
        row1.addWidget(lbl_trans)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(40)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setFixedHeight(16)
        self.opacity_slider.setValue(int(self.opacity_level * 100))
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        row1.addWidget(self.opacity_slider)
        lay.addLayout(row1)

        # Pin + Click-through
        row2 = QHBoxLayout()
        lbl_pin = QLabel("Pin:")
        lbl_pin.setStyleSheet("font-size: 7pt;")
        row2.addWidget(lbl_pin)
        self.pin_buttons = {}
        for corner, tip in [("tl", "Oben links"), ("tr", "Oben rechts"), ("bl", "Unten links"), ("br", "Unten rechts")]:
            btn = QPushButton(corner.upper())
            btn.setFixedSize(26, 20)
            btn.setStyleSheet("font-size: 7pt; padding: 0;")
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=corner: self.pin_to_corner(c))
            self.pin_buttons[corner] = btn
            row2.addWidget(btn)
        row2.addStretch()

        self.btn_ontop = QPushButton("📌")
        self.btn_ontop.setFixedSize(26, 20)
        self.btn_ontop.setCheckable(True)
        self.btn_ontop.setChecked(True)
        self.btn_ontop.setToolTip("Immer im Vordergrund")
        self.btn_ontop.clicked.connect(self.toggle_always_on_top)
        row2.addWidget(self.btn_ontop)

        self.chk_click_through = QPushButton("Durchklicken")
        self.chk_click_through.setFixedHeight(20)
        self.chk_click_through.setStyleSheet("font-size: 7.5pt; padding: 0 4px;")
        self.chk_click_through.setCheckable(True)
        self.chk_click_through.setToolTip("Mausklicks durchlassen (zum Deaktivieren Overlay-Hotkey nutzen)")
        self.chk_click_through.clicked.connect(self.toggle_click_through)
        row2.addWidget(self.chk_click_through)
        lay.addLayout(row2)

        return frame

    def apply_styles(self):
        # Catppuccin Mocha Palette (für das Overlay leicht angepasst für Transparenz)
        palette = {
            "bg": f"rgba(30, 30, 46, {self.opacity_level})",
            "surface": "rgba(49, 50, 68, 0.4)",
            "accent": "rgba(137, 180, 250, 0.8)",  # Blue
            "text": "rgba(205, 214, 244, 0.95)",
            "subtext": "rgba(166, 173, 200, 0.8)",
            "red": "rgba(243, 139, 168, 0.9)",
            "green": "rgba(166, 227, 161, 0.9)",
            "yellow": "rgba(249, 226, 175, 0.9)",
            "border": "rgba(137, 180, 250, 0.25)",
            "crust": "rgba(17, 17, 27, 0.6)",
        }

        # Statusfarben basierend auf Zustand
        status_color = palette["accent"]
        if self.is_paused:
            status_color = palette["yellow"]
        elif self.current_macro:
            status_color = palette["green"]
        elif getattr(self, "status_label", None) and self.status_label.text() == "AUFNAHME":
            status_color = palette["red"]

        # Globales Stylesheet für das gesamte Widget (vererbt Transparenz)
        self.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                color: {palette["text"]};
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            #overlayContainer {{
                background-color: {palette["bg"]};
                border: 1px solid {palette["border"]};
                border-radius: 20px;
            }}
            #overlayHeader {{
                background-color: rgba(0, 0, 0, 0.25);
                border-radius: 20px 20px 0 0;
            }}
            #statusBox {{
                background: transparent;
            }}
            #statusLabel {{ 
                color: {status_color}; 
                padding: 0;
                margin-top: 4px;
            }}
            #macroLabel {{ 
                color: {palette["subtext"]}; 
                font-size: 9pt; 
                margin-bottom: 4px;
            }}
            #progressWidget, #rotationContainer, #logContainer {{
                background-color: {palette["surface"]};
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }}
            #timerLabel {{ 
                color: {palette["yellow"]}; 
                font-size: 9.5pt; 
                font-family: 'JetBrains Mono', monospace; 
                font-weight: bold;
            }}
            QProgressBar {{
                border: none;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {palette["accent"]}, stop:1 #b4befe);
                border-radius: 4px;
            }}
            #pauseButton {{
                background-color: {palette["yellow"]};
                color: #11111b;
                border: none;
                border-radius: 10px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 8.5pt;
            }}
            #pauseButton:hover {{ background-color: rgba(249, 226, 175, 1.0); }}
            #stopButton {{
                background-color: {palette["red"]};
                color: #11111b;
                border: none;
                border-radius: 10px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 8.5pt;
            }}
            #stopButton:hover {{ background-color: rgba(243, 139, 168, 1.0); }}
            #playButton {{
                background-color: #2ecc71;
                color: #11111b;
                border: none;
                border-radius: 10px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 8.5pt;
            }}
            #playButton:hover {{ background-color: rgba(46, 204, 113, 1.0); }}
            QPushButton {{
                background-color: {palette["surface"]};
                color: {palette["text"]};
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px;
            }}
            QPushButton:hover {{ 
                background-color: rgba(69, 71, 90, 0.7);
                border-color: {palette["accent"]};
            }}
            QPushButton:checked {{ 
                background-color: {palette["accent"]}; 
                color: #11111b;
                border: none;
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {palette["accent"]};
                width: 14px;
                height: 14px;
                margin: -5px 0;
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
            # Schönere Darstellung mit Pfeilen
            self.skill_rotation_label.setText(" → ".join(self.skill_rotation_list[:4]))
            self.rotation_container.setVisible(not self.is_minimal)
        else:
            self.rotation_container.setVisible(False)

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

    def set_session_stats(self, success: int, fail: int):
        """Zeigt Session-Statistiken im Overlay an."""
        self._session_stats = f" | ✅{success} ❌{fail}"

    def set_next_schedule(self, text: str):
        """Zeigt den nächsten geplanten Makro-Termin."""
        if text:
            self.countdown_label.setText(f"Nächster: {text}")
            self.countdown_label.setVisible(True) # Immer sichtbar wenn Text da ist
        else:
            self.countdown_label.setVisible(False)

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
            self.lbl_fps_val.setText(str(self.current_fps))
            
            # Ressourcen-Check (CPU/RAM) alle 2 Sekunden
            if t_perf - self._resource_timer >= 2.0:
                self._resource_timer = t_perf
                if psutil:
                    try:
                        self.current_cpu = int(psutil.cpu_percent())
                        self.current_ram = int(psutil.virtual_memory().percent)
                    except Exception:
                        pass
                else:
                    # Fallback ohne psutil
                    try:
                        if hasattr(os, 'getloadavg'): # Linux/macOS
                            self.current_cpu = int(os.getloadavg()[0] * 10)
                    except Exception:
                        pass
                
                self.lbl_cpu_val.setText(f"{self.current_cpu}%")
                self.lbl_ram_val.setText(f"{self.current_ram}%")

        if self.isVisible():
            self.update()

    def set_session_stats(self, success: int, fail: int):
        """Zeigt Session-Statistiken im Overlay an."""
        self.lbl_stats_ok.setText(f"✅ {success}")
        self.lbl_stats_err.setText(f"❌ {fail}")

    def set_mini_log(self, message: str):
        """Zeigt eine kurze Nachricht (Log) im Overlay."""
        clean_msg = str(message).strip()
        # Falls es eine Erfolgs/Fehler-Nachricht ist, direkt flashen
        if any(kw in clean_msg for kw in ["Erfolg", "Gefunden", "Success"]):
            self.flash_success()
        elif any(kw in clean_msg.lower() for kw in ["fehler", "nicht gefunden", "error", "fail"]):
            self.flash_error()

        self.mini_log_label.setText(clean_msg[:60] + ("..." if len(clean_msg) > 60 else ""))
        # Reset nach 4 Sekunden
        QTimer.singleShot(4000, lambda: self.mini_log_label.setText("") if self.mini_log_label.text() == (clean_msg[:60] + ("..." if len(clean_msg) > 60 else "")) else None)

    def set_macro_running(self, macro_name: str):
        self.current_macro = macro_name
        self.macro_start_time = time.time()
        self.status_label.setText("LÄUFT")
        self.macro_label.setText(macro_name)
        self.progress_bar.setValue(0)
        self.lbl_loop_action.setText("Loop 0 · Action 0")
        self.progress_widget.setVisible(not self.is_minimal)
        self.btn_play_pause.setVisible(False)
        self.btn_pause.setVisible(True)
        self.set_paused(False)
        self.set_mini_log(f"Starte: {macro_name}")
        self.update_style()

    def set_playback_progress(self, progress: float, loop: int, action: int):
        self.playback_progress = progress
        self.playback_loop = loop
        self.playback_action = action
        self.progress_bar.setValue(int(progress))
        self.lbl_loop_action.setText(f"Loop {loop} · Action {action}")
        self.btn_pause.setVisible(True)

    def set_macro_stopped(self):
        if self.current_macro and self.macro_start_time is not None:
            self.last_run_name = self.current_macro
            self.last_run_duration = time.time() - self.macro_start_time
            m, s = int(self.last_run_duration // 60), int(self.last_run_duration % 60)
            self.set_mini_log(f"Beendet: {self.current_macro} ({m:02d}:{s:02d})")
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
        self.status_label.setText("BEREIT")
        self.macro_label.setText("Kein Makro aktiv")
        self.timer_label.setText("00:00")
        self.progress_widget.setVisible(False)
        self.progress_bar.setValue(0)
        self.lbl_loop_action.setText("Loop 0 · Action 0")
        self.btn_play_pause.setVisible(True)
        self.btn_play_pause.setText("▶ PLAY")
        self.btn_pause.setVisible(False)
        self.is_paused = False
        self.update_style()

    def set_recording(self, is_recording: bool):
        if is_recording:
            self.status_label.setText("AUFNAHME")
            self.macro_label.setText("Makro wird aufgenommen…")
            self.macro_start_time = time.time()
            self.progress_widget.setVisible(False)
            self.update_style()
        else:
            self.set_macro_stopped()

    def set_video_recording(self, is_recording: bool):
        """Aktualisiert den Status der Videoaufnahme im Overlay."""
        self.is_video_recording = is_recording
        if hasattr(self, 'btn_video'):
            self.btn_video.setChecked(is_recording)
            self.btn_video.setText("🔴" if is_recording else "🎥")
            self.btn_video.setStyleSheet("background-color: rgba(243, 139, 168, 0.5);" if is_recording else "")
        
        if is_recording:
            self.set_mini_log("Videoaufnahme läuft...")
        else:
            self.set_mini_log("Videoaufnahme beendet.")

    def flash_success(self):
        """Lässt das Overlay kurz grün aufleuchten."""
        self._flash_color("#a6e3a1")

    def flash_error(self):
        """Lässt das Overlay kurz rot aufleuchten."""
        self._flash_color("#f38ba8")

    def _flash_color(self, color_hex: str):
        """Interne Methode für den Flash-Effekt (Rahmen kurz einfärben)."""
        original_border = "rgba(137, 180, 250, 0.25)"
        current_style = self.styleSheet()
        flash_style = current_style.replace(
            f"border: 1px solid {original_border};",
            f"border: 2px solid {color_hex};"
        )
        self.setStyleSheet(flash_style)
        QTimer.singleShot(400, lambda: self.setStyleSheet(current_style))

    def on_opacity_changed(self, value: int):
        self.opacity_level = value / 100.0
        self.update_style()

    def toggle_compact(self):
        if self.is_minimal:
            self.toggle_minimal()
            
        self.is_compact = not self.is_compact
        
        # Animation für sanftes Auf/Zuklappen
        self.anim = QPropertyAnimation(self, b"size")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        start_size = self.size()
        if self.is_compact:
            self.scroll_area.setVisible(False)
            end_size = QRect(0, 0, self.width(), 48).size()
        else:
            end_size = QRect(0, 0, self.width(), 520).size()
            # Verzögertes Anzeigen des Contents nach Animation
            QTimer.singleShot(300, lambda: self.scroll_area.setVisible(True))
            
        self.anim.setStartValue(start_size)
        self.anim.setEndValue(end_size)
        self.anim.start()

        if hasattr(self, 'btn_compact'):
            self.btn_compact.setText("▾" if self.is_compact else "▸")

    def toggle_minimal(self):
        """Minimal-Ansicht: zeigt nur Status, Makroname, Fortschritt und Countdown."""
        self.is_minimal = not self.is_minimal
        if hasattr(self, 'btn_minimal'):
            self.btn_minimal.setChecked(self.is_minimal)
            
        # Animation für Breite
        self.anim_w = QPropertyAnimation(self, b"size")
        self.anim_w.setDuration(300)
        self.anim_w.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        start_size = self.size()
        if self.is_minimal:
            end_size = QRect(0, 0, 280, self.height()).size()
        else:
            end_size = QRect(0, 0, 340, self.height()).size()
            
        self.anim_w.setStartValue(start_size)
        self.anim_w.setEndValue(end_size)
        self.anim_w.start()
        
        self._update_minimal_visibility()

    def _update_minimal_visibility(self):
        if not hasattr(self, 'progress_widget'):
            return
        show = not self.is_minimal
        self.sep1.setVisible(show)
        self.progress_widget.setVisible(self.current_macro is not None)
        self.res_frame.setVisible(show)
        self.stats_row.parent().findChildren(QLabel)[-1].setVisible(show) # Dummy für row
        # Wir blenden gezielt Container aus
        self.rotation_container.setVisible(len(self.skill_rotation_list) > 0 and show)
        self.mini_log_container.setVisible(show)
        self.sep2.setVisible(show)
        self.quick_frame.setVisible(show)
        self.options_frame.setVisible(show)
        self.window_label.setVisible(show)

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

    def toggle_always_on_top(self):
        """Schaltet 'Immer im Vordergrund' um."""
        on_top = self.btn_ontop.isChecked()
        if on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        # Fenster muss neu angezeigt werden, damit Flags greifen
        self.show()

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

"""
Gaming-Overlay - Transparentes Overlay-Fenster für Echtzeit-Informationen
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QSlider)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QPalette, QColor
import time


class GamingOverlay(QWidget):
    """Transparentes Overlay-Fenster mit Makro-Status und Quick-Access"""
    
    toggle_visibility = pyqtSignal()
    stop_all_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # State
        self.is_dragging = False
        self.drag_position = QPoint()
        self.current_macro = None
        self.macro_start_time = None
        self.opacity_level = 0.85
        
        # Performance tracking
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """Initialisiert die UI"""
        self.setMinimumSize(300, 200)
        self.setMaximumSize(500, 400)
        self.resize(350, 250)
        
        # Hauptlayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container mit Hintergrund
        self.container = QFrame()
        self.container.setObjectName("overlayContainer")
        self.update_style()
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(8)
        
        # Header mit Drag-Handle und Buttons
        header = self.create_header()
        container_layout.addWidget(header)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background-color: rgba(255, 255, 255, 0.2);")
        separator1.setFixedHeight(1)
        container_layout.addWidget(separator1)
        
        # Status-Bereich
        self.status_label = QLabel("🎮 Bereit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #00ff00; padding: 5px;")
        container_layout.addWidget(self.status_label)
        
        # Makro-Info
        self.macro_label = QLabel("Kein Makro aktiv")
        self.macro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.macro_label.setStyleSheet("color: #ffffff; font-size: 10pt;")
        self.macro_label.setWordWrap(True)
        container_layout.addWidget(self.macro_label)
        
        # Timer
        self.timer_label = QLabel("⏱️ 00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #ffaa00; font-size: 10pt; font-family: monospace;")
        container_layout.addWidget(self.timer_label)
        
        # Performance Counter
        self.fps_label = QLabel("FPS: 0 | CPU: 0%")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet("color: #888888; font-size: 8pt; font-family: monospace;")
        container_layout.addWidget(self.fps_label)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: rgba(255, 255, 255, 0.2);")
        separator2.setFixedHeight(1)
        container_layout.addWidget(separator2)
        
        # Quick-Access Buttons
        quick_buttons = self.create_quick_buttons()
        container_layout.addWidget(quick_buttons)
        
        # Opacity Slider
        opacity_control = self.create_opacity_control()
        container_layout.addWidget(opacity_control)
        
        container_layout.addStretch()
        
        layout.addWidget(self.container)
        
    def create_header(self):
        """Erstellt den Header mit Titel und Buttons"""
        header = QFrame()
        header.setObjectName("overlayHeader")
        header.setCursor(Qt.CursorShape.SizeAllCursor)
        header.setStyleSheet("""
            #overlayHeader {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Titel
        title = QLabel("⚡ Advanced Auto Clicker")
        title.setStyleSheet("color: #00ffff; font-weight: bold; font-size: 10pt;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Minimize Button
        btn_minimize = QPushButton("─")
        btn_minimize.setFixedSize(24, 24)
        btn_minimize.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 170, 0, 0.8);
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 170, 0, 1.0);
            }
        """)
        btn_minimize.clicked.connect(self.hide)
        layout.addWidget(btn_minimize)
        
        # Close Button
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 0.8);
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 1.0);
            }
        """)
        btn_close.clicked.connect(self.hide)
        layout.addWidget(btn_close)
        
        # Drag-Funktionalität
        header.mousePressEvent = self.start_drag
        header.mouseMoveEvent = self.do_drag
        header.mouseReleaseEvent = self.end_drag
        
        return header
        
    def create_quick_buttons(self):
        """Erstellt Quick-Access Buttons"""
        buttons_frame = QFrame()
        layout = QHBoxLayout(buttons_frame)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(5)
        
        # Stop All Button
        btn_stop_all = QPushButton("⏹️ STOP ALL")
        btn_stop_all.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 0.7);
                color: white;
                border: 2px solid #ff0000;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.9);
            }
            QPushButton:pressed {
                background-color: rgba(200, 0, 0, 1.0);
            }
        """)
        btn_stop_all.clicked.connect(self.stop_all_requested.emit)
        layout.addWidget(btn_stop_all)
        
        return buttons_frame
        
    def create_opacity_control(self):
        """Erstellt Opacity-Slider"""
        control_frame = QFrame()
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(5)
        
        label = QLabel("Transparenz:")
        label.setStyleSheet("color: #888888; font-size: 8pt;")
        layout.addWidget(label)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(30)
        slider.setMaximum(100)
        slider.setValue(int(self.opacity_level * 100))
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #00ffff;
                border: 1px solid #00aaaa;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)
        slider.valueChanged.connect(self.on_opacity_changed)
        layout.addWidget(slider)
        
        return control_frame
        
    def update_style(self):
        """Aktualisiert den Container-Style mit Opacity"""
        self.container.setStyleSheet(f"""
            #overlayContainer {{
                background-color: rgba(20, 20, 30, {self.opacity_level});
                border: 2px solid rgba(0, 255, 255, 0.5);
                border-radius: 10px;
            }}
        """)
        
    def setup_timer(self):
        """Richtet Update-Timer ein"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # Update alle 100ms
        
    def update_display(self):
        """Aktualisiert die Anzeige"""
        # Timer aktualisieren
        if self.macro_start_time:
            elapsed = time.time() - self.macro_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_label.setText(f"⏱️ {minutes:02d}:{seconds:02d}")
        
        # FPS berechnen
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time
            
        # CPU-Info (vereinfacht - könnte mit psutil erweitert werden)
        self.fps_label.setText(f"FPS: {self.current_fps}")
        
    def set_macro_running(self, macro_name: str):
        """Setzt Status auf 'Makro läuft'"""
        self.current_macro = macro_name
        self.macro_start_time = time.time()
        self.status_label.setText("▶️ LÄUFT")
        self.status_label.setStyleSheet("color: #00ff00; padding: 5px; font-weight: bold;")
        self.macro_label.setText(f"📝 {macro_name}")
        
    def set_macro_stopped(self):
        """Setzt Status auf 'Bereit'"""
        self.current_macro = None
        self.macro_start_time = None
        self.status_label.setText("🎮 Bereit")
        self.status_label.setStyleSheet("color: #00ffff; padding: 5px; font-weight: bold;")
        self.macro_label.setText("Kein Makro aktiv")
        self.timer_label.setText("⏱️ 00:00")
        
    def set_recording(self, is_recording: bool):
        """Setzt Aufnahme-Status"""
        if is_recording:
            self.status_label.setText("🔴 AUFNAHME")
            self.status_label.setStyleSheet("color: #ff0000; padding: 5px; font-weight: bold;")
            self.macro_label.setText("Makro wird aufgenommen...")
            self.macro_start_time = time.time()
        else:
            self.set_macro_stopped()
            
    def on_opacity_changed(self, value: int):
        """Opacity wurde geändert"""
        self.opacity_level = value / 100.0
        self.update_style()
        
    def start_drag(self, event):
        """Startet Drag-Operation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def do_drag(self, event):
        """Führt Drag durch"""
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def end_drag(self, event):
        """Beendet Drag"""
        self.is_dragging = False
        event.accept()
        
    def showEvent(self, event):
        """Wird aufgerufen wenn Overlay angezeigt wird"""
        super().showEvent(event)
        # Positioniere in oberer rechter Ecke, falls noch nicht positioniert
        if self.pos().x() == 0 and self.pos().y() == 0:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            self.move(screen.width() - self.width() - 20, 20)

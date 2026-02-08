"""
Tools-Tab: Video-Aufnahme, Screenshot-Quick-Access, etc.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFormLayout,
)
from PyQt6.QtCore import QTimer, Qt
from pathlib import Path
from typing import Optional

from database import DatabaseManager
from core.screen_recorder import ScreenRecorder


class ToolsTab(QWidget):
    """Tab für Video-Aufnahme und weitere Tools."""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.recorder: Optional[ScreenRecorder] = None
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Video-Aufnahme
        video_group = QGroupBox("Bildschirm-Video")
        video_layout = QFormLayout()
        self.btn_video_start = QPushButton("▶ Video starten")
        self.btn_video_start.clicked.connect(self.start_video)
        video_layout.addRow("", self.btn_video_start)
        self.btn_video_stop = QPushButton("⏹ Video stoppen")
        self.btn_video_stop.clicked.connect(self.stop_video)
        self.btn_video_stop.setEnabled(False)
        video_layout.addRow("", self.btn_video_stop)
        self.lbl_video_status = QLabel("Nicht aktiv")
        self.lbl_video_status.setWordWrap(True)
        video_layout.addRow("Status:", self.lbl_video_status)
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        layout.addStretch()

    def _get_recorder(self) -> ScreenRecorder:
        if self.recorder is None:
            folder = self.db.get_setting("video_folder", "").strip()
            fps = 30
            try:
                fps = int(self.db.get_setting("video_fps", "30"))
            except ValueError:
                pass
            self.recorder = ScreenRecorder(fps=fps, save_dir=folder or None)
        else:
            folder = self.db.get_setting("video_folder", "").strip()
            fps = 30
            try:
                fps = int(self.db.get_setting("video_fps", "30"))
            except ValueError:
                pass
            self.recorder.fps = max(1, min(60, fps))
            self.recorder.save_dir = Path(folder) if folder else Path("data") / "recordings"
            self.recorder.save_dir.mkdir(parents=True, exist_ok=True)
        return self.recorder

    def start_video(self):
        rec = self._get_recorder()
        if rec.is_recording:
            return
        path = rec.start()
        if path:
            self.btn_video_start.setEnabled(False)
            self.btn_video_stop.setEnabled(True)
            self._update_timer.start(1000)
            self._update_status()
        else:
            self.lbl_video_status.setText("Start fehlgeschlagen.")

    def stop_video(self):
        if self.recorder is None or not self.recorder.is_recording:
            return
        path = self.recorder.stop()
        self._update_timer.stop()
        self.btn_video_start.setEnabled(True)
        self.btn_video_stop.setEnabled(False)
        if path:
            self.lbl_video_status.setText(f"Gespeichert: {path}")
        else:
            self.lbl_video_status.setText("Nicht aktiv")

    def _update_status(self):
        if self.recorder is None or not self.recorder.is_recording:
            return
        secs = int(self.recorder.duration_seconds)
        m, s = secs // 60, secs % 60
        self.lbl_video_status.setText(f"Aufnahme läuft – {m:02d}:{s:02d} – {self.recorder.output_path}")

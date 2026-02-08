"""
Bildschirm-Video aufnehmen (z. B. für Tutorials, Gameplay).
Thread-basiert, konfigurierbare FPS, Ausgabe AVI/MP4.
"""

import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from PIL import ImageGrab
import cv2
import numpy as np


class ScreenRecorder:
    """Zeichnet den Bildschirm als Video auf."""

    def __init__(self, fps: int = 30, save_dir: Optional[str] = None):
        self.fps = max(1, min(60, fps))
        self.save_dir = Path(save_dir) if save_dir and str(save_dir).strip() else Path("data") / "recordings"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._writer: Optional[cv2.VideoWriter] = None
        self._output_path: Optional[Path] = None
        self._start_time: Optional[float] = None

    @property
    def is_recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def output_path(self) -> Optional[Path]:
        return self._output_path

    @property
    def duration_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def start(self) -> Optional[Path]:
        """Startet die Aufnahme. Gibt den geplanten Ausgabepfad zurück."""
        if self.is_recording:
            return None
        self._stop.clear()
        name = f"recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.avi"
        self._output_path = self.save_dir / name
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        self._start_time = time.time()
        return self._output_path

    def stop(self) -> Optional[Path]:
        """Stoppt die Aufnahme. Gibt den gespeicherten Dateipfad zurück."""
        if not self.is_recording:
            return None
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        path = self._output_path
        self._output_path = None
        self._start_time = None
        return path

    def _record_loop(self):
        """Hauptschleife: Screenshot → BGR → VideoWriter."""
        # Ersten Frame holen für Größe
        pil_img = ImageGrab.grab()
        frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self._writer = cv2.VideoWriter(str(self._output_path), fourcc, self.fps, (w, h))
        if not self._writer.isOpened():
            self._writer = None
            return
        interval = 1.0 / self.fps
        next_capture = time.perf_counter()
        while not self._stop.is_set():
            now = time.perf_counter()
            if now >= next_capture:
                pil_img = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                self._writer.write(frame)
                next_capture = now + interval
            else:
                time.sleep(min(0.01, next_capture - now))
        if self._writer:
            self._writer.release()
            self._writer = None

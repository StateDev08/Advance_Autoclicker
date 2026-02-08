"""
Screenshot: Vollbild oder Bereich als PNG speichern.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from PIL import ImageGrab


def get_screenshot_folder(settings_dir: Optional[str] = None) -> Path:
    """Gibt den konfigurierten Screenshot-Ordner zurück (Standard: data/screenshots)."""
    if settings_dir and settings_dir.strip():
        p = Path(settings_dir.strip())
    else:
        p = Path("data") / "screenshots"
    p.mkdir(parents=True, exist_ok=True)
    return p


def capture_fullscreen(save_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Erstellt einen Vollbild-Screenshot und speichert ihn als PNG.
    Dateiname: screenshot_YYYY-MM-DD_HH-MM-SS.png
    Returns: Pfad zur gespeicherten Datei oder None bei Fehler.
    """
    try:
        img = ImageGrab.grab()
        if save_dir is None:
            save_dir = get_screenshot_folder()
        name = f"screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        path = save_dir / name
        img.save(path)
        return path
    except Exception:
        return None


def capture_region(
    bbox: Tuple[int, int, int, int],
    save_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Screenshot eines Bereichs (x1, y1, x2, y2).
    Returns: Pfad zur gespeicherten Datei oder None.
    """
    try:
        img = ImageGrab.grab(bbox=bbox)
        if save_dir is None:
            save_dir = get_screenshot_folder()
        name = f"screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        path = save_dir / name
        img.save(path)
        return path
    except Exception:
        return None

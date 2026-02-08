"""
Update-Prüfung und Download für Advanced Gaming.
Lädt version.json, vergleicht Versionen, lädt EXE mit Fortschritts-Callback.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Callable, Tuple

from core.version import APP_VERSION, UPDATE_BASE_URL


def _parse_version(s: str) -> Tuple[int, ...]:
    """Versionsstring in vergleichbares Tupel umwandeln (z.B. '3.1.0' -> (3, 1, 0))."""
    parts = []
    for p in s.strip().split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def version_compare(local: str, remote: str) -> int:
    """
    Vergleicht zwei Versionsstrings.
    Returns: -1 wenn local < remote, 0 wenn gleich, 1 wenn local > remote
    """
    a, b = _parse_version(local), _parse_version(remote)
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def fetch_version_info(timeout: float = 10.0) -> Optional[dict]:
    """
    Lädt version.json vom Server.
    Erwartetes Format: {"version": "3.1.0", "url": "https://.../AdvancedGaming.exe"} (url optional)
    Returns None bei Fehler oder Timeout.
    """
    url = f"{UPDATE_BASE_URL.rstrip('/')}/version.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AdvancedGaming-Updater"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        return None


def get_update_info() -> Tuple[bool, Optional[str], str]:
    """
    Prüft, ob eine neuere Version verfügbar ist.
    Returns: (update_available, server_version, download_url)
    download_url ist die EXE-URL (aus version.json oder Standard).
    """
    info = fetch_version_info()
    if not info or "version" not in info:
        return False, None, f"{UPDATE_BASE_URL.rstrip('/')}/AdvancedGaming.exe"
    server_version = str(info["version"]).strip()
    url = info.get("url") or f"{UPDATE_BASE_URL.rstrip('/')}/AdvancedGaming.exe"
    if version_compare(APP_VERSION, server_version) < 0:
        return True, server_version, url
    return False, server_version, url


def download_file(
    url: str,
    path: Path,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    timeout: float = 60.0,
) -> Optional[str]:
    """
    Lädt eine Datei herunter und ruft progress_callback(loaded_bytes, total_bytes_or_None) auf.
    total_bytes ist None wenn Content-Length fehlt.
    Returns None bei Erfolg, sonst Fehlermeldung.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AdvancedGaming-Updater"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = resp.headers.get("Content-Length")
            total_int = int(total) if total else None
            chunk_size = 64 * 1024
            loaded = 0
            with open(path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    loaded += len(chunk)
                    if progress_callback:
                        progress_callback(loaded, total_int)
        return None
    except Exception as e:
        return str(e)

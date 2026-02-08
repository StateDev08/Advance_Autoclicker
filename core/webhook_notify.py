"""
Outgoing-Webhook: Benachrichtigung beim Ende eines Makros (normal oder gestoppt).
Sendet einen POST in einem separaten Thread, blockiert die App nicht.
"""

import json
import threading
import urllib.request
import urllib.error
from typing import Optional


def notify_macro_finished(
    url: str,
    macro_id: int,
    macro_name: str,
    status: str = "completed",
):
    """
    Sendet einen HTTP-POST an die konfigurierte URL (in einem Thread).
    status: "completed" (normal beendet) oder "stopped" (vom Nutzer gestoppt).
    """
    if not url or not url.strip():
        return
    payload = {
        "macro_id": macro_id,
        "macro_name": macro_name,
        "status": status,
    }

    def _send():
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass  # Stille Fehlerbehandlung, kein Blockieren

    threading.Thread(target=_send, daemon=True).start()

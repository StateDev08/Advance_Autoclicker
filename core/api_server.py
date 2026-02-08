"""
Lokale HTTP-API für Steuerung von außen (Browser, OBS, Stream Deck, Scripts).
Läuft nur auf 127.0.0.1, portkonfigurierbar.
"""

import json
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional, Any


def _cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


class APIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler für die lokale API."""

    # Wird vom Server gesetzt
    api_handlers: Optional[dict] = None

    def log_message(self, format, *args):
        pass  # Stille Logs, optional später an LogManager anbinden

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: int = 400):
        self._send_json({"error": message}, status=status)

    def _parse_path(self):
        path = self.path
        if "?" in path:
            path, query = path.split("?", 1)
            query = urllib.parse.parse_qs(query)
        else:
            query = {}
        parts = [p for p in path.split("/") if p]
        return parts, query

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        parts, query = self._parse_path()
        handlers = self.api_handlers or {}

        # /api/status
        if parts == ["api", "status"]:
            cb = handlers.get("get_status")
            if not cb:
                return self._send_error_json("API not configured", 503)
            try:
                data = cb()
                return self._send_json(data)
            except Exception as e:
                return self._send_error_json(str(e), 500)

        # /api/profiles
        if parts == ["api", "profiles"]:
            cb = handlers.get("get_profiles")
            if not cb:
                return self._send_error_json("API not configured", 503)
            try:
                data = cb()
                return self._send_json(data)
            except Exception as e:
                return self._send_error_json(str(e), 500)

        # /api/macros?profile_id=1
        if parts == ["api", "macros"]:
            cb = handlers.get("get_macros")
            if not cb:
                return self._send_error_json("API not configured", 503)
            profile_id = query.get("profile_id", [None])[0]
            if profile_id is not None:
                try:
                    profile_id = int(profile_id)
                except ValueError:
                    return self._send_error_json("Invalid profile_id", 400)
            try:
                data = cb(profile_id)
                return self._send_json(data)
            except Exception as e:
                return self._send_error_json(str(e), 500)

        self._send_error_json("Not Found", 404)

    def do_POST(self):
        parts, query = self._parse_path()
        handlers = self.api_handlers or {}

        # /api/stop
        if parts == ["api", "stop"]:
            cb = handlers.get("stop_playback")
            if not cb:
                return self._send_error_json("API not configured", 503)
            try:
                cb()
                return self._send_json({"ok": True})
            except Exception as e:
                return self._send_error_json(str(e), 500)

        # /api/macros/<id>/start
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "macros" and parts[3] == "start":
            try:
                macro_id = int(parts[2])
            except ValueError:
                return self._send_error_json("Invalid macro id", 400)
            loop_infinite = query.get("loop_infinite", ["0"])[0] in ("1", "true", "yes")
            cb = handlers.get("start_macro")
            if not cb:
                return self._send_error_json("API not configured", 503)
            try:
                cb(macro_id, loop_infinite=loop_infinite)
                return self._send_json({"ok": True, "macro_id": macro_id})
            except Exception as e:
                return self._send_error_json(str(e), 500)

        # /api/trigger?macro_id=123&token=XXX
        if parts == ["api", "trigger"]:
            macro_id_s = query.get("macro_id", [None])[0]
            token = query.get("token", [""])[0]
            if not macro_id_s:
                return self._send_error_json("macro_id required", 400)
            try:
                macro_id = int(macro_id_s)
            except ValueError:
                return self._send_error_json("Invalid macro_id", 400)
            cb = handlers.get("trigger")
            if not cb:
                return self._send_error_json("API not configured", 503)
            try:
                ok = cb(macro_id, token)
                if ok:
                    return self._send_json({"ok": True, "macro_id": macro_id})
                return self._send_error_json("Invalid token or trigger disabled", 403)
            except Exception as e:
                return self._send_error_json(str(e), 500)

        self._send_error_json("Not Found", 404)


def _fix_post_macros_start(parts: list) -> bool:
    # POST /api/macros/5/start -> parts = ["api", "macros", "5", "start"]
    return len(parts) == 4 and parts[0] == "api" and parts[1] == "macros" and parts[3] == "start"


class APIServer:
    """Thread-basierter HTTP-Server für die lokale API."""

    def __init__(
        self,
        port: int = 5847,
        get_status: Optional[Callable[[], dict]] = None,
        get_profiles: Optional[Callable[[], list]] = None,
        get_macros: Optional[Callable[[Optional[int]], list]] = None,
        start_macro: Optional[Callable[[int, bool], None]] = None,
        stop_playback: Optional[Callable[[], None]] = None,
        trigger: Optional[Callable[[int, str], bool]] = None,
    ):
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._handlers = {
            "get_status": get_status,
            "get_profiles": get_profiles,
            "get_macros": get_macros,
            "start_macro": start_macro,
            "stop_playback": stop_playback,
            "trigger": trigger,
        }
        APIHandler.api_handlers = self._handlers

    def start(self):
        if self._server is not None:
            return
        try:
            self._server = HTTPServer(("127.0.0.1", self.port), APIHandler)
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
        except OSError:
            self._server = None
            self._thread = None
            raise

    def stop(self):
        if self._server is None:
            return
        self._server.shutdown()
        self._server = None
        self._thread = None

    def is_running(self) -> bool:
        return self._server is not None

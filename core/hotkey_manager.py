"""
Hotkey-Manager - Verwaltet globale Tastenkombinationen
"""

from pynput import keyboard, mouse
from typing import Dict, Callable, Optional
import threading


class HotkeyManager:
    """Verwaltet globale Hotkeys für Makros (Tastatur + Maus)"""

    def __init__(self):
        # hotkey-string (z.B. "ctrl+shift+r", "mouse_x1") -> Callback
        self.hotkeys: Dict[str, Callable] = {}
        self.keyboard_listener = None
        self.mouse_listener = None
        self.is_active = False
        self.current_keys = set()

        # Optionaler Debug-Callback, um erkannte Kombinationen anzuzeigen
        self.debug_callback: Optional[Callable[[str], None]] = None

    def register_hotkey(self, hotkey: str, callback: Callable):
        """Registriert einen Hotkey.

        Hotkey-Format entspricht den Strings aus den Einstellungen/Dialogs,
        z.B. "ctrl+shift+r", "f8", "mouse_x1".
        """
        if not hotkey:
            return
        self.hotkeys[hotkey.lower()] = callback

    def unregister_hotkey(self, hotkey: str):
        """Entfernt einen Hotkey"""
        if not hotkey:
            return
        if hotkey.lower() in self.hotkeys:
            del self.hotkeys[hotkey.lower()]

    def set_debug_callback(self, callback: Optional[Callable[[str], None]]):
        """Setzt oder entfernt den Debug-Callback.

        Wird bei jeder erkannten Kombination aufgerufen (egal ob registriert
        oder nicht)."""
        self.debug_callback = callback

    def start(self):
        """Startet die globalen Hotkey-Listener (Tastatur + Maus)."""
        if self.is_active:
            return

        self.is_active = True

        # Tastatur-Listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self.keyboard_listener.start()

        # Maus-Listener (für mouse_left, mouse_x1, ...)
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
        )
        self.mouse_listener.start()

    def stop(self):
        """Stoppt die globalen Hotkey-Listener."""
        if not self.is_active:
            return

        self.is_active = False

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        self.current_keys.clear()

    # --- Event-Handler ---

    def _on_key_press(self, key):
        """Key-Press Event Handler"""
        if not self.is_active:
            return

        key_str = self._key_to_string(key)
        if key_str:
            self.current_keys.add(key_str)
            self._check_hotkeys()

    def _on_key_release(self, key):
        """Key-Release Event Handler"""
        if not self.is_active:
            return

        key_str = self._key_to_string(key)
        if key_str and key_str in self.current_keys:
            self.current_keys.remove(key_str)

    def _on_mouse_click(self, x, y, button, pressed):
        """Mouse-Click Event Handler für Maus-Hotkeys"""
        if not self.is_active:
            return

        button_str = self._mouse_button_to_string(button)
        if not button_str:
            return

        if pressed:
            # Maustaste gedrückt -> in aktuelle Kombi aufnehmen
            self.current_keys.add(button_str)
            self._check_hotkeys()
        else:
            # Maustaste losgelassen -> aus Kombi entfernen
            if button_str in self.current_keys:
                self.current_keys.remove(button_str)

    # --- Hotkey-Auswertung ---

    def _check_hotkeys(self):
        """Prüft, ob eine registrierte Hotkey-Kombination gedrückt wurde."""
        if not self.current_keys:
            return

        current_combo = "+".join(sorted(self.current_keys))

        # Debug-Callback immer informieren (falls aktiv)
        if self.debug_callback:
            self._safe_call(self.debug_callback, current_combo)

        for hotkey, callback in self.hotkeys.items():
            if current_combo == hotkey:
                # Callback in separatem Thread ausführen
                thread = threading.Thread(
                    target=self._safe_call,
                    args=(callback,),
                    daemon=True,
                )
                thread.start()

    @staticmethod
    def _safe_call(callback: Callable, *args, **kwargs):
        """Führt einen Callback sicher aus, ohne Hotkey-Thread zu crashen."""
        try:
            callback(*args, **kwargs)
        except Exception as e:
            print(f"Hotkey callback error: {e}")

    # --- Hilfsfunktionen ---

    def _key_to_string(self, key) -> str:
        """Konvertiert Keyboard-Key-Objekt zu einem String."""
        try:
            # Normale Zeichen (a, b, c, ...)
            return key.char.lower()
        except AttributeError:
            # Spezielle Tasten (Key.f1, Key.shift, ...)
            key_name = str(key).replace("Key.", "")
            return key_name.lower()

    def _mouse_button_to_string(self, button) -> str:
        """Konvertiert Mouse-Button-Objekt zu einem String.

        Wichtig: Die Namen müssen mit denen im GUI-Code übereinstimmen
        (macro_dialog, settings_tab, recorder_tab): mouse_left, mouse_x1, ...
        """
        mapping = {
            mouse.Button.left: "mouse_left",
            mouse.Button.right: "mouse_right",
            mouse.Button.middle: "mouse_middle",
            mouse.Button.x1: "mouse_x1",
            mouse.Button.x2: "mouse_x2",
        }
        return mapping.get(button, None)

    @staticmethod
    def parse_hotkey(hotkey_string: str) -> str:
        """Normalisiert Hotkey-String (Reihenfolge der Teile egal)."""
        parts = [part.strip().lower() for part in hotkey_string.split("+") if part.strip()]
        return "+".join(sorted(parts))

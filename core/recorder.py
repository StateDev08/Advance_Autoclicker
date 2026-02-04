"""
Makro-Recorder - Zeichnet Maus- und Tastaturaktionen auf
"""

from pynput import mouse, keyboard
from typing import List, Dict, Callable
import time
from datetime import datetime

class MacroRecorder:
    """Zeichnet Benutzeraktionen auf"""
    
    def __init__(self):
        self.is_recording = False
        self.actions: List[Dict] = []
        self.start_time = None
        self.last_action_time = None

        self.mouse_listener = None
        self.keyboard_listener = None

        self.on_action_callback = None
        
        # Aufnahme-Filter
        # record_mouse steuert Mausbewegungen und normale Buttons (Links/Rechts/Mitte).
        # Seitentasten (x1/x2) werden immer aufgezeichnet, damit sie als Makro-/Hotkey-
        # Tasten genutzt werden können – auch wenn "Maus" im UI deaktiviert ist.
        self.record_mouse = True
        self.record_keyboard = True

        # Minimale Zeit zwischen aufgezeichneten Mausbewegungen (in Sekunden)
        # Standard: 0.05s (50ms), kann über Einstellungen angepasst werden
        self.mouse_move_threshold = 0.05
    
    def start_recording(self, on_action: Callable = None):
        """Startet die Aufnahme"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.actions = []
        self.start_time = time.time()
        self.last_action_time = self.start_time
        self.on_action_callback = on_action
        
        # Maus-Listener immer starten, damit Seitentasten (x1/x2) auch dann
        # erkannt werden, wenn die normale Maus-Aufnahme im UI deaktiviert ist.
        # Ob eine Aktion tatsächlich aufgezeichnet wird, steuern wir in den
        # Handlern über self.record_mouse.
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self.mouse_listener.start()
        
        # Tastatur-Listener starten (nur wenn aktiviert)
        if self.record_keyboard:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.start()
    
    def stop_recording(self) -> List[Dict]:
        """Stoppt die Aufnahme und gibt die Aktionen zurück"""
        if not self.is_recording:
            return self.actions
        
        self.is_recording = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        return self.actions
    
    def _add_action(self, action: Dict):
        """Fügt eine Aktion zur Aufnahme hinzu"""
        current_time = time.time()
        delay = current_time - self.last_action_time
        
        action['delay'] = delay
        action['timestamp'] = current_time - self.start_time
        
        self.actions.append(action)
        self.last_action_time = current_time
        
        if self.on_action_callback:
            self.on_action_callback(action)
    
    def _on_mouse_move(self, x, y):
        """Mausbewegung aufzeichnen"""
        if not self.is_recording or not self.record_mouse:
            # Mausbewegungen nur aufzeichnen, wenn Maus-Aufnahme aktiv ist
            return
        
        # Nur bedeutende Bewegungen aufzeichnen (Schwelle in ms einstellbar)
        if len(self.actions) > 0:
            last_action = self.actions[-1]
            if (
                last_action.get('type') == 'mouse_move'
                and time.time() - self.last_action_time < self.mouse_move_threshold
            ):
                # Letzte Position aktualisieren statt neue Aktion
                last_action['x'] = x
                last_action['y'] = y
                return
        
        self._add_action({
            'type': 'mouse_move',
            'x': x,
            'y': y
        })
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Mausklick aufzeichnen"""
        if not self.is_recording:
            return

        # Wenn Maus-Aufnahme deaktiviert ist, nur Seitentasten (x1/x2) aufzeichnen,
        # damit diese als Makro-/Hotkey-Tasten nutzbar bleiben.
        if not self.record_mouse and button not in (mouse.Button.x1, mouse.Button.x2):
            return
        
        self._add_action({
            'type': 'mouse_click',
            'x': x,
            'y': y,
            'button': button.name,
            'pressed': pressed
        })
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Maus-Scroll aufzeichnen"""
        if not self.is_recording or not self.record_mouse:
            # Scroll nur aufzeichnen, wenn Maus-Aufnahme aktiv ist
            return
        
        self._add_action({
            'type': 'mouse_scroll',
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy
        })
    
    def _on_key_press(self, key):
        """Tastendruck aufzeichnen"""
        if not self.is_recording:
            return
        
        try:
            key_name = key.char
        except AttributeError:
            key_name = str(key)
        
        self._add_action({
            'type': 'key_press',
            'key': key_name
        })
    
    def _on_key_release(self, key):
        """Tastenloslassen aufzeichnen"""
        if not self.is_recording:
            return
        
        try:
            key_name = key.char
        except AttributeError:
            key_name = str(key)
        
        self._add_action({
            'type': 'key_release',
            'key': key_name
        })

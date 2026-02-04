"""
Window Detector - Erkennt aktive Fenster (Windows-spezifisch)
"""

import ctypes
from ctypes import wintypes
import time
from typing import Optional, Callable
import threading

# Windows API Funktionen
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class WindowDetector:
    """Erkennt und überwacht aktive Fenster"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.target_window = None
        self.on_window_change_callback = None
    
    @staticmethod
    def get_active_window_title() -> str:
        """Gibt den Titel des aktiven Fensters zurück"""
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        
        if length == 0:
            return ""
        
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value
    
    @staticmethod
    def get_active_window_class() -> str:
        """Gibt die Klasse des aktiven Fensters zurück"""
        hwnd = user32.GetForegroundWindow()
        buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buffer, 256)
        return buffer.value
    
    @staticmethod
    def get_active_window_process() -> str:
        """Gibt den Prozessnamen des aktiven Fensters zurück"""
        hwnd = user32.GetForegroundWindow()
        
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Process Handle öffnen
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        process_handle = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
            False,
            pid.value
        )
        
        if not process_handle:
            return ""
        
        try:
            # Prozessnamen abrufen
            buffer = ctypes.create_unicode_buffer(260)
            size = wintypes.DWORD(260)
            
            if kernel32.QueryFullProcessImageNameW(process_handle, 0, buffer, ctypes.byref(size)):
                return buffer.value.split('\\')[-1]
            return ""
        finally:
            kernel32.CloseHandle(process_handle)
    
    @staticmethod
    def get_active_window_info() -> dict:
        """Gibt alle Informationen zum aktiven Fenster zurück"""
        return {
            'title': WindowDetector.get_active_window_title(),
            'class': WindowDetector.get_active_window_class(),
            'process': WindowDetector.get_active_window_process()
        }
    
    @staticmethod
    def matches_filter(window_filter: str) -> bool:
        """Prüft ob das aktive Fenster dem Filter entspricht"""
        if not window_filter:
            return True
        
        info = WindowDetector.get_active_window_info()
        filter_lower = window_filter.lower()
        
        return (filter_lower in info['title'].lower() or
                filter_lower in info['class'].lower() or
                filter_lower in info['process'].lower())
    
    def start_monitoring(self, on_window_change: Callable = None, interval: float = 0.5):
        """Startet die Fensterüberwachung"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.on_window_change_callback = on_window_change
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_worker,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stoppt die Fensterüberwachung"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None
    
    def _monitor_worker(self, interval: float):
        """Worker-Thread für die Fensterüberwachung"""
        last_window = None
        
        while self.monitoring:
            try:
                current_window = self.get_active_window_info()
                
                if current_window != last_window:
                    if self.on_window_change_callback:
                        self.on_window_change_callback(current_window)
                    last_window = current_window
                
                time.sleep(interval)
            except Exception as e:
                print(f"Window monitoring error: {e}")
                time.sleep(interval)

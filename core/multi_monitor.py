"""
Multi-Monitor-Unterstützung
Erkennt und verwaltet mehrere Bildschirme
"""

import win32api
import win32con
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Monitor:
    """Repräsentiert einen Monitor"""
    index: int
    name: str
    x: int
    y: int
    width: int
    height: int
    is_primary: bool
    
    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Gibt Grenzen zurück (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)
    
    @property
    def center(self) -> Tuple[int, int]:
        """Gibt Mittelpunkt zurück"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def contains_point(self, x: int, y: int) -> bool:
        """Prüft ob Punkt auf diesem Monitor liegt"""
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)


class MultiMonitorManager:
    """Verwaltet Multi-Monitor-Setup"""
    
    def __init__(self):
        self.monitors: List[Monitor] = []
        self.refresh_monitors()
    
    def refresh_monitors(self):
        """Aktualisiert Monitor-Liste"""
        self.monitors.clear()
        
        # Alle Monitore abrufen
        monitors_info = win32api.EnumDisplayMonitors()
        
        for i, (hMonitor, hdcMonitor, rect) in enumerate(monitors_info):
            monitor_info = win32api.GetMonitorInfo(hMonitor)
            
            # Monitor-Daten extrahieren
            monitor_rect = monitor_info['Monitor']
            x, y, right, bottom = monitor_rect
            width = right - x
            height = bottom - y
            
            # Primärer Monitor?
            is_primary = monitor_info['Flags'] & win32con.MONITORINFOF_PRIMARY != 0
            
            # Device-Name
            device = monitor_info.get('Device', f'Monitor {i+1}')
            
            monitor = Monitor(
                index=i,
                name=device,
                x=x,
                y=y,
                width=width,
                height=height,
                is_primary=is_primary
            )
            
            self.monitors.append(monitor)
    
    def get_monitor_count(self) -> int:
        """Gibt Anzahl der Monitore zurück"""
        return len(self.monitors)
    
    def get_primary_monitor(self) -> Optional[Monitor]:
        """Gibt primären Monitor zurück"""
        for monitor in self.monitors:
            if monitor.is_primary:
                return monitor
        return self.monitors[0] if self.monitors else None
    
    def get_monitor_by_index(self, index: int) -> Optional[Monitor]:
        """Gibt Monitor nach Index zurück"""
        if 0 <= index < len(self.monitors):
            return self.monitors[index]
        return None
    
    def get_monitor_at_point(self, x: int, y: int) -> Optional[Monitor]:
        """Gibt Monitor an Position zurück"""
        for monitor in self.monitors:
            if monitor.contains_point(x, y):
                return monitor
        return None
    
    def convert_to_monitor_relative(self, x: int, y: int, monitor_index: int) -> Tuple[int, int]:
        """
        Konvertiert absolute Koordinaten zu Monitor-relativen Koordinaten
        
        Args:
            x, y: Absolute Bildschirm-Koordinaten
            monitor_index: Ziel-Monitor
            
        Returns:
            (x, y) relativ zum Monitor (0,0 = obere linke Ecke)
        """
        monitor = self.get_monitor_by_index(monitor_index)
        if monitor:
            return (x - monitor.x, y - monitor.y)
        return (x, y)
    
    def convert_to_absolute(self, x: int, y: int, monitor_index: int) -> Tuple[int, int]:
        """
        Konvertiert Monitor-relative zu absoluten Koordinaten
        
        Args:
            x, y: Koordinaten relativ zum Monitor
            monitor_index: Quell-Monitor
            
        Returns:
            (x, y) absolute Bildschirm-Koordinaten
        """
        monitor = self.get_monitor_by_index(monitor_index)
        if monitor:
            return (monitor.x + x, monitor.y + y)
        return (x, y)
    
    def get_virtual_screen_bounds(self) -> Tuple[int, int, int, int]:
        """
        Gibt Grenzen des virtuellen Bildschirms zurück
        (umfasst alle Monitore)
        
        Returns:
            (min_x, min_y, max_x, max_y)
        """
        if not self.monitors:
            return (0, 0, 0, 0)
        
        min_x = min(m.x for m in self.monitors)
        min_y = min(m.y for m in self.monitors)
        max_x = max(m.x + m.width for m in self.monitors)
        max_y = max(m.y + m.height for m in self.monitors)
        
        return (min_x, min_y, max_x, max_y)
    
    def get_total_resolution(self) -> Tuple[int, int]:
        """
        Gibt Gesamt-Auflösung über alle Monitore zurück
        
        Returns:
            (total_width, total_height)
        """
        min_x, min_y, max_x, max_y = self.get_virtual_screen_bounds()
        return (max_x - min_x, max_y - min_y)
    
    def get_monitor_info_text(self) -> str:
        """Gibt formatierte Monitor-Info zurück"""
        lines = [f"Monitore: {self.get_monitor_count()}"]
        
        for monitor in self.monitors:
            primary_marker = " [PRIMARY]" if monitor.is_primary else ""
            lines.append(
                f"  {monitor.index}: {monitor.width}x{monitor.height} "
                f"@ ({monitor.x}, {monitor.y}){primary_marker}"
            )
        
        return "\n".join(lines)

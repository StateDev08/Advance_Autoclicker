"""
Pixel-Farb-Erkennung
Sucht nach spezifischen Farben auf dem Bildschirm
"""

from PIL import ImageGrab
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PixelMatch:
    """Ergebnis einer Pixel-Suche"""
    x: int
    y: int
    color: Tuple[int, int, int]  # (R, G, B)
    distance: float  # Farbdistanz (0 = exakt)


class PixelDetector:
    """Erkennt Pixel-Farben auf dem Bildschirm"""
    
    def __init__(self):
        pass
    
    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """
        Gibt Farbe des Pixels an Position (x, y) zurück
        
        Returns:
            (R, G, B) Tuple
        """
        screenshot = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
        pixel = screenshot.getpixel((0, 0))
        return pixel[:3]  # RGB, ohne Alpha
    
    def color_distance(self, color1: Tuple[int, int, int], 
                      color2: Tuple[int, int, int]) -> float:
        """
        Berechnet Distanz zwischen zwei Farben (Euclidean)
        
        Returns:
            Distanz (0 = identisch, 441.67 = maximaler Unterschied)
        """
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        return np.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)
    
    def find_color(self, target_color: Tuple[int, int, int],
                   region: Optional[Tuple[int, int, int, int]] = None,
                   tolerance: int = 10) -> Optional[PixelMatch]:
        """
        Findet erstes Vorkommen einer Farbe
        
        Args:
            target_color: Gesuchte Farbe (R, G, B)
            region: Suchbereich (x, y, width, height) oder None für Vollbild
            tolerance: Toleranz (0 = exakt, höher = mehr Abweichung erlaubt)
            
        Returns:
            PixelMatch oder None
        """
        # Screenshot erstellen
        if region:
            x, y, width, height = region
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            offset_x, offset_y = x, y
        else:
            screenshot = ImageGrab.grab()
            offset_x, offset_y = 0, 0
        
        # Zu numpy array konvertieren
        img_array = np.array(screenshot)
        height, width = img_array.shape[:2]
        
        # Durch Pixel iterieren
        for y in range(height):
            for x in range(width):
                pixel_color = tuple(img_array[y, x][:3])  # RGB
                
                distance = self.color_distance(pixel_color, target_color)
                
                if distance <= tolerance:
                    return PixelMatch(
                        x=x + offset_x,
                        y=y + offset_y,
                        color=pixel_color,
                        distance=distance
                    )
        
        return None
    
    def find_all_colors(self, target_color: Tuple[int, int, int],
                       region: Optional[Tuple[int, int, int, int]] = None,
                       tolerance: int = 10,
                       max_results: int = 100) -> List[PixelMatch]:
        """
        Findet alle Vorkommen einer Farbe
        
        Args:
            target_color: Gesuchte Farbe (R, G, B)
            region: Suchbereich oder None für Vollbild
            tolerance: Toleranz
            max_results: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von PixelMatch
        """
        # Screenshot erstellen
        if region:
            x, y, width, height = region
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            offset_x, offset_y = x, y
        else:
            screenshot = ImageGrab.grab()
            offset_x, offset_y = 0, 0
        
        # Zu numpy array konvertieren
        img_array = np.array(screenshot)
        height, width = img_array.shape[:2]
        
        matches = []
        
        # Durch Pixel iterieren
        for y in range(height):
            for x in range(width):
                if len(matches) >= max_results:
                    break
                
                pixel_color = tuple(img_array[y, x][:3])  # RGB
                
                distance = self.color_distance(pixel_color, target_color)
                
                if distance <= tolerance:
                    matches.append(PixelMatch(
                        x=x + offset_x,
                        y=y + offset_y,
                        color=pixel_color,
                        distance=distance
                    ))
            
            if len(matches) >= max_results:
                break
        
        return matches
    
    def wait_for_color(self, target_color: Tuple[int, int, int],
                      x: int, y: int,
                      tolerance: int = 10,
                      timeout: float = 10.0,
                      check_interval: float = 0.1) -> bool:
        """
        Wartet bis ein Pixel eine bestimmte Farbe hat
        
        Args:
            target_color: Gesuchte Farbe (R, G, B)
            x, y: Position des zu überwachenden Pixels
            tolerance: Toleranz
            timeout: Maximale Wartezeit in Sekunden
            check_interval: Prüfintervall in Sekunden
            
        Returns:
            True wenn Farbe gefunden, False bei Timeout
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_color = self.get_pixel_color(x, y)
            distance = self.color_distance(current_color, target_color)
            
            if distance <= tolerance:
                return True
            
            time.sleep(check_interval)
        
        return False
    
    def color_to_hex(self, color: Tuple[int, int, int]) -> str:
        """
        Konvertiert RGB zu Hex-String
        
        Args:
            color: (R, G, B) Tuple
            
        Returns:
            Hex-String (z.B. "#FF0000")
        """
        r, g, b = color
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def hex_to_color(self, hex_str: str) -> Tuple[int, int, int]:
        """
        Konvertiert Hex-String zu RGB
        
        Args:
            hex_str: Hex-String (z.B. "#FF0000" oder "FF0000")
            
        Returns:
            (R, G, B) Tuple
        """
        # # entfernen falls vorhanden
        hex_str = hex_str.lstrip('#')
        
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        
        return (r, g, b)

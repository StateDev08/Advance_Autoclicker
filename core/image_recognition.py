"""
Bild-Erkennung mit OpenCV für Template Matching
Ermöglicht "Klicke auf Bild X" Aktionen
"""

import cv2
import numpy as np
from PIL import ImageGrab
import os
from typing import Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class ImageMatch:
    """Ergebnis einer Bild-Suche"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    @property
    def center(self) -> Tuple[int, int]:
        """Gibt den Mittelpunkt zurück"""
        return (self.x + self.width // 2, self.y + self.height // 2)


class ImageRecognition:
    """Bild-Erkennung für Template Matching"""
    
    def __init__(self, template_folder: str = "data/templates"):
        """Initialisiert die Bild-Erkennung"""
        self.template_folder = template_folder
        os.makedirs(template_folder, exist_ok=True)
        
        # Cache für geladene Templates
        self._template_cache = {}
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Erstellt einen Screenshot
        
        Args:
            region: Optional (x, y, width, height) für bestimmten Bereich
            
        Returns:
            Screenshot als numpy array (BGR Format für OpenCV)
        """
        if region:
            x, y, width, height = region
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        else:
            screenshot = ImageGrab.grab()
        
        # PIL Image zu numpy array (RGB)
        img_rgb = np.array(screenshot)
        
        # RGB zu BGR für OpenCV
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        
        return img_bgr
    
    def save_template(self, name: str, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Speichert einen Screenshot als Template
        
        Args:
            name: Name des Templates (ohne Dateiendung)
            region: Optional Bereich zum Erfassen
            
        Returns:
            Pfad zur gespeicherten Datei
        """
        screenshot = self.capture_screen(region)
        
        # Dateiname bereinigen
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        template_path = os.path.join(self.template_folder, f"{safe_name}.png")
        
        # Als PNG speichern
        cv2.imwrite(template_path, screenshot)
        
        # Cache leeren für dieses Template
        if safe_name in self._template_cache:
            del self._template_cache[safe_name]
        
        return template_path
    
    def load_template(self, name: str) -> Optional[np.ndarray]:
        """
        Lädt ein Template aus dem Cache oder von der Festplatte
        
        Args:
            name: Name des Templates (mit oder ohne .png)
            
        Returns:
            Template als numpy array oder None wenn nicht gefunden
        """
        # .png entfernen falls vorhanden
        if name.endswith('.png'):
            name = name[:-4]
        
        # Aus Cache laden
        if name in self._template_cache:
            return self._template_cache[name]
        
        # Von Festplatte laden
        template_path = os.path.join(self.template_folder, f"{name}.png")
        if not os.path.exists(template_path):
            return None
        
        template = cv2.imread(template_path)
        if template is None:
            return None
        
        # In Cache speichern
        self._template_cache[name] = template
        
        return template
    
    def find_template(self, template_name: str, confidence: float = 0.8,
                     region: Optional[Tuple[int, int, int, int]] = None,
                     grayscale: bool = True) -> Optional[ImageMatch]:
        """
        Sucht ein Template im Screenshot
        
        Args:
            template_name: Name des Templates
            confidence: Mindest-Übereinstimmung (0.0 - 1.0)
            region: Optional Suchbereich
            grayscale: Ob in Graustufen gesucht werden soll (schneller)
            
        Returns:
            ImageMatch mit Position und Konfidenz oder None
        """
        # Template laden
        template = self.load_template(template_name)
        if template is None:
            return None
        
        # Screenshot erstellen
        screenshot = self.capture_screen(region)
        
        # Optional in Graustufen konvertieren (schneller)
        if grayscale:
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Template Matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        
        # Beste Übereinstimmung finden
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Prüfen ob Konfidenz ausreichend
        if max_val < confidence:
            return None
        
        # Position berechnen (relativ zum Suchbereich)
        x, y = max_loc
        h, w = template.shape[:2]
        
        # Bei regionalem Suchbereich Offset addieren
        if region:
            x += region[0]
            y += region[1]
        
        return ImageMatch(
            x=x,
            y=y,
            width=w,
            height=h,
            confidence=max_val
        )
    
    def find_all_templates(self, template_name: str, confidence: float = 0.8,
                          region: Optional[Tuple[int, int, int, int]] = None,
                          grayscale: bool = True) -> List[ImageMatch]:
        """
        Findet alle Vorkommen eines Templates
        
        Args:
            template_name: Name des Templates
            confidence: Mindest-Übereinstimmung (0.0 - 1.0)
            region: Optional Suchbereich
            grayscale: Ob in Graustufen gesucht werden soll
            
        Returns:
            Liste von ImageMatch Objekten
        """
        # Template laden
        template = self.load_template(template_name)
        if template is None:
            return []
        
        # Screenshot erstellen
        screenshot = self.capture_screen(region)
        
        # Optional in Graustufen konvertieren
        if grayscale:
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Template Matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        
        # Alle Übereinstimmungen über Schwellwert finden
        locations = np.where(result >= confidence)
        
        matches = []
        h, w = template.shape[:2]
        
        # Überlappende Ergebnisse zusammenfassen
        points = list(zip(*locations[::-1]))
        
        # Non-Maximum Suppression für überlappende Matches
        if points:
            # Sortieren nach Konfidenz (absteigend)
            points_with_conf = [(pt, result[pt[1], pt[0]]) for pt in points]
            points_with_conf.sort(key=lambda x: x[1], reverse=True)
            
            for (x, y), conf in points_with_conf:
                # Prüfen ob zu nah an existierendem Match
                overlap = False
                for match in matches:
                    if abs(x - match.x) < w * 0.5 and abs(y - match.y) < h * 0.5:
                        overlap = True
                        break
                
                if not overlap:
                    # Bei regionalem Suchbereich Offset addieren
                    final_x = x + (region[0] if region else 0)
                    final_y = y + (region[1] if region else 0)
                    
                    matches.append(ImageMatch(
                        x=final_x,
                        y=final_y,
                        width=w,
                        height=h,
                        confidence=conf
                    ))
        
        return matches
    
    def wait_for_template(self, template_name: str, timeout: float = 10.0,
                         confidence: float = 0.8, check_interval: float = 0.5,
                         region: Optional[Tuple[int, int, int, int]] = None) -> Optional[ImageMatch]:
        """
        Wartet bis ein Template erscheint (mit Timeout)
        
        Args:
            template_name: Name des Templates
            timeout: Maximale Wartezeit in Sekunden
            confidence: Mindest-Übereinstimmung
            check_interval: Prüfintervall in Sekunden
            region: Optional Suchbereich
            
        Returns:
            ImageMatch oder None bei Timeout
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            match = self.find_template(template_name, confidence, region)
            if match:
                return match
            
            time.sleep(check_interval)
        
        return None
    
    def list_templates(self) -> List[str]:
        """
        Listet alle verfügbaren Templates auf
        
        Returns:
            Liste von Template-Namen (ohne .png)
        """
        if not os.path.exists(self.template_folder):
            return []
        
        templates = []
        for file in os.listdir(self.template_folder):
            if file.endswith('.png'):
                templates.append(file[:-4])
        
        return sorted(templates)
    
    def delete_template(self, name: str) -> bool:
        """
        Löscht ein Template
        
        Args:
            name: Name des Templates
            
        Returns:
            True bei Erfolg
        """
        if name.endswith('.png'):
            name = name[:-4]
        
        template_path = os.path.join(self.template_folder, f"{name}.png")
        
        if os.path.exists(template_path):
            os.remove(template_path)
            
            # Aus Cache entfernen
            if name in self._template_cache:
                del self._template_cache[name]
            
            return True
        
        return False

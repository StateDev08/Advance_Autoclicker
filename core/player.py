"""
Makro-Player - Spielt aufgezeichnete Aktionen ab
Unterstützt: Bild-Erkennung, Variablen, Bedingungen, Schleifen
"""

from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
from typing import List, Dict, Callable, Optional, Any, Tuple
import time
import threading
import random

from core.image_recognition import ImageRecognition
from core.pixel_detection import PixelDetector
from core.variables import VariableManager, ConditionEvaluator
from core.logging_system import get_logger
from core.multi_monitor import MultiMonitorManager

class MacroPlayer:
    """Spielt Makro-Aktionen ab mit erweiterten Features"""
    
    def __init__(self):
        self.is_playing = False
        self.should_stop = False
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.play_thread = None
        
        self.on_progress_callback = None
        self.on_complete_callback = None
        
        # Neue Features
        self.image_recognition = ImageRecognition()
        self.pixel_detector = PixelDetector()
        self.multi_monitor = MultiMonitorManager()
        self.variable_manager = VariableManager()
        self.condition_evaluator = ConditionEvaluator(self.variable_manager)
        self.logger = get_logger()
        
        # Ausführungs-Kontext
        self.current_loop = 0
        self.current_action = 0
        self.paused = False
        self._jump_to_index: Optional[int] = None  # Für jump_to_action
        # Anti-Erkennung (von außen gesetzt, z. B. aus Einstellungen)
        self.humanize_click_offset = False
        self.humanize_delay_before_action: Optional[Tuple[float, float]] = None  # (min_sec, max_sec) oder None
    
    def _apply_click_offset(self, x: int, y: int) -> Tuple[int, int]:
        """Wendet kleinen Zufalls-Offset auf Klickposition an (Anti-Erkennung)."""
        if not self.humanize_click_offset:
            return (x, y)
        dx = random.randint(-3, 3)
        dy = random.randint(-3, 3)
        return (x + dx, y + dy)
    
    def play(self, actions: List[Dict], loop_count: int = 1, 
             loop_infinite: bool = False, delay_between_loops: float = 0.0,
             speed_multiplier: float = 1.0,
             on_progress: Callable = None, on_complete: Callable = None):
        """Spielt Aktionen ab"""
        if self.is_playing:
            return
        
        self.on_progress_callback = on_progress
        self.on_complete_callback = on_complete
        
        self.play_thread = threading.Thread(
            target=self._play_worker,
            args=(actions, loop_count, loop_infinite, delay_between_loops, speed_multiplier),
            daemon=True
        )
        self.play_thread.start()
    
    def stop(self):
        """Stoppt die Wiedergabe"""
        self.should_stop = True
        self.paused = False
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=2.0)
        self.is_playing = False

    def pause(self):
        """Pausiert die Wiedergabe (bis resume())."""
        self.paused = True
        self.logger.info("Makro-Wiedergabe pausiert")

    def resume(self):
        """Setzt pausierte Wiedergabe fort."""
        self.paused = False
        self.logger.info("Makro-Wiedergabe fortgesetzt")
    
    def _play_worker(self, actions: List[Dict], loop_count: int, 
                     loop_infinite: bool, delay_between_loops: float,
                     speed_multiplier: float):
        """Worker-Thread für die Wiedergabe"""
        self.is_playing = True
        self.should_stop = False
        self.paused = False
        self._jump_to_index = None
        
        # Variablen zurücksetzen
        self.variable_manager.reset()
        self.variable_manager.set('loop_count', loop_count)
        self.variable_manager.set('action_count', len(actions))
        
        self.current_loop = 0
        start_time = time.time()
        
        try:
            self.logger.log_macro_start("Makro", loop_count if not loop_infinite else -1)
            
            while (loop_infinite or self.current_loop < loop_count) and not self.should_stop:
                self.variable_manager.set('current_loop', self.current_loop + 1)
                
                i = 0
                while i < len(actions):
                    if self.should_stop:
                        break
                    while self.paused and not self.should_stop:
                        time.sleep(0.1)
                    
                    action = actions[i]
                    self.current_action = i
                    self.variable_manager.set('current_action', i + 1)
                    
                    # Verzögerung vor der Aktion
                    delay = action.get('delay', 0) / speed_multiplier
                    if delay > 0:
                        time.sleep(delay)
                    # Anti-Erkennung: Zufalls-Delay vor Aktion
                    if self.humanize_delay_before_action:
                        min_s, max_s = self.humanize_delay_before_action
                        time.sleep(random.uniform(min_s, max_s))
                    
                    # Aktion ausführen (mit Fehlerbehandlung)
                    try:
                        self._execute_action(action)
                    except Exception as e:
                        self.logger.log_exception(e, f"Action {i+1}")
                    
                    # Sprung zu Aktion (jump_to_action)
                    if self._jump_to_index is not None:
                        i = self._jump_to_index
                        self._jump_to_index = None
                    else:
                        i += 1
                    
                    # Fortschritt melden
                    if self.on_progress_callback:
                        if loop_infinite or loop_count <= 0 or len(actions) == 0:
                            # Endlos oder leeres Makro: kein sinnvolles Prozent, 100% = "läuft"
                            progress = 100.0
                        else:
                            total = loop_count * len(actions)
                            progress = min(100.0, ((self.current_loop * len(actions) + i + 1) / total) * 100)
                        self.on_progress_callback(progress, self.current_loop + 1, i + 1)
                
                if self.should_stop:
                    break
                
                self.current_loop += 1
                
                # Verzögerung zwischen Loops
                if (loop_infinite or self.current_loop < loop_count) and delay_between_loops > 0:
                    time.sleep(delay_between_loops)
            
            # Erfolg loggen
            duration = time.time() - start_time
            self.logger.log_macro_end("Makro", not self.should_stop, duration)
        
        except Exception as e:
            self.logger.log_exception(e, "Makro-Wiedergabe")
        
        finally:
            self.is_playing = False
            if self.on_complete_callback:
                self.on_complete_callback()
    
    def _execute_action(self, action: Dict):
        """Führt eine einzelne Aktion aus (erweitert)"""
        action_type = action.get('type')
        
        # Neue Action-Typen mit erweiterten Features
        if action_type == 'set_variable':
            self._action_set_variable(action)
        
        elif action_type == 'if_condition':
            self._action_if_condition(action)
        
        elif action_type == 'wait_for_image':
            self._action_wait_for_image(action)
        
        elif action_type == 'click_on_image':
            self._action_click_on_image(action)
        
        elif action_type == 'wait':
            self._action_wait(action)
        
        elif action_type == 'log_message':
            self._action_log_message(action)
        
        elif action_type == 'type_text':
            self._action_type_text(action)
        
        elif action_type == 'double_click':
            self._action_double_click(action)
        
        elif action_type == 'wait_for_pixel_color':
            self._action_wait_for_pixel_color(action)
        
        elif action_type == 'click_at_color':
            self._action_click_at_color(action)
        
        elif action_type == 'wait_for_any_color':
            self._action_wait_for_any_color(action)
        
        elif action_type == 'click_at_any_color':
            self._action_click_at_any_color(action)
        
        elif action_type == 'random_delay':
            self._action_random_delay(action)
        elif action_type == 'reaction_delay':
            self._action_reaction_delay(action)
        elif action_type == 'wait_for_health_color':
            self._action_wait_for_health_color(action)
        elif action_type == 'click_at_health_color':
            self._action_click_at_health_color(action)
        elif action_type == 'cooldown_wait':
            self._action_cooldown_wait(action)
        
        elif action_type == 'human_mouse_move':
            self._action_human_mouse_move(action)
        elif action_type == 'hold_key':
            self._action_hold_key(action)
        elif action_type == 'release_key':
            self._action_release_key(action)
        elif action_type == 'mouse_drag':
            self._action_mouse_drag(action)
        elif action_type == 'wait_for_image_region':
            self._action_wait_for_image_region(action)
        elif action_type == 'random_click_region':
            self._action_random_click_region(action)
        elif action_type == 'key_sequence':
            self._action_key_sequence(action)
        elif action_type == 'jump_to_action':
            self._action_jump_to_action(action)
        
        # Bestehende Action-Typen
        elif action_type == 'mouse_move':
            x = action.get('x', 0)
            y = action.get('y', 0)
            if isinstance(x, str):
                x = int(self.variable_manager.evaluate(x))
            if isinstance(y, str):
                y = int(self.variable_manager.evaluate(y))
            x, y = self._resolve_xy(x, y, action)
            self.mouse_controller.position = (x, y)
            self.logger.log_macro_action('mouse_move', f'({x}, {y})')
        
        elif action_type == 'mouse_click':
            x = action.get('x', 0)
            y = action.get('y', 0)
            button_name = str(action.get('button', 'left')).lower()
            pressed = action.get('pressed', True)
            if isinstance(x, str):
                x = int(self.variable_manager.evaluate(x))
            if isinstance(y, str):
                y = int(self.variable_manager.evaluate(y))
            x, y = self._resolve_xy(x, y, action)
            x, y = self._apply_click_offset(x, y)
            self.mouse_controller.position = (x, y)
            
            # Standard: linke Maustaste
            button = Button.left
            if button_name in ("left", "mouse_left"):
                button = Button.left
            elif button_name in ("right", "mouse_right"):
                button = Button.right
            elif button_name in ("middle", "mouse_middle"):
                button = Button.middle
            elif button_name in ("x1", "mouse_x1", "button8"):
                try:
                    button = Button.x1
                except AttributeError:
                    button = Button.right
            elif button_name in ("x2", "mouse_x2", "button9"):
                try:
                    return self.mouse_controller.press(Button.x2) if pressed else self.mouse_controller.release(Button.x2)
                except AttributeError:
                    button = Button.right
            
            if pressed:
                self.mouse_controller.press(button)
            else:
                self.mouse_controller.release(button)
            
            self.logger.log_macro_action('mouse_click', f'{button_name} at ({x}, {y})')
        
        elif action_type == 'mouse_scroll':
            x = action.get('x', 0)
            y = action.get('y', 0)
            dx = action.get('dx', 0)
            dy = action.get('dy', 0)
            if isinstance(x, str):
                x = int(self.variable_manager.evaluate(x))
            if isinstance(y, str):
                y = int(self.variable_manager.evaluate(y))
            if isinstance(dx, str):
                dx = int(self.variable_manager.evaluate(dx))
            if isinstance(dy, str):
                dy = int(self.variable_manager.evaluate(dy))
            x, y = self._resolve_xy(x, y, action)
            self.mouse_controller.position = (x, y)
            self.mouse_controller.scroll(dx, dy)
            self.logger.log_macro_action('mouse_scroll', f'dx={dx}, dy={dy}')
        
        elif action_type == 'key_press':
            key_name = action.get('key')
            key = self._parse_key(key_name)
            if key:
                self.keyboard_controller.press(key)
                self.logger.log_macro_action('key_press', key_name)
        
        elif action_type == 'key_release':
            key_name = action.get('key')
            key = self._parse_key(key_name)
            if key:
                self.keyboard_controller.release(key)
                self.logger.log_macro_action('key_release', key_name)
        
        else:
            self.logger.warning(f"Unbekannter Action-Typ: {action_type}")
    
    def _resolve_xy(self, x: int, y: int, action: Dict) -> tuple:
        """Konvertiert (x,y) zu absoluten Koordinaten wenn action monitor_id hat."""
        monitor_id = action.get('monitor_id')
        if monitor_id is not None:
            return self.multi_monitor.convert_to_absolute(int(x), int(y), int(monitor_id))
        return (int(x), int(y))
    
    # Neue Action-Handler
    def _action_set_variable(self, action: Dict):
        """Setzt eine Variable"""
        var_name = action.get('name', '')
        var_value = action.get('value', '')
        
        # Wert auswerten (kann Ausdruck sein)
        if isinstance(var_value, str):
            try:
                evaluated = self.variable_manager.evaluate(var_value)
                self.variable_manager.set(var_name, evaluated)
                self.logger.log_macro_action('set_variable', f'{var_name} = {evaluated}')
            except Exception as e:
                self.logger.error(f"Fehler beim Setzen von {var_name}: {e}")
        else:
            self.variable_manager.set(var_name, var_value)
            self.logger.log_macro_action('set_variable', f'{var_name} = {var_value}')
    
    def _action_if_condition(self, action: Dict):
        """Führt bedingte Aktionen aus"""
        condition = action.get('condition', '')
        true_actions = action.get('true_actions', [])
        false_actions = action.get('false_actions', [])
        
        # Bedingung auswerten
        result = self.condition_evaluator.evaluate_condition(condition)
        self.logger.log_macro_action('if_condition', f'{condition} = {result}')
        
        # Entsprechende Aktionen ausführen
        actions_to_execute = true_actions if result else false_actions
        for sub_action in actions_to_execute:
            if self.should_stop:
                break
            self._execute_action(sub_action)
    
    def _action_wait_for_image(self, action: Dict):
        """Wartet bis ein Bild erscheint"""
        template_name = action.get('template', '')
        timeout = action.get('timeout', 10.0)
        confidence = action.get('confidence', 0.8)
        
        self.logger.log_macro_action('wait_for_image', f'{template_name} (timeout={timeout}s)')
        
        match = self.image_recognition.wait_for_template(
            template_name,
            timeout=timeout,
            confidence=confidence
        )
        
        if match:
            # Position in Variablen speichern
            self.variable_manager.set('image_x', match.center[0])
            self.variable_manager.set('image_y', match.center[1])
            self.variable_manager.set('image_found', True)
            self.logger.log_macro_action('wait_for_image', f'Gefunden bei ({match.center[0]}, {match.center[1]})')
        else:
            self.variable_manager.set('image_found', False)
            self.logger.warning(f'Bild {template_name} nicht gefunden innerhalb {timeout}s')
    
    def _action_click_on_image(self, action: Dict):
        """Klickt auf ein Bild (optional: match_index für n-tes Vorkommen, 0-basiert)."""
        template_name = action.get('template', '')
        confidence = action.get('confidence', 0.8)
        button = action.get('button', 'left')
        offset_x = action.get('offset_x', 0)
        offset_y = action.get('offset_y', 0)
        match_index = action.get('match_index')
        region = action.get('region')  # Optional (x, y, width, height) für Suchbereich
        if isinstance(region, (list, tuple)) and len(region) >= 4:
            region = tuple(int(v) for v in region[:4])
        
        self.logger.log_macro_action('click_on_image', template_name)
        
        if match_index is not None:
            matches = self.image_recognition.find_all_templates(
                template_name, confidence=confidence, region=region
            )
            idx = int(match_index)
            match = matches[idx] if 0 <= idx < len(matches) else None
        else:
            match = self.image_recognition.find_template(
                template_name, confidence=confidence, region=region
            )
        
        if match:
            # Auf Mittelpunkt klicken (mit optionalem Offset)
            x = int(match.center[0] + offset_x)
            y = int(match.center[1] + offset_y)
            x, y = self._apply_click_offset(x, y)
            self.mouse_controller.position = (x, y)
            
            # Button bestimmen
            btn = Button.left
            if button == 'right':
                btn = Button.right
            elif button == 'middle':
                btn = Button.middle
            
            self.mouse_controller.click(btn)
            
            self.variable_manager.set('image_found', True)
            self.logger.log_macro_action('click_on_image', f'Geklickt bei ({x}, {y})')
        else:
            self.variable_manager.set('image_found', False)
            self.logger.warning(f'Bild {template_name} nicht gefunden')
    
    def _action_wait(self, action: Dict):
        """Wartet eine bestimmte Zeit"""
        duration = action.get('duration', 1.0)
        
        # Variablen in Duration unterstützen
        if isinstance(duration, str):
            duration = float(self.variable_manager.evaluate(duration))
        
        self.logger.log_macro_action('wait', f'{duration}s')
        time.sleep(duration)
    
    def _action_log_message(self, action: Dict):
        """Loggt eine Nachricht"""
        message = action.get('message', '')
        level = action.get('level', 'info')
        
        # Variablen in Nachricht ersetzen
        if isinstance(message, str) and '{' in message:
            try:
                message = self.variable_manager.evaluate(message)
            except Exception:
                pass  # Falls nicht auswertbar, original nutzen
        
        if level == 'debug':
            self.logger.debug(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def _parse_color(self, color_spec: Any) -> tuple:
        """Konvertiert Farbangabe (Liste, Tuple, Hex-String oder "r,g,b") zu (R, G, B)."""
        if color_spec is None:
            return (0, 0, 0)
        if isinstance(color_spec, (list, tuple)) and len(color_spec) >= 3:
            return (int(color_spec[0]), int(color_spec[1]), int(color_spec[2]))
        if isinstance(color_spec, str):
            s = color_spec.strip()
            if s.startswith('#'):
                return self.pixel_detector.hex_to_color(s)
            parts = [p.strip() for p in s.split(',')]
            if len(parts) >= 3:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
        return (0, 0, 0)
    
    def _action_type_text(self, action: Dict):
        """Gibt Text ein (mit Variablen-Ersetzung)."""
        text = action.get('text', '')
        if isinstance(text, str) and '{' in text:
            try:
                text = str(self.variable_manager.evaluate(text))
            except Exception:
                pass
        text = str(text)
        self.logger.log_macro_action('type_text', repr(text)[:50])
        for char in text:
            if self.should_stop:
                break
            if char == '\n':
                self.keyboard_controller.press(Key.enter)
                self.keyboard_controller.release(Key.enter)
            elif char == '\t':
                self.keyboard_controller.press(Key.tab)
                self.keyboard_controller.release(Key.tab)
            else:
                try:
                    self.keyboard_controller.type(char)
                except Exception:
                    pass
    
    def _action_double_click(self, action: Dict):
        """Doppelklick an Position."""
        x = action.get('x', 0)
        y = action.get('y', 0)
        button_name = str(action.get('button', 'left')).lower()
        if isinstance(x, str):
            x = int(self.variable_manager.evaluate(x))
        if isinstance(y, str):
            y = int(self.variable_manager.evaluate(y))
        x, y = self._resolve_xy(x, y, action)
        x, y = self._apply_click_offset(x, y)
        self.mouse_controller.position = (x, y)
        btn = Button.left
        if button_name in ("right", "mouse_right"):
            btn = Button.right
        elif button_name in ("middle", "mouse_middle"):
            btn = Button.middle
        self.mouse_controller.click(btn, 2)
        self.logger.log_macro_action('double_click', f'at ({x}, {y})')
    
    def _action_wait_for_pixel_color(self, action: Dict):
        """Wartet bis Pixel an (x,y) die Farbe hat, oder bis Farbe in Region erscheint (wenn region gesetzt)."""
        color = self._parse_color(action.get('color'))
        tolerance = int(action.get('tolerance', 10))
        timeout = float(action.get('timeout', 10.0))
        region = action.get('region')
        # Region parsen: (x, y, width, height) für PixelDetector
        if isinstance(region, str) and region.strip():
            try:
                parts = [int(p.strip()) for p in region.split(',')]
                if len(parts) >= 4:
                    region = (parts[0], parts[1], parts[2] - parts[0], parts[3] - parts[1])
                else:
                    region = None
            except (ValueError, IndexError):
                region = None
        elif isinstance(region, (list, tuple)) and len(region) >= 4:
            x1, y1, x2, y2 = region[0], region[1], region[2], region[3]
            region = (x1, y1, x2 - x1, y2 - y1)
        if region is not None:
            self.logger.log_macro_action('wait_for_pixel_color', f'region={region} color={color} timeout={timeout}s')
            match = self.pixel_detector.wait_for_color_in_region(
                color, region=region, tolerance=tolerance, timeout=timeout
            )
            found = match is not None
            self.variable_manager.set('pixel_color_found', found)
            if match:
                self.variable_manager.set('pixel_color_x', match.x)
                self.variable_manager.set('pixel_color_y', match.y)
            if not found:
                self.logger.warning(f'Pixelfarbe in Region nicht innerhalb {timeout}s gefunden')
            return
        x = action.get('x', 0)
        y = action.get('y', 0)
        if isinstance(x, str):
            x = int(self.variable_manager.evaluate(x))
        if isinstance(y, str):
            y = int(self.variable_manager.evaluate(y))
        self.logger.log_macro_action('wait_for_pixel_color', f'({x},{y}) color={color} timeout={timeout}s')
        found = self.pixel_detector.wait_for_color(color, x, y, tolerance=tolerance, timeout=timeout)
        self.variable_manager.set('pixel_color_found', found)
        if not found:
            self.logger.warning(f'Pixelfarbe bei ({x},{y}) nicht innerhalb {timeout}s gefunden')
    
    def _action_click_at_color(self, action: Dict):
        """Findet erste Farbe in Region und klickt darauf."""
        color = self._parse_color(action.get('color'))
        tolerance = int(action.get('tolerance', 10))
        region = action.get('region')  # None = Vollbild, oder (x, y, width, height) / (x1,y1,x2,y2)
        if isinstance(region, str) and region.strip():
            try:
                parts = [int(p.strip()) for p in region.split(',')]
                if len(parts) >= 4:
                    region = (parts[0], parts[1], parts[2] - parts[0], parts[3] - parts[1])
                else:
                    region = None
            except (ValueError, IndexError):
                region = None
        if isinstance(region, (list, tuple)) and len(region) >= 4:
            # (x1, y1, x2, y2) -> (x, y, width, height)
            x1, y1, x2, y2 = region[0], region[1], region[2], region[3]
            region = (x1, y1, x2 - x1, y2 - y1)
        button_name = str(action.get('button', 'left')).lower()
        self.logger.log_macro_action('click_at_color', f'color={color} tolerance={tolerance}')
        match = self.pixel_detector.find_color(color, region=region, tolerance=tolerance)
        if match:
            cx, cy = self._apply_click_offset(match.x, match.y)
            self.mouse_controller.position = (cx, cy)
            btn = Button.left
            if button_name in ("right", "mouse_right"):
                btn = Button.right
            elif button_name in ("middle", "mouse_middle"):
                btn = Button.middle
            self.mouse_controller.click(btn)
            self.variable_manager.set('color_click_x', match.x)
            self.variable_manager.set('color_click_y', match.y)
            self.logger.log_macro_action('click_at_color', f'Geklickt bei ({match.x}, {match.y})')
        else:
            self.logger.warning('Farbe nicht gefunden')
    
    def _parse_region(self, region: Any) -> Optional[Tuple[int, int, int, int]]:
        """Konvertiert region zu (x, y, width, height) oder None."""
        if region is None:
            return None
        if isinstance(region, str) and region.strip():
            try:
                parts = [int(p.strip()) for p in region.split(',')]
                if len(parts) >= 4:
                    return (parts[0], parts[1], parts[2] - parts[0], parts[3] - parts[1])
            except (ValueError, IndexError):
                pass
            return None
        if isinstance(region, (list, tuple)) and len(region) >= 4:
            x1, y1, x2, y2 = region[0], region[1], region[2], region[3]
            return (x1, y1, x2 - x1, y2 - y1)
        return None
    
    def _action_wait_for_any_color(self, action: Dict):
        """Wartet bis eine beliebige Farbe aus der Liste in der Region erscheint."""
        colors_spec = action.get('colors', [])
        if not colors_spec:
            self.logger.warning('wait_for_any_color: keine Farben angegeben')
            return
        colors = [self._parse_color(c) for c in colors_spec]
        tolerance = int(action.get('tolerance', 10))
        timeout = float(action.get('timeout', 10.0))
        check_interval = float(action.get('check_interval', 0.2))
        region = self._parse_region(action.get('region'))
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.should_stop:
                return
            result = self.pixel_detector.find_first_of_colors(colors, region=region, tolerance=tolerance)
            if result:
                match, color_index = result
                self.variable_manager.set('matched_color_index', color_index)
                self.variable_manager.set('pixel_x', match.x)
                self.variable_manager.set('pixel_y', match.y)
                self.variable_manager.set('pixel_color_found', True)
                self.logger.log_macro_action('wait_for_any_color', f'Farbe {color_index} bei ({match.x},{match.y})')
                return
            time.sleep(check_interval)
        self.variable_manager.set('pixel_color_found', False)
        self.logger.warning(f'wait_for_any_color: keine der Farben innerhalb {timeout}s gefunden')
    
    def _action_click_at_any_color(self, action: Dict):
        """Klickt auf die erste gefundene Farbe aus der Liste (Priorität: Reihenfolge)."""
        colors_spec = action.get('colors', [])
        if not colors_spec:
            self.logger.warning('click_at_any_color: keine Farben angegeben')
            return
        colors = [self._parse_color(c) for c in colors_spec]
        tolerance = int(action.get('tolerance', 10))
        region = self._parse_region(action.get('region'))
        button_name = str(action.get('button', 'left')).lower()
        self.logger.log_macro_action('click_at_any_color', f'{len(colors)} Farben, tolerance={tolerance}')
        result = self.pixel_detector.find_first_of_colors(colors, region=region, tolerance=tolerance)
        if result:
            match, color_index = result
            cx, cy = self._apply_click_offset(match.x, match.y)
            self.mouse_controller.position = (cx, cy)
            btn = Button.left
            if button_name in ("right", "mouse_right"):
                btn = Button.right
            elif button_name in ("middle", "mouse_middle"):
                btn = Button.middle
            self.mouse_controller.click(btn)
            self.variable_manager.set('color_click_x', match.x)
            self.variable_manager.set('color_click_y', match.y)
            self.variable_manager.set('matched_color_index', color_index)
            self.logger.log_macro_action('click_at_any_color', f'Farbe {color_index} bei ({match.x}, {match.y})')
        else:
            self.logger.warning('click_at_any_color: keine der Farben gefunden')
    
    def _action_random_delay(self, action: Dict):
        """Verzögerung mit Zufallsbereich (Anti-Pattern)."""
        min_sec = float(action.get('min_sec', 0.5))
        max_sec = float(action.get('max_sec', 1.5))
        sec = random.uniform(min_sec, max_sec)
        self.logger.log_macro_action('random_delay', f'{sec:.2f}s')
        time.sleep(sec)
    
    def _action_reaction_delay(self, action: Dict):
        """Kurze menschliche Reaktionszeit (min–max ms)."""
        min_ms = int(action.get('min_ms', 50))
        max_ms = int(action.get('max_ms', 200))
        sec = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
        self.logger.log_macro_action('reaction_delay', f'{sec*1000:.0f}ms')
        time.sleep(sec)
    
    def _action_wait_for_health_color(self, action: Dict):
        """Warte auf eine von mehreren Farben (z. B. Lebensbalken); optional variable_prefix."""
        prefix = (action.get('variable_prefix') or '').strip()
        self._action_wait_for_any_color(action)
        if prefix and self.variable_manager.get('pixel_color_found'):
            self.variable_manager.set(prefix + 'index', self.variable_manager.get('matched_color_index'))
            self.variable_manager.set(prefix + 'x', self.variable_manager.get('pixel_x'))
            self.variable_manager.set(prefix + 'y', self.variable_manager.get('pixel_y'))
    
    def _action_click_at_health_color(self, action: Dict):
        """Klick auf erste gefundene Farbe aus Liste (z. B. Potion-Button)."""
        self._action_click_at_any_color(action)
    
    def _action_cooldown_wait(self, action: Dict):
        """Zufällige Wartezeit für Skill-Cooldowns."""
        min_sec = float(action.get('min_sec', 1.0))
        max_sec = float(action.get('max_sec', 5.0))
        sec = random.uniform(min_sec, max_sec)
        self.logger.log_macro_action('cooldown_wait', f'{sec:.2f}s')
        time.sleep(sec)
    
    def _action_human_mouse_move(self, action: Dict):
        """Maus in Schritten mit leichter Zufallsabweichung bewegen (menschlicher)."""
        x = action.get('x', 0)
        y = action.get('y', 0)
        if isinstance(x, str):
            x = int(self.variable_manager.evaluate(x))
        if isinstance(y, str):
            y = int(self.variable_manager.evaluate(y))
        x, y = self._resolve_xy(x, y, action)
        steps = max(5, int(action.get('steps', 10)))
        step_delay = float(action.get('step_delay', 0.03))
        jitter = int(action.get('jitter', 2))
        cur = self.mouse_controller.position
        x0, y0 = cur[0], cur[1]
        for i in range(1, steps + 1):
            if self.should_stop:
                return
            t = i / steps
            px = int(x0 + (x - x0) * t + random.randint(-jitter, jitter))
            py = int(y0 + (y - y0) * t + random.randint(-jitter, jitter))
            self.mouse_controller.position = (px, py)
            time.sleep(step_delay)
        self.mouse_controller.position = (x, y)
        self.logger.log_macro_action('human_mouse_move', f'({x}, {y})')
    
    def _action_hold_key(self, action: Dict):
        """Taste gedrückt halten für duration_ms, dann loslassen (z.B. Sprint)."""
        key_name = action.get('key', '')
        duration_ms = float(action.get('duration_ms', 500))
        key = self._parse_key(key_name)
        if key:
            self.keyboard_controller.press(key)
            self.logger.log_macro_action('hold_key', f'{key_name} {duration_ms}ms')
            time.sleep(duration_ms / 1000.0)
            self.keyboard_controller.release(key)
    
    def _action_release_key(self, action: Dict):
        """Taste explizit loslassen (Sicherheit nach hold_key)."""
        key_name = action.get('key', '')
        key = self._parse_key(key_name)
        if key:
            self.keyboard_controller.release(key)
            self.logger.log_macro_action('release_key', key_name)
    
    def _action_mouse_drag(self, action: Dict):
        """Maus von (x1,y1) nach (x2,y2) ziehen (Button gedrückt). Optional human_move."""
        x1 = action.get('x1', 0)
        y1 = action.get('y1', 0)
        x2 = action.get('x2', 0)
        y2 = action.get('y2', 0)
        button = action.get('button', 'left')
        human_move = action.get('human_move', False)
        if isinstance(x1, str):
            x1 = int(self.variable_manager.evaluate(x1))
        if isinstance(y1, str):
            y1 = int(self.variable_manager.evaluate(y1))
        if isinstance(x2, str):
            x2 = int(self.variable_manager.evaluate(x2))
        if isinstance(y2, str):
            y2 = int(self.variable_manager.evaluate(y2))
        x1, y1 = self._resolve_xy(int(x1), int(y1), action)
        x2, y2 = self._resolve_xy(int(x2), int(y2), action)
        btn = Button.left if button == 'left' else (Button.right if button == 'right' else Button.middle)
        self.mouse_controller.position = (x1, y1)
        self.mouse_controller.press(btn)
        try:
            if human_move:
                steps = max(5, int(action.get('steps', 15)))
                step_delay = float(action.get('step_delay', 0.02))
                jitter = int(action.get('jitter', 2))
                for i in range(1, steps + 1):
                    if self.should_stop:
                        return
                    t = i / steps
                    px = int(x1 + (x2 - x1) * t + random.randint(-jitter, jitter))
                    py = int(y1 + (y2 - y1) * t + random.randint(-jitter, jitter))
                    self.mouse_controller.position = (px, py)
                    time.sleep(step_delay)
            else:
                self.mouse_controller.position = (x2, y2)
        finally:
            self.mouse_controller.release(btn)
        self.logger.log_macro_action('mouse_drag', f'({x1},{y1})->({x2},{y2})')
    
    def _action_wait_for_image_region(self, action: Dict):
        """Wie wait_for_image, aber nur in definiertem Rechteck (x,y,w,h) suchen."""
        template_name = action.get('template', '')
        region = action.get('region', (0, 0, 1920, 1080))
        if isinstance(region, (list, tuple)) and len(region) >= 4:
            region = tuple(int(v) for v in region[:4])
        else:
            region = None
        timeout = action.get('timeout', 10.0)
        confidence = action.get('confidence', 0.8)
        self.logger.log_macro_action('wait_for_image_region', f'{template_name} region={region}')
        match = self.image_recognition.wait_for_template(
            template_name, timeout=timeout, confidence=confidence, region=region
        )
        if match:
            self.variable_manager.set('image_x', match.center[0])
            self.variable_manager.set('image_y', match.center[1])
            self.variable_manager.set('image_found', True)
        else:
            self.variable_manager.set('image_found', False)
    
    def _action_random_click_region(self, action: Dict):
        """Klick auf Zufallsposition innerhalb des Rechtecks (x, y, width, height)."""
        x = int(action.get('x', 0))
        y = int(action.get('y', 0))
        w = int(action.get('width', 100))
        h = int(action.get('height', 100))
        button = action.get('button', 'left')
        if isinstance(x, str):
            x = int(self.variable_manager.evaluate(x))
        if isinstance(y, str):
            y = int(self.variable_manager.evaluate(y))
        if isinstance(w, str):
            w = int(self.variable_manager.evaluate(w))
        if isinstance(h, str):
            h = int(self.variable_manager.evaluate(h))
        x, y = self._resolve_xy(x, y, action)
        rx = x + random.randint(0, max(0, w - 1))
        ry = y + random.randint(0, max(0, h - 1))
        rx, ry = self._apply_click_offset(rx, ry)
        self.mouse_controller.position = (rx, ry)
        btn = Button.left if button == 'left' else (Button.right if button == 'right' else Button.middle)
        self.mouse_controller.click(btn)
        self.logger.log_macro_action('random_click_region', f'({rx},{ry}) in {w}x{h}')
    
    def _action_key_sequence(self, action: Dict):
        """Mehrere Tasten nacheinander mit optionalem Delay dazwischen (Kombo)."""
        keys = action.get('keys', [])
        delay_ms = float(action.get('delay_ms', 50))
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.split(',') if k.strip()]
        for i, key_name in enumerate(keys):
            if self.should_stop:
                return
            key = self._parse_key(key_name)
            if key:
                self.keyboard_controller.press(key)
                time.sleep(0.02)
                self.keyboard_controller.release(key)
            if i < len(keys) - 1 and delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        self.logger.log_macro_action('key_sequence', f'{len(keys)} keys')
    
    def _action_jump_to_action(self, action: Dict):
        """Sprung zu Aktion an Index (0-basiert). Für bedingte Schleifen/Skills."""
        target = action.get('action_index', 0)
        if isinstance(target, str):
            target = int(self.variable_manager.evaluate(target))
        target = max(0, min(target, 9999))
        self._jump_to_index = target
        self.logger.log_macro_action('jump_to_action', f'-> {target}')
    
    # Namens-Map für Tasten (z. B. aus importierten Makros)
    _KEY_ALIASES = {
        'space': Key.space, 'enter': Key.enter, 'return': Key.enter,
        'tab': Key.tab, 'escape': Key.esc, 'esc': Key.esc,
        'backspace': Key.backspace, 'delete': Key.delete,
        'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
        'home': Key.home, 'end': Key.end, 'pageup': Key.page_up, 'pagedown': Key.page_down,
        'shift': Key.shift, 'ctrl': Key.ctrl, 'control': Key.ctrl,
        'alt': Key.alt, 'caps_lock': Key.caps_lock,
    }
    
    def _parse_key(self, key_name: str):
        """Konvertiert Key-Namen zurück zu Key-Objekten"""
        if not key_name:
            return None
        
        key_str = str(key_name).strip().lower()
        if key_str in self._KEY_ALIASES:
            return self._KEY_ALIASES[key_str]
        
        # Spezielle Tasten (Key.xxx)
        if key_str.startswith('key.'):
            key_attr = key_str.replace('key.', '')
            try:
                return getattr(Key, key_attr)
            except AttributeError:
                return None
        
        # Normale Zeichen
        if len(key_str) == 1:
            return key_str
        
        return None

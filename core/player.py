"""
Makro-Player - Spielt aufgezeichnete Aktionen ab
Unterstützt: Bild-Erkennung, Variablen, Bedingungen, Schleifen
"""

from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
from typing import List, Dict, Callable, Optional, Any
import time
import threading

from core.image_recognition import ImageRecognition
from core.variables import VariableManager, ConditionEvaluator
from core.logging_system import get_logger

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
        self.variable_manager = VariableManager()
        self.condition_evaluator = ConditionEvaluator(self.variable_manager)
        self.logger = get_logger()
        
        # Ausführungs-Kontext
        self.current_loop = 0
        self.current_action = 0
    
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
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=2.0)
        self.is_playing = False
    
    def _play_worker(self, actions: List[Dict], loop_count: int, 
                     loop_infinite: bool, delay_between_loops: float,
                     speed_multiplier: float):
        """Worker-Thread für die Wiedergabe"""
        self.is_playing = True
        self.should_stop = False
        
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
                
                for i, action in enumerate(actions):
                    if self.should_stop:
                        break
                    
                    self.current_action = i
                    self.variable_manager.set('current_action', i + 1)
                    
                    # Verzögerung vor der Aktion
                    delay = action.get('delay', 0) / speed_multiplier
                    if delay > 0:
                        time.sleep(delay)
                    
                    # Aktion ausführen (mit Fehlerbehandlung)
                    try:
                        self._execute_action(action)
                    except Exception as e:
                        self.logger.log_exception(e, f"Action {i+1}")
                        # Weiter machen, außer bei kritischen Fehlern
                    
                    # Fortschritt melden
                    if self.on_progress_callback:
                        progress = ((self.current_loop * len(actions) + i + 1) / 
                                   (loop_count * len(actions)) * 100)
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
        
        # Bestehende Action-Typen
        elif action_type == 'mouse_move':
            x = action.get('x', 0)
            y = action.get('y', 0)
            # Variablen in Koordinaten unterstützen
            if isinstance(x, str):
                x = int(self.variable_manager.evaluate(x))
            if isinstance(y, str):
                y = int(self.variable_manager.evaluate(y))
            self.mouse_controller.position = (x, y)
            self.logger.log_macro_action('mouse_move', f'({x}, {y})')
        
        elif action_type == 'mouse_click':
            x = action.get('x', 0)
            y = action.get('y', 0)
            button_name = str(action.get('button', 'left')).lower()
            pressed = action.get('pressed', True)
            
            # Variablen in Koordinaten unterstützen
            if isinstance(x, str):
                x = int(self.variable_manager.evaluate(x))
            if isinstance(y, str):
                y = int(self.variable_manager.evaluate(y))
            
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
        """Klickt auf ein Bild"""
        template_name = action.get('template', '')
        confidence = action.get('confidence', 0.8)
        button = action.get('button', 'left')
        offset_x = action.get('offset_x', 0)
        offset_y = action.get('offset_y', 0)
        
        self.logger.log_macro_action('click_on_image', template_name)
        
        match = self.image_recognition.find_template(template_name, confidence)
        
        if match:
            # Auf Mittelpunkt klicken (mit optionalem Offset)
            x = match.center[0] + offset_x
            y = match.center[1] + offset_y
            
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
            except:
                pass  # Falls nicht auswertbar, original nutzen
        
        if level == 'debug':
            self.logger.debug(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def _parse_key(self, key_name: str):
        """Konvertiert Key-Namen zurück zu Key-Objekten"""
        if not key_name:
            return None
        
        # Spezielle Tasten
        if key_name.startswith('Key.'):
            key_attr = key_name.replace('Key.', '')
            try:
                return getattr(Key, key_attr)
            except AttributeError:
                return None
        
        # Normale Zeichen
        if len(key_name) == 1:
            return key_name
        
        return None

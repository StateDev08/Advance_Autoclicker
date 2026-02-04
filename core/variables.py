"""
Variablen-System für intelligente Makros
Unterstützt Variablen, Bedingungen und Schleifen
"""

from typing import Any, Dict, Optional, Callable
import re
import random


class VariableManager:
    """Verwaltet Variablen für Makro-Ausführung"""
    
    def __init__(self):
        """Initialisiert den Variable Manager"""
        self.variables: Dict[str, Any] = {}
        self.global_variables: Dict[str, Any] = {}
        
        # Built-in Funktionen
        self.functions: Dict[str, Callable] = {
            'random': self._func_random,
            'random_int': self._func_random_int,
            'random_float': self._func_random_float,
            'len': len,
            'str': str,
            'int': self._safe_int,
            'float': self._safe_float,
        }
    
    def reset(self):
        """Setzt alle lokalen Variablen zurück"""
        self.variables.clear()
    
    def set(self, name: str, value: Any):
        """Setzt eine Variable"""
        self.variables[name] = value
    
    def get(self, name: str, default: Any = None) -> Any:
        """Holt eine Variable (zuerst lokal, dann global)"""
        if name in self.variables:
            return self.variables[name]
        return self.global_variables.get(name, default)
    
    def set_global(self, name: str, value: Any):
        """Setzt eine globale Variable"""
        self.global_variables[name] = value
    
    def delete(self, name: str) -> bool:
        """Löscht eine Variable"""
        if name in self.variables:
            del self.variables[name]
            return True
        return False
    
    def exists(self, name: str) -> bool:
        """Prüft ob eine Variable existiert"""
        return name in self.variables or name in self.global_variables
    
    def evaluate(self, expression: str) -> Any:
        """
        Wertet einen Ausdruck aus (sicher, ohne eval)
        
        Unterstützt:
        - Variablen: {var_name}
        - Arithmetik: + - * / % **
        - Vergleiche: == != < > <= >=
        - Logik: and or not
        - Funktionen: random(), random_int(min, max), etc.
        
        Beispiele:
            "{counter} + 1"
            "{x} * {y}"
            "random_int(1, 100)"
            "{health} > 50 and {mana} > 20"
        """
        # Variablen ersetzen
        expr = self._replace_variables(expression)
        
        try:
            # Funktionsaufrufe verarbeiten
            expr = self._process_functions(expr)
            
            # Sicheres Auswerten (nur erlaubte Operationen)
            result = self._safe_eval(expr)
            return result
        except Exception as e:
            raise ValueError(f"Fehler beim Auswerten von '{expression}': {e}")
    
    def _replace_variables(self, text: str) -> str:
        """Ersetzt {var_name} durch Werte"""
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        
        def replacer(match):
            var_name = match.group(1)
            value = self.get(var_name)
            if value is None:
                raise ValueError(f"Variable '{var_name}' nicht gefunden")
            return str(value)
        
        return re.sub(pattern, replacer, text)
    
    def _process_functions(self, expr: str) -> str:
        """Verarbeitet Funktionsaufrufe"""
        # Pattern für Funktionsaufrufe: func_name(arg1, arg2, ...)
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)'
        
        def replacer(match):
            func_name = match.group(1)
            args_str = match.group(2)
            
            if func_name not in self.functions:
                raise ValueError(f"Unbekannte Funktion: {func_name}")
            
            # Argumente parsen
            args = []
            if args_str.strip():
                for arg in args_str.split(','):
                    arg = arg.strip()
                    # Versuche als Zahl zu parsen
                    try:
                        if '.' in arg:
                            args.append(float(arg))
                        else:
                            args.append(int(arg))
                    except ValueError:
                        # Als String behandeln
                        args.append(arg.strip('"\''))
            
            # Funktion aufrufen
            result = self.functions[func_name](*args)
            return str(result)
        
        # Wiederhole bis keine Funktionen mehr übrig
        max_iterations = 10
        for _ in range(max_iterations):
            new_expr = re.sub(pattern, replacer, expr)
            if new_expr == expr:
                break
            expr = new_expr
        
        return expr
    
    def _safe_eval(self, expr: str) -> Any:
        """
        Sicheres Auswerten von Ausdrücken
        Nur erlaubte Operationen, kein exec/eval
        """
        expr = expr.strip()
        
        # Boolean Werte
        if expr.lower() == 'true':
            return True
        if expr.lower() == 'false':
            return False
        
        # Zahlen
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # Strings (in Anführungszeichen)
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        
        # Vergleichsoperatoren
        for op in ['==', '!=', '<=', '>=', '<', '>']:
            if op in expr:
                left, right = expr.split(op, 1)
                left_val = self._safe_eval(left.strip())
                right_val = self._safe_eval(right.strip())
                
                if op == '==':
                    return left_val == right_val
                elif op == '!=':
                    return left_val != right_val
                elif op == '<':
                    return left_val < right_val
                elif op == '>':
                    return left_val > right_val
                elif op == '<=':
                    return left_val <= right_val
                elif op == '>=':
                    return left_val >= right_val
        
        # Logische Operatoren
        if ' and ' in expr:
            parts = expr.split(' and ')
            return all(self._safe_eval(p.strip()) for p in parts)
        
        if ' or ' in expr:
            parts = expr.split(' or ')
            return any(self._safe_eval(p.strip()) for p in parts)
        
        if expr.startswith('not '):
            return not self._safe_eval(expr[4:].strip())
        
        # Arithmetische Operatoren
        for op in ['+', '-', '*', '/', '%', '**']:
            if op in expr:
                # Richtigen Split finden (von rechts für +-)
                if op in ['+', '-']:
                    parts = expr.rsplit(op, 1)
                else:
                    parts = expr.split(op, 1)
                
                if len(parts) == 2:
                    left_val = self._safe_eval(parts[0].strip())
                    right_val = self._safe_eval(parts[1].strip())
                    
                    if op == '+':
                        return left_val + right_val
                    elif op == '-':
                        return left_val - right_val
                    elif op == '*':
                        return left_val * right_val
                    elif op == '/':
                        return left_val / right_val if right_val != 0 else 0
                    elif op == '%':
                        return left_val % right_val if right_val != 0 else 0
                    elif op == '**':
                        return left_val ** right_val
        
        # Wenn nichts passt, als String zurückgeben
        return expr
    
    # Built-in Funktionen
    def _func_random(self) -> float:
        """Zufallszahl zwischen 0.0 und 1.0"""
        return random.random()
    
    def _func_random_int(self, min_val: int, max_val: int) -> int:
        """Zufallszahl zwischen min und max (inklusive)"""
        return random.randint(int(min_val), int(max_val))
    
    def _func_random_float(self, min_val: float, max_val: float) -> float:
        """Zufalls-Fließkommazahl zwischen min und max"""
        return random.uniform(float(min_val), float(max_val))
    
    def _safe_int(self, value: Any) -> int:
        """Sichere Int-Konvertierung"""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value: Any) -> float:
        """Sichere Float-Konvertierung"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


class ConditionEvaluator:
    """Wertet Bedingungen für If/Else aus"""
    
    def __init__(self, variable_manager: VariableManager):
        self.var_manager = variable_manager
    
    def evaluate_condition(self, condition: str) -> bool:
        """
        Wertet eine Bedingung aus
        
        Args:
            condition: Bedingung als String (z.B. "{counter} > 10")
            
        Returns:
            True wenn Bedingung erfüllt, sonst False
        """
        try:
            result = self.var_manager.evaluate(condition)
            # Zu Boolean konvertieren
            if isinstance(result, bool):
                return result
            # Alles außer 0, None, "" ist True
            return bool(result)
        except Exception:
            return False

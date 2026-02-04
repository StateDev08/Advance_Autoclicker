"""
Professionelles Logging-System für Advanced Auto Clicker
Strukturiertes Logging mit Levels, Rotation und GUI-Integration
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class LogSignalHandler(logging.Handler, QObject):
    """Custom Handler der Log-Messages als Qt-Signale emittiert"""
    
    # Signal für neue Log-Nachrichten (level, message)
    log_message = pyqtSignal(str, str)
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
    
    def emit(self, record):
        """Emittiert Log-Record als Signal"""
        try:
            msg = self.format(record)
            level = record.levelname
            self.log_message.emit(level, msg)
        except Exception:
            self.handleError(record)


class LogManager:
    """Zentrales Logging-System"""
    
    # Singleton-Instanz
    _instance: Optional['LogManager'] = None
    
    def __init__(self, log_dir: str = "data/logs"):
        """
        Initialisiert das Logging-System
        
        Args:
            log_dir: Verzeichnis für Log-Dateien
        """
        if LogManager._instance is not None:
            raise RuntimeError("LogManager ist ein Singleton! Nutze get_instance()")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Signal-Handler für GUI
        self.signal_handler = LogSignalHandler()
        
        # Logger einrichten
        self._setup_loggers()
        
        LogManager._instance = self
    
    @staticmethod
    def get_instance() -> 'LogManager':
        """Gibt die Singleton-Instanz zurück"""
        if LogManager._instance is None:
            LogManager()
        return LogManager._instance
    
    def _setup_loggers(self):
        """Richtet alle Logger ein"""
        
        # Haupt-Logger
        self.main_logger = self._create_logger(
            name="main",
            filename="autoclicker.log",
            level=logging.INFO
        )
        
        # Makro-Logger (für Makro-Ausführung)
        self.macro_logger = self._create_logger(
            name="macro",
            filename="macro.log",
            level=logging.DEBUG
        )
        
        # Error-Logger (nur Fehler)
        self.error_logger = self._create_logger(
            name="error",
            filename="error.log",
            level=logging.ERROR
        )
        
        # Performance-Logger
        self.perf_logger = self._create_logger(
            name="performance",
            filename="performance.log",
            level=logging.INFO
        )
    
    def _create_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """
        Erstellt einen konfigurierten Logger
        
        Args:
            name: Logger-Name
            filename: Log-Dateiname
            level: Log-Level
            
        Returns:
            Konfigurierter Logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        
        # Bestehende Handler entfernen
        logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File Handler mit Rotation (max 10 MB, 5 Backups)
        file_handler = RotatingFileHandler(
            filename=self.log_dir / filename,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console Handler (nur für WARNING und höher)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Signal Handler für GUI (alle Levels)
        self.signal_handler.setLevel(logging.DEBUG)
        self.signal_handler.setFormatter(formatter)
        logger.addHandler(self.signal_handler)
        
        return logger
    
    # Convenience-Methoden für Haupt-Logger
    def info(self, message: str):
        """Info-Level Log"""
        self.main_logger.info(message)
    
    def debug(self, message: str):
        """Debug-Level Log"""
        self.main_logger.debug(message)
    
    def warning(self, message: str):
        """Warning-Level Log"""
        self.main_logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Error-Level Log"""
        self.main_logger.error(message, exc_info=exc_info)
        self.error_logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """Critical-Level Log"""
        self.main_logger.critical(message, exc_info=exc_info)
        self.error_logger.critical(message, exc_info=exc_info)
    
    # Spezielle Logger
    def log_macro_start(self, macro_name: str, loop_count: int):
        """Loggt Makro-Start"""
        self.macro_logger.info(f"Makro gestartet: '{macro_name}' (Loops: {loop_count})")
    
    def log_macro_action(self, action_type: str, details: str = ""):
        """Loggt Makro-Aktion"""
        msg = f"Aktion: {action_type}"
        if details:
            msg += f" | {details}"
        self.macro_logger.debug(msg)
    
    def log_macro_end(self, macro_name: str, success: bool, duration: float):
        """Loggt Makro-Ende"""
        status = "erfolgreich" if success else "abgebrochen"
        self.macro_logger.info(
            f"Makro beendet: '{macro_name}' ({status}) | Dauer: {duration:.2f}s"
        )
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """Loggt Performance-Metrik"""
        msg = f"{operation}: {duration:.3f}s"
        if details:
            msg += f" | {details}"
        self.perf_logger.info(msg)
    
    def log_exception(self, exc: Exception, context: str = ""):
        """Loggt Exception mit Kontext"""
        msg = f"Exception"
        if context:
            msg += f" in {context}"
        msg += f": {type(exc).__name__}: {exc}"
        self.error(msg, exc_info=True)
    
    def get_signal_handler(self) -> LogSignalHandler:
        """Gibt den Signal-Handler für GUI-Integration zurück"""
        return self.signal_handler
    
    def set_level(self, logger_name: str, level: int):
        """Setzt Log-Level für einen Logger"""
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    def clear_logs(self):
        """Löscht alle Log-Dateien"""
        for log_file in self.log_dir.glob("*.log*"):
            try:
                log_file.unlink()
            except Exception as e:
                self.error(f"Fehler beim Löschen von {log_file}: {e}")


# Globale Convenience-Funktionen
def get_logger() -> LogManager:
    """Gibt die LogManager-Instanz zurück"""
    return LogManager.get_instance()


def log_info(message: str):
    """Shortcut für Info-Log"""
    get_logger().info(message)


def log_debug(message: str):
    """Shortcut für Debug-Log"""
    get_logger().debug(message)


def log_warning(message: str):
    """Shortcut für Warning-Log"""
    get_logger().warning(message)


def log_error(message: str, exc_info: bool = False):
    """Shortcut für Error-Log"""
    get_logger().error(message, exc_info)


def log_exception(exc: Exception, context: str = ""):
    """Shortcut für Exception-Log"""
    get_logger().log_exception(exc, context)

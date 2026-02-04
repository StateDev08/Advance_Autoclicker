"""
Makro-Scheduler für zeitgesteuerte Ausführung
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time as time_module
from core.logging_system import get_logger


class ScheduleType(Enum):
    """Typen von Schedules"""
    ONCE = "once"              # Einmalig zu bestimmter Zeit
    DAILY = "daily"            # Täglich
    WEEKLY = "weekly"          # Wöchentlich
    INTERVAL = "interval"      # Alle X Minuten/Stunden
    COUNTDOWN = "countdown"    # Nach X Sekunden


@dataclass
class Schedule:
    """Geplante Makro-Ausführung"""
    id: int
    macro_id: int
    macro_name: str
    schedule_type: ScheduleType
    enabled: bool = True
    
    # Zeit-Parameter (abhängig von Type)
    time: Optional[time] = None              # Für ONCE, DAILY
    weekday: Optional[int] = None            # 0=Montag, 6=Sonntag (für WEEKLY)
    interval_minutes: Optional[int] = None   # Für INTERVAL
    countdown_seconds: Optional[int] = None  # Für COUNTDOWN
    
    # Metadata
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0


class MacroScheduler:
    """Scheduler für automatische Makro-Ausführung"""
    
    def __init__(self):
        self.schedules: List[Schedule] = []
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.logger = get_logger()
        
        # Callbacks
        self.on_macro_execute: Optional[Callable] = None
        
        self._next_schedule_id = 1
    
    def add_schedule(self, macro_id: int, macro_name: str,
                    schedule_type: ScheduleType, **kwargs) -> Schedule:
        """
        Fügt einen neuen Schedule hinzu
        
        Args:
            macro_id: ID des Makros
            macro_name: Name des Makros
            schedule_type: Typ des Schedules
            **kwargs: Zeit-Parameter je nach Type
                - time: datetime.time für ONCE, DAILY
                - weekday: int (0-6) für WEEKLY
                - interval_minutes: int für INTERVAL
                - countdown_seconds: int für COUNTDOWN
        
        Returns:
            Erstellter Schedule
        """
        schedule = Schedule(
            id=self._next_schedule_id,
            macro_id=macro_id,
            macro_name=macro_name,
            schedule_type=schedule_type,
            time=kwargs.get('time'),
            weekday=kwargs.get('weekday'),
            interval_minutes=kwargs.get('interval_minutes'),
            countdown_seconds=kwargs.get('countdown_seconds')
        )
        
        self._next_schedule_id += 1
        
        # Next run berechnen
        schedule.next_run = self._calculate_next_run(schedule)
        
        self.schedules.append(schedule)
        self.logger.info(f"Schedule erstellt: {macro_name} ({schedule_type.value})")
        
        return schedule
    
    def remove_schedule(self, schedule_id: int) -> bool:
        """Entfernt einen Schedule"""
        for i, schedule in enumerate(self.schedules):
            if schedule.id == schedule_id:
                del self.schedules[i]
                self.logger.info(f"Schedule gelöscht: {schedule.macro_name}")
                return True
        return False
    
    def toggle_schedule(self, schedule_id: int) -> bool:
        """Aktiviert/Deaktiviert einen Schedule"""
        for schedule in self.schedules:
            if schedule.id == schedule_id:
                schedule.enabled = not schedule.enabled
                self.logger.info(
                    f"Schedule {'aktiviert' if schedule.enabled else 'deaktiviert'}: "
                    f"{schedule.macro_name}"
                )
                return True
        return False
    
    def start(self):
        """Startet den Scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_worker,
            daemon=True
        )
        self.scheduler_thread.start()
        self.logger.info("Scheduler gestartet")
    
    def stop(self):
        """Stoppt den Scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
        self.logger.info("Scheduler gestoppt")
    
    def _scheduler_worker(self):
        """Worker-Thread für Scheduler"""
        while self.is_running:
            now = datetime.now()
            
            for schedule in self.schedules:
                if not schedule.enabled:
                    continue
                
                if schedule.next_run and now >= schedule.next_run:
                    # Makro ausführen
                    self._execute_scheduled_macro(schedule)
                    
                    # Nächsten Run berechnen
                    schedule.last_run = now
                    schedule.run_count += 1
                    schedule.next_run = self._calculate_next_run(schedule)
            
            # 1 Sekunde warten
            time_module.sleep(1)
    
    def _execute_scheduled_macro(self, schedule: Schedule):
        """Führt geplantes Makro aus"""
        self.logger.info(f"Führe geplantes Makro aus: {schedule.macro_name}")
        
        if self.on_macro_execute:
            try:
                self.on_macro_execute(schedule.macro_id, schedule.macro_name)
            except Exception as e:
                self.logger.log_exception(e, f"Scheduled Macro: {schedule.macro_name}")
    
    def _calculate_next_run(self, schedule: Schedule) -> Optional[datetime]:
        """Berechnet nächsten Ausführungszeitpunkt"""
        now = datetime.now()
        
        if schedule.schedule_type == ScheduleType.ONCE:
            # Einmalig - nur wenn noch nicht gelaufen
            if schedule.last_run is None and schedule.time:
                next_time = datetime.combine(now.date(), schedule.time)
                if next_time < now:
                    next_time += timedelta(days=1)
                return next_time
            return None
        
        elif schedule.schedule_type == ScheduleType.DAILY:
            # Täglich zur selben Zeit
            if schedule.time:
                next_time = datetime.combine(now.date(), schedule.time)
                if next_time <= now:
                    next_time += timedelta(days=1)
                return next_time
        
        elif schedule.schedule_type == ScheduleType.WEEKLY:
            # Wöchentlich am selben Tag zur selben Zeit
            if schedule.time and schedule.weekday is not None:
                days_ahead = schedule.weekday - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                next_date = now.date() + timedelta(days=days_ahead)
                next_time = datetime.combine(next_date, schedule.time)
                if next_time <= now:
                    next_time += timedelta(weeks=1)
                return next_time
        
        elif schedule.schedule_type == ScheduleType.INTERVAL:
            # Alle X Minuten
            if schedule.interval_minutes:
                if schedule.last_run:
                    return schedule.last_run + timedelta(minutes=schedule.interval_minutes)
                else:
                    return now + timedelta(minutes=schedule.interval_minutes)
        
        elif schedule.schedule_type == ScheduleType.COUNTDOWN:
            # Nach X Sekunden (einmalig)
            if schedule.countdown_seconds and schedule.last_run is None:
                return now + timedelta(seconds=schedule.countdown_seconds)
            return None
        
        return None
    
    def get_next_scheduled_macro(self) -> Optional[Schedule]:
        """Gibt das nächste geplante Makro zurück"""
        enabled_schedules = [s for s in self.schedules if s.enabled and s.next_run]
        
        if not enabled_schedules:
            return None
        
        return min(enabled_schedules, key=lambda s: s.next_run)
    
    def get_schedules_for_macro(self, macro_id: int) -> List[Schedule]:
        """Gibt alle Schedules für ein Makro zurück"""
        return [s for s in self.schedules if s.macro_id == macro_id]

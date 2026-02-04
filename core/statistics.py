"""
Statistiken & Analytics für Makros
Tracking von Ausführungen, Performance, Erfolgsrate
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class MacroExecutionStats:
    """Statistiken für eine Makro-Ausführung"""
    macro_id: int
    macro_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    success: bool = True
    actions_executed: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class MacroStatistics:
    """Aggregierte Statistiken für ein Makro"""
    macro_id: int
    macro_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    last_execution: Optional[datetime] = None
    total_actions_executed: int = 0


class StatisticsManager:
    """Verwaltet Statistiken für Makros"""
    
    def __init__(self, stats_file: str = "data/statistics.json"):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Laufende Executions
        self.current_executions: Dict[int, MacroExecutionStats] = {}
        
        # Statistiken pro Makro
        self.macro_stats: Dict[int, MacroStatistics] = {}
        
        # Execution-Historie (letzte 1000)
        self.execution_history: List[MacroExecutionStats] = []
        
        self.load_statistics()
    
    def start_execution(self, macro_id: int, macro_name: str) -> int:
        """
        Startet Tracking einer Makro-Ausführung
        
        Returns:
            Execution-ID
        """
        exec_id = id(datetime.now())
        
        stats = MacroExecutionStats(
            macro_id=macro_id,
            macro_name=macro_name,
            start_time=datetime.now()
        )
        
        self.current_executions[exec_id] = stats
        
        return exec_id
    
    def end_execution(self, exec_id: int, success: bool = True, 
                     actions_executed: int = 0, errors: List[str] = None):
        """Beendet Tracking einer Makro-Ausführung"""
        if exec_id not in self.current_executions:
            return
        
        stats = self.current_executions[exec_id]
        stats.end_time = datetime.now()
        stats.duration = (stats.end_time - stats.start_time).total_seconds()
        stats.success = success
        stats.actions_executed = actions_executed
        if errors:
            stats.errors = errors
        
        # Zu Historie hinzufügen
        self.execution_history.append(stats)
        
        # Limite auf 1000
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        # Aggregierte Stats aktualisieren
        self._update_macro_statistics(stats)
        
        # Aus laufenden entfernen
        del self.current_executions[exec_id]
        
        # Speichern
        self.save_statistics()
    
    def _update_macro_statistics(self, exec_stats: MacroExecutionStats):
        """Aktualisiert aggregierte Statistiken"""
        macro_id = exec_stats.macro_id
        
        if macro_id not in self.macro_stats:
            self.macro_stats[macro_id] = MacroStatistics(
                macro_id=macro_id,
                macro_name=exec_stats.macro_name
            )
        
        stats = self.macro_stats[macro_id]
        stats.total_executions += 1
        
        if exec_stats.success:
            stats.successful_executions += 1
        else:
            stats.failed_executions += 1
        
        stats.total_duration += exec_stats.duration
        stats.average_duration = stats.total_duration / stats.total_executions
        
        if stats.min_duration == 0 or exec_stats.duration < stats.min_duration:
            stats.min_duration = exec_stats.duration
        
        if exec_stats.duration > stats.max_duration:
            stats.max_duration = exec_stats.duration
        
        stats.last_execution = exec_stats.end_time
        stats.total_actions_executed += exec_stats.actions_executed
    
    def get_macro_statistics(self, macro_id: int) -> Optional[MacroStatistics]:
        """Gibt Statistiken für ein Makro zurück"""
        return self.macro_stats.get(macro_id)
    
    def get_all_statistics(self) -> List[MacroStatistics]:
        """Gibt Statistiken für alle Makros zurück"""
        return list(self.macro_stats.values())
    
    def get_recent_executions(self, limit: int = 10) -> List[MacroExecutionStats]:
        """Gibt letzte N Ausführungen zurück"""
        return self.execution_history[-limit:]
    
    def get_executions_for_macro(self, macro_id: int, 
                                 limit: int = 10) -> List[MacroExecutionStats]:
        """Gibt letzte N Ausführungen für ein Makro zurück"""
        macro_execs = [
            e for e in self.execution_history 
            if e.macro_id == macro_id
        ]
        return macro_execs[-limit:]
    
    def get_executions_today(self) -> List[MacroExecutionStats]:
        """Gibt Ausführungen von heute zurück"""
        today = datetime.now().date()
        return [
            e for e in self.execution_history
            if e.start_time.date() == today
        ]
    
    def get_success_rate(self, macro_id: Optional[int] = None) -> float:
        """
        Gibt Erfolgsrate zurück
        
        Args:
            macro_id: Spezifisches Makro oder None für alle
            
        Returns:
            Erfolgsrate (0.0 - 1.0)
        """
        if macro_id:
            stats = self.macro_stats.get(macro_id)
            if not stats or stats.total_executions == 0:
                return 0.0
            return stats.successful_executions / stats.total_executions
        else:
            total = sum(s.total_executions for s in self.macro_stats.values())
            successful = sum(s.successful_executions for s in self.macro_stats.values())
            return successful / total if total > 0 else 0.0
    
    def get_total_execution_time(self, macro_id: Optional[int] = None) -> float:
        """Gibt Gesamt-Ausführungszeit zurück (in Sekunden)"""
        if macro_id:
            stats = self.macro_stats.get(macro_id)
            return stats.total_duration if stats else 0.0
        else:
            return sum(s.total_duration for s in self.macro_stats.values())
    
    def reset_statistics(self, macro_id: Optional[int] = None):
        """
        Setzt Statistiken zurück
        
        Args:
            macro_id: Spezifisches Makro oder None für alle
        """
        if macro_id:
            if macro_id in self.macro_stats:
                del self.macro_stats[macro_id]
            self.execution_history = [
                e for e in self.execution_history
                if e.macro_id != macro_id
            ]
        else:
            self.macro_stats.clear()
            self.execution_history.clear()
        
        self.save_statistics()
    
    def save_statistics(self):
        """Speichert Statistiken in Datei"""
        try:
            data = {
                'macro_stats': {
                    str(macro_id): {
                        'macro_id': stats.macro_id,
                        'macro_name': stats.macro_name,
                        'total_executions': stats.total_executions,
                        'successful_executions': stats.successful_executions,
                        'failed_executions': stats.failed_executions,
                        'total_duration': stats.total_duration,
                        'average_duration': stats.average_duration,
                        'min_duration': stats.min_duration,
                        'max_duration': stats.max_duration,
                        'last_execution': stats.last_execution.isoformat() if stats.last_execution else None,
                        'total_actions_executed': stats.total_actions_executed
                    }
                    for macro_id, stats in self.macro_stats.items()
                },
                'execution_history': [
                    {
                        'macro_id': e.macro_id,
                        'macro_name': e.macro_name,
                        'start_time': e.start_time.isoformat(),
                        'end_time': e.end_time.isoformat() if e.end_time else None,
                        'duration': e.duration,
                        'success': e.success,
                        'actions_executed': e.actions_executed,
                        'errors': e.errors
                    }
                    for e in self.execution_history[-100:]  # Nur letzte 100 speichern
                ]
            }
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def load_statistics(self):
        """Lädt Statistiken aus Datei"""
        if not self.stats_file.exists():
            return
        
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Makro-Stats laden
            for macro_id_str, stats_data in data.get('macro_stats', {}).items():
                macro_id = int(macro_id_str)
                self.macro_stats[macro_id] = MacroStatistics(
                    macro_id=stats_data['macro_id'],
                    macro_name=stats_data['macro_name'],
                    total_executions=stats_data['total_executions'],
                    successful_executions=stats_data['successful_executions'],
                    failed_executions=stats_data['failed_executions'],
                    total_duration=stats_data['total_duration'],
                    average_duration=stats_data['average_duration'],
                    min_duration=stats_data['min_duration'],
                    max_duration=stats_data['max_duration'],
                    last_execution=datetime.fromisoformat(stats_data['last_execution']) if stats_data['last_execution'] else None,
                    total_actions_executed=stats_data['total_actions_executed']
                )
            
            # Execution-Historie laden
            for exec_data in data.get('execution_history', []):
                self.execution_history.append(MacroExecutionStats(
                    macro_id=exec_data['macro_id'],
                    macro_name=exec_data['macro_name'],
                    start_time=datetime.fromisoformat(exec_data['start_time']),
                    end_time=datetime.fromisoformat(exec_data['end_time']) if exec_data['end_time'] else None,
                    duration=exec_data['duration'],
                    success=exec_data['success'],
                    actions_executed=exec_data['actions_executed'],
                    errors=exec_data['errors']
                ))
        except Exception:
            pass

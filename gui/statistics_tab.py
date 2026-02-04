"""
Statistiken-Tab für Makro-Analytics
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QComboBox,
                             QGroupBox, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from core.statistics import StatisticsManager
from datetime import datetime


class StatisticsTab(QWidget):
    """Tab für Makro-Statistiken"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.stats_manager = StatisticsManager()
        self.setup_ui()
        
        # Auto-Refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_statistics)
        self.refresh_timer.start(5000)  # Alle 5 Sekunden
    
    def setup_ui(self):
        """Erstellt das UI"""
        layout = QVBoxLayout(self)
        
        # Gesamt-Statistiken
        overview_group = QGroupBox("Gesamt-Übersicht")
        overview_layout = QHBoxLayout()
        
        self.lbl_total_executions = QLabel("Ausführungen: 0")
        overview_layout.addWidget(self.lbl_total_executions)
        
        self.lbl_success_rate = QLabel("Erfolgsrate: 0%")
        overview_layout.addWidget(self.lbl_success_rate)
        
        self.lbl_total_time = QLabel("Gesamt-Zeit: 0s")
        overview_layout.addWidget(self.lbl_total_time)
        
        self.lbl_today = QLabel("Heute: 0")
        overview_layout.addWidget(self.lbl_today)
        
        overview_layout.addStretch()
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("Filter:"))
        
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Alle Makros", "Nach Ausführungen", "Nach Erfolgsrate"])
        self.cmb_filter.currentIndexChanged.connect(self.refresh_statistics)
        toolbar.addWidget(self.cmb_filter)
        
        toolbar.addStretch()
        
        btn_refresh = QPushButton("🔄 Aktualisieren")
        btn_refresh.clicked.connect(self.refresh_statistics)
        toolbar.addWidget(btn_refresh)
        
        btn_reset = QPushButton("🗑️ Zurücksetzen")
        btn_reset.clicked.connect(self.reset_statistics)
        toolbar.addWidget(btn_reset)
        
        btn_export = QPushButton("📊 Export CSV")
        btn_export.clicked.connect(self.export_statistics)
        toolbar.addWidget(btn_export)
        
        layout.addLayout(toolbar)
        
        # Tabelle - Makro-Statistiken
        self.table_macros = QTableWidget()
        self.table_macros.setColumnCount(8)
        self.table_macros.setHorizontalHeaderLabels([
            "Makro", "Ausführungen", "Erfolgreich", "Fehlgeschlagen",
            "Erfolgsrate", "Durchschnitt", "Min/Max", "Letzte Ausführung"
        ])
        self.table_macros.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("<b>Makro-Statistiken:</b>"))
        layout.addWidget(self.table_macros)
        
        # Tabelle - Letzte Ausführungen
        self.table_recent = QTableWidget()
        self.table_recent.setColumnCount(5)
        self.table_recent.setHorizontalHeaderLabels([
            "Zeit", "Makro", "Dauer", "Aktionen", "Status"
        ])
        self.table_recent.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_recent.setMaximumHeight(200)
        layout.addWidget(QLabel("<b>Letzte Ausführungen:</b>"))
        layout.addWidget(self.table_recent)
        
        # Info
        self.lbl_info = QLabel("Automatisches Tracking aller Makro-Ausführungen")
        self.lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_info)
        
        self.refresh_statistics()
    
    def refresh_statistics(self):
        """Aktualisiert alle Statistiken"""
        # Gesamt-Statistiken
        all_stats = self.stats_manager.get_all_statistics()
        
        total_executions = sum(s.total_executions for s in all_stats)
        success_rate = self.stats_manager.get_success_rate() * 100
        total_time = self.stats_manager.get_total_execution_time()
        today_count = len(self.stats_manager.get_executions_today())
        
        self.lbl_total_executions.setText(f"Ausführungen: {total_executions}")
        self.lbl_success_rate.setText(f"Erfolgsrate: {success_rate:.1f}%")
        self.lbl_total_time.setText(f"Gesamt-Zeit: {self._format_duration(total_time)}")
        self.lbl_today.setText(f"Heute: {today_count}")
        
        # Makro-Statistiken Tabelle
        # Sortieren nach Filter
        filter_index = self.cmb_filter.currentIndex()
        if filter_index == 1:  # Nach Ausführungen
            all_stats.sort(key=lambda s: s.total_executions, reverse=True)
        elif filter_index == 2:  # Nach Erfolgsrate
            all_stats.sort(key=lambda s: s.successful_executions / max(s.total_executions, 1), reverse=True)
        
        self.table_macros.setRowCount(len(all_stats))
        
        for i, stats in enumerate(all_stats):
            # Makro
            self.table_macros.setItem(i, 0, QTableWidgetItem(stats.macro_name))
            
            # Ausführungen
            self.table_macros.setItem(i, 1, QTableWidgetItem(str(stats.total_executions)))
            
            # Erfolgreich
            success_item = QTableWidgetItem(str(stats.successful_executions))
            success_item.setForeground(QColor(0, 200, 0))
            self.table_macros.setItem(i, 2, success_item)
            
            # Fehlgeschlagen
            failed_item = QTableWidgetItem(str(stats.failed_executions))
            if stats.failed_executions > 0:
                failed_item.setForeground(QColor(200, 0, 0))
            self.table_macros.setItem(i, 3, failed_item)
            
            # Erfolgsrate
            success_rate = (stats.successful_executions / max(stats.total_executions, 1)) * 100
            rate_item = QTableWidgetItem(f"{success_rate:.1f}%")
            if success_rate >= 95:
                rate_item.setForeground(QColor(0, 200, 0))
            elif success_rate < 80:
                rate_item.setForeground(QColor(200, 100, 0))
            self.table_macros.setItem(i, 4, rate_item)
            
            # Durchschnitt
            avg_text = self._format_duration(stats.average_duration)
            self.table_macros.setItem(i, 5, QTableWidgetItem(avg_text))
            
            # Min/Max
            min_max = f"{self._format_duration(stats.min_duration)} / {self._format_duration(stats.max_duration)}"
            self.table_macros.setItem(i, 6, QTableWidgetItem(min_max))
            
            # Letzte Ausführung
            if stats.last_execution:
                last_text = stats.last_execution.strftime("%d.%m. %H:%M")
            else:
                last_text = "-"
            self.table_macros.setItem(i, 7, QTableWidgetItem(last_text))
        
        # Letzte Ausführungen
        recent = self.stats_manager.get_recent_executions(20)
        self.table_recent.setRowCount(len(recent))
        
        for i, exec_stats in enumerate(reversed(recent)):
            # Zeit
            time_text = exec_stats.start_time.strftime("%H:%M:%S")
            self.table_recent.setItem(i, 0, QTableWidgetItem(time_text))
            
            # Makro
            self.table_recent.setItem(i, 1, QTableWidgetItem(exec_stats.macro_name))
            
            # Dauer
            duration_text = self._format_duration(exec_stats.duration)
            self.table_recent.setItem(i, 2, QTableWidgetItem(duration_text))
            
            # Aktionen
            self.table_recent.setItem(i, 3, QTableWidgetItem(str(exec_stats.actions_executed)))
            
            # Status
            status_text = "✅ Erfolg" if exec_stats.success else "❌ Fehler"
            status_item = QTableWidgetItem(status_text)
            if exec_stats.success:
                status_item.setForeground(QColor(0, 200, 0))
            else:
                status_item.setForeground(QColor(200, 0, 0))
            self.table_recent.setItem(i, 4, status_item)
    
    def reset_statistics(self):
        """Setzt Statistiken zurück"""
        reply = QMessageBox.question(
            self,
            "Statistiken zurücksetzen",
            "Möchten Sie wirklich ALLE Statistiken zurücksetzen?\nDieser Vorgang kann nicht rückgängig gemacht werden!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stats_manager.reset_statistics()
            self.refresh_statistics()
            self.lbl_info.setText("Alle Statistiken zurückgesetzt")
            QMessageBox.information(self, "Erfolg", "Statistiken wurden zurückgesetzt!")
    
    def export_statistics(self):
        """Exportiert Statistiken als CSV"""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Statistiken exportieren",
            f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    "Makro", "Gesamt-Ausführungen", "Erfolgreich", "Fehlgeschlagen",
                    "Erfolgsrate (%)", "Durchschnitt (s)", "Min (s)", "Max (s)",
                    "Gesamt-Zeit (s)", "Letzte Ausführung"
                ])
                
                # Daten
                for stats in self.stats_manager.get_all_statistics():
                    success_rate = (stats.successful_executions / max(stats.total_executions, 1)) * 100
                    last_exec = stats.last_execution.isoformat() if stats.last_execution else "-"
                    
                    writer.writerow([
                        stats.macro_name,
                        stats.total_executions,
                        stats.successful_executions,
                        stats.failed_executions,
                        f"{success_rate:.2f}",
                        f"{stats.average_duration:.3f}",
                        f"{stats.min_duration:.3f}",
                        f"{stats.max_duration:.3f}",
                        f"{stats.total_duration:.3f}",
                        last_exec
                    ])
            
            self.lbl_info.setText(f"Statistiken exportiert: {filename}")
            QMessageBox.information(self, "Erfolg", "Statistiken wurden exportiert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Exportieren: {e}")
    
    def _format_duration(self, seconds: float) -> str:
        """Formatiert Dauer für Anzeige"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

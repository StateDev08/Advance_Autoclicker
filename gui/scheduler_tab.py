"""
Scheduler-GUI Tab für zeitgesteuerte Makro-Ausführung
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
                             QComboBox, QTimeEdit, QSpinBox, QLabel, QMessageBox,
                             QHeaderView, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QTime
from datetime import datetime, time
from core.scheduler import MacroScheduler, ScheduleType, Schedule
from typing import Optional


class ScheduleDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten eines Schedules"""
    
    def __init__(self, macro_list: list, parent=None):
        super().__init__(parent)
        self.macro_list = macro_list
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt das UI"""
        self.setWindowTitle("Schedule erstellen")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Makro auswählen
        self.cmb_macro = QComboBox()
        for macro_id, macro_name in self.macro_list:
            self.cmb_macro.addItem(macro_name, macro_id)
        form.addRow("Makro:", self.cmb_macro)
        
        # Schedule-Typ
        self.cmb_type = QComboBox()
        self.cmb_type.addItems([
            "Einmalig",
            "Täglich",
            "Wöchentlich",
            "Intervall",
            "Countdown"
        ])
        self.cmb_type.currentIndexChanged.connect(self.on_type_changed)
        form.addRow("Typ:", self.cmb_type)
        
        layout.addLayout(form)
        
        # Parameter-Container
        self.param_group = QGroupBox("Parameter")
        self.param_layout = QFormLayout()
        self.param_group.setLayout(self.param_layout)
        layout.addWidget(self.param_group)
        
        # Parameter-Widgets
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        
        self.weekday_combo = QComboBox()
        self.weekday_combo.addItems([
            "Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag"
        ])
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(30)
        self.interval_spin.setSuffix(" Minuten")
        
        self.countdown_spin = QSpinBox()
        self.countdown_spin.setRange(1, 86400)
        self.countdown_spin.setValue(60)
        self.countdown_spin.setSuffix(" Sekunden")
        
        # Initiales Update
        self.on_type_changed(0)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_create = QPushButton("Erstellen")
        btn_create.clicked.connect(self.accept)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_create)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def on_type_changed(self, index: int):
        """Aktualisiert Parameter-Felder basierend auf Typ"""
        # Layout leeren
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        if index == 0:  # Einmalig
            self.param_layout.addRow("Uhrzeit:", self.time_edit)
        elif index == 1:  # Täglich
            self.param_layout.addRow("Uhrzeit:", self.time_edit)
        elif index == 2:  # Wöchentlich
            self.param_layout.addRow("Wochentag:", self.weekday_combo)
            self.param_layout.addRow("Uhrzeit:", self.time_edit)
        elif index == 3:  # Intervall
            self.param_layout.addRow("Alle:", self.interval_spin)
        elif index == 4:  # Countdown
            self.param_layout.addRow("Nach:", self.countdown_spin)
    
    def get_schedule_data(self) -> dict:
        """Gibt Schedule-Daten zurück"""
        macro_id = self.cmb_macro.currentData()
        macro_name = self.cmb_macro.currentText()
        
        type_index = self.cmb_type.currentIndex()
        type_map = [
            ScheduleType.ONCE,
            ScheduleType.DAILY,
            ScheduleType.WEEKLY,
            ScheduleType.INTERVAL,
            ScheduleType.COUNTDOWN
        ]
        schedule_type = type_map[type_index]
        
        kwargs = {}
        
        if type_index in [0, 1, 2]:  # Zeit-basiert
            qt_time = self.time_edit.time()
            kwargs['time'] = time(qt_time.hour(), qt_time.minute())
        
        if type_index == 2:  # Wöchentlich
            kwargs['weekday'] = self.weekday_combo.currentIndex()
        
        if type_index == 3:  # Intervall
            kwargs['interval_minutes'] = self.interval_spin.value()
        
        if type_index == 4:  # Countdown
            kwargs['countdown_seconds'] = self.countdown_spin.value()
        
        return {
            'macro_id': macro_id,
            'macro_name': macro_name,
            'schedule_type': schedule_type,
            'kwargs': kwargs
        }


class SchedulerTab(QWidget):
    """Tab für Makro-Scheduler"""
    
    execute_macro = pyqtSignal(int, str)  # macro_id, macro_name
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.scheduler = MacroScheduler()
        self.scheduler.on_macro_execute = self._on_scheduled_macro
        self.setup_ui()
        
        # Update-Timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_table)
        self.update_timer.start(1000)  # Jede Sekunde
    
    def setup_ui(self):
        """Erstellt das UI"""
        layout = QVBoxLayout(self)
        
        # Info
        info_group = QGroupBox("Scheduler-Status")
        info_layout = QHBoxLayout()
        
        self.lbl_status = QLabel("⏸️ Gestoppt")
        info_layout.addWidget(self.lbl_status)
        
        info_layout.addStretch()
        
        self.lbl_next = QLabel("Nächstes: -")
        info_layout.addWidget(self.lbl_next)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Starten")
        self.btn_start.clicked.connect(self.start_scheduler)
        toolbar.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏸️ Stoppen")
        self.btn_stop.clicked.connect(self.stop_scheduler)
        self.btn_stop.setEnabled(False)
        toolbar.addWidget(self.btn_stop)
        
        toolbar.addStretch()
        
        btn_add = QPushButton("➕ Schedule hinzufügen")
        btn_add.clicked.connect(self.add_schedule)
        toolbar.addWidget(btn_add)
        
        btn_toggle = QPushButton("⏯️ Aktivieren/Deaktivieren")
        btn_toggle.clicked.connect(self.toggle_schedule)
        toolbar.addWidget(btn_toggle)
        
        btn_delete = QPushButton("🗑️ Löschen")
        btn_delete.clicked.connect(self.delete_schedule)
        toolbar.addWidget(btn_delete)
        
        layout.addLayout(toolbar)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Makro", "Typ", "Parameter", "Nächster Run", "Status", "Ausführungen"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # Info
        self.lbl_info = QLabel("Scheduler automatisiert Makro-Ausführung zu bestimmten Zeiten")
        self.lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_info)
    
    def start_scheduler(self):
        """Startet den Scheduler"""
        self.scheduler.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("▶️ Läuft")
        self.lbl_info.setText("Scheduler läuft - Makros werden automatisch ausgeführt")
    
    def stop_scheduler(self):
        """Stoppt den Scheduler"""
        self.scheduler.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("⏸️ Gestoppt")
        self.lbl_info.setText("Scheduler gestoppt - Keine automatische Ausführung")
    
    def add_schedule(self):
        """Fügt einen neuen Schedule hinzu"""
        # Makro-Liste abrufen
        profile_id = 1  # TODO: Aktuelles Profil nutzen
        macros = self.db.get_macros(profile_id)
        
        if not macros:
            QMessageBox.information(self, "Keine Makros", "Bitte erst Makros erstellen!")
            return
        
        macro_list = [(m['id'], m['name']) for m in macros]
        
        dialog = ScheduleDialog(macro_list, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_schedule_data()
            
            self.scheduler.add_schedule(
                macro_id=data['macro_id'],
                macro_name=data['macro_name'],
                schedule_type=data['schedule_type'],
                **data['kwargs']
            )
            
            self.refresh_table()
            self.lbl_info.setText(f"Schedule erstellt für: {data['macro_name']}")
    
    def toggle_schedule(self):
        """Aktiviert/Deaktiviert ausgewählten Schedule"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        schedule_id = int(self.table.item(row, 0).text())
        self.scheduler.toggle_schedule(schedule_id)
        self.refresh_table()
    
    def delete_schedule(self):
        """Löscht ausgewählten Schedule"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        schedule_id = int(self.table.item(row, 0).text())
        
        reply = QMessageBox.question(
            self,
            "Schedule löschen",
            "Möchten Sie diesen Schedule wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.scheduler.remove_schedule(schedule_id)
            self.refresh_table()
            self.lbl_info.setText("Schedule gelöscht")
    
    def refresh_table(self):
        """Aktualisiert die Tabelle"""
        self.table.setRowCount(len(self.scheduler.schedules))
        
        now = datetime.now()
        
        for i, schedule in enumerate(self.scheduler.schedules):
            # ID
            self.table.setItem(i, 0, QTableWidgetItem(str(schedule.id)))
            
            # Makro
            self.table.setItem(i, 1, QTableWidgetItem(schedule.macro_name))
            
            # Typ
            type_names = {
                ScheduleType.ONCE: "Einmalig",
                ScheduleType.DAILY: "Täglich",
                ScheduleType.WEEKLY: "Wöchentlich",
                ScheduleType.INTERVAL: "Intervall",
                ScheduleType.COUNTDOWN: "Countdown"
            }
            self.table.setItem(i, 2, QTableWidgetItem(type_names[schedule.schedule_type]))
            
            # Parameter
            param_text = self._format_schedule_params(schedule)
            self.table.setItem(i, 3, QTableWidgetItem(param_text))
            
            # Nächster Run
            if schedule.next_run:
                time_until = schedule.next_run - now
                if time_until.total_seconds() > 0:
                    next_text = schedule.next_run.strftime("%d.%m. %H:%M")
                    seconds = int(time_until.total_seconds())
                    if seconds < 60:
                        next_text += f" ({seconds}s)"
                    elif seconds < 3600:
                        next_text += f" ({seconds // 60}m)"
                    else:
                        next_text += f" ({seconds // 3600}h)"
                else:
                    next_text = "Läuft..."
            else:
                next_text = "-"
            self.table.setItem(i, 4, QTableWidgetItem(next_text))
            
            # Status
            status = "✅ Aktiv" if schedule.enabled else "⏸️ Pausiert"
            self.table.setItem(i, 5, QTableWidgetItem(status))
            
            # Ausführungen
            self.table.setItem(i, 6, QTableWidgetItem(str(schedule.run_count)))
        
        # Nächstes Update
        next_schedule = self.scheduler.get_next_scheduled_macro()
        if next_schedule:
            time_until = next_schedule.next_run - now
            minutes = int(time_until.total_seconds() / 60)
            self.lbl_next.setText(f"Nächstes: {next_schedule.macro_name} in {minutes}m")
        else:
            self.lbl_next.setText("Nächstes: -")
    
    def _format_schedule_params(self, schedule: Schedule) -> str:
        """Formatiert Schedule-Parameter für Anzeige"""
        if schedule.schedule_type in [ScheduleType.ONCE, ScheduleType.DAILY]:
            return schedule.time.strftime("%H:%M") if schedule.time else "-"
        
        elif schedule.schedule_type == ScheduleType.WEEKLY:
            weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
            weekday = weekday_names[schedule.weekday] if schedule.weekday is not None else "?"
            time_str = schedule.time.strftime("%H:%M") if schedule.time else "?"
            return f"{weekday} {time_str}"
        
        elif schedule.schedule_type == ScheduleType.INTERVAL:
            return f"Alle {schedule.interval_minutes}m"
        
        elif schedule.schedule_type == ScheduleType.COUNTDOWN:
            return f"In {schedule.countdown_seconds}s"
        
        return "-"
    
    def _on_scheduled_macro(self, macro_id: int, macro_name: str):
        """Callback wenn Scheduler ein Makro ausführen will"""
        self.execute_macro.emit(macro_id, macro_name)

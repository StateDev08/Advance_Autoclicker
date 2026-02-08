"""
Profile-Verwaltungs Tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QListWidget, QListWidgetItem, QLabel, QLineEdit,
                              QTextEdit, QDialog, QDialogButtonBox, QMessageBox,
                              QInputDialog, QGroupBox, QFormLayout, QComboBox)
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path
import json
from database import DatabaseManager
from core import HotkeyManager


def _game_templates_path():
    return Path(__file__).resolve().parent.parent / "data" / "game_templates.json"


def _load_game_templates():
    p = _game_templates_path()
    if not p.exists():
        return []
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_game_templates(templates: list):
    p = _game_templates_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)

class ProfileTab(QWidget):
    """Tab für Profile-Verwaltung"""
    
    profile_selected = pyqtSignal(int)
    
    def __init__(self, db: DatabaseManager, hotkey_manager: HotkeyManager):
        super().__init__()
        self.db = db
        self.hotkey_manager = hotkey_manager
        self.current_profile_id = None
        
        self.init_ui()
        self.load_profiles()
    
    def init_ui(self):
        """Initialisiert die UI"""
        layout = QHBoxLayout(self)
        
        # Linke Seite - Profil-Liste
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("<b>Profile:</b>"))
        
        self.profile_list = QListWidget()
        self.profile_list.itemClicked.connect(self.on_profile_clicked)
        left_layout.addWidget(self.profile_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_new = QPushButton("➕ Neu")
        self.btn_new.clicked.connect(self.create_profile)
        button_layout.addWidget(self.btn_new)
        
        self.btn_edit = QPushButton("✏️ Bearbeiten")
        self.btn_edit.clicked.connect(self.edit_profile)
        self.btn_edit.setEnabled(False)
        button_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("🗑️ Löschen")
        self.btn_delete.clicked.connect(self.delete_profile)
        self.btn_delete.setEnabled(False)
        button_layout.addWidget(self.btn_delete)
        
        left_layout.addLayout(button_layout)
        
        # Rechte Seite - Profil-Details
        right_layout = QVBoxLayout()
        
        details_group = QGroupBox("Profil-Details")
        details_layout = QVBoxLayout()
        
        self.lbl_name = QLabel("<i>Kein Profil ausgewählt</i>")
        self.lbl_name.setWordWrap(True)
        details_layout.addWidget(self.lbl_name)
        
        self.lbl_description = QLabel("")
        self.lbl_description.setWordWrap(True)
        details_layout.addWidget(self.lbl_description)
        
        self.lbl_macros = QLabel("")
        details_layout.addWidget(self.lbl_macros)
        
        details_layout.addStretch()
        details_group.setLayout(details_layout)
        right_layout.addWidget(details_group)
        
        # Spiel-Vorlagen
        templates_group = QGroupBox("Spiel-Vorlagen")
        templates_layout = QVBoxLayout()
        self.template_list = QListWidget()
        self.template_list.setMaximumHeight(120)
        templates_layout.addWidget(self.template_list)
        template_btn_layout = QHBoxLayout()
        self.btn_template_create = QPushButton("Vorlage erstellen")
        self.btn_template_create.clicked.connect(self.create_game_template)
        template_btn_layout.addWidget(self.btn_template_create)
        self.btn_template_start = QPushButton("Starten")
        self.btn_template_start.clicked.connect(self.start_game_template)
        self.btn_template_start.setEnabled(False)
        template_btn_layout.addWidget(self.btn_template_start)
        self.btn_template_delete = QPushButton("Löschen")
        self.btn_template_delete.clicked.connect(self.delete_game_template)
        self.btn_template_delete.setEnabled(False)
        template_btn_layout.addWidget(self.btn_template_delete)
        templates_layout.addLayout(template_btn_layout)
        templates_group.setLayout(templates_layout)
        right_layout.addWidget(templates_group)
        self.template_list.itemSelectionChanged.connect(self.on_template_selection_changed)
        self.refresh_template_list()
        
        # Layouts zusammenfügen
        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 2)
    
    def load_profiles(self):
        """Lädt alle Profile"""
        self.profile_list.clear()
        profiles = self.db.get_profiles()
        
        for profile in profiles:
            item = QListWidgetItem(f"{profile['name']}")
            item.setData(Qt.ItemDataRole.UserRole, profile['id'])
            self.profile_list.addItem(item)
    
    def on_profile_clicked(self, item: QListWidgetItem):
        """Callback wenn ein Profil angeklickt wurde"""
        profile_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_profile_id = profile_id
        
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)
        
        # Details anzeigen
        profile = self.db.get_profile(profile_id)
        if profile:
            self.lbl_name.setText(f"<h2>{profile['name']}</h2>")
            self.lbl_description.setText(f"{profile['description'] or '<i>Keine Beschreibung</i>'}")
            
            # Makros zählen
            macros = self.db.get_macros(profile_id)
            self.lbl_macros.setText(f"<b>Makros:</b> {len(macros)}")
            
            self.profile_selected.emit(profile_id)
    
    def create_profile(self):
        """Erstellt ein neues Profil"""
        dialog = ProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, description = dialog.get_data()
            try:
                profile_id = self.db.create_profile(name, description)
                self.load_profiles()
                self.select_profile(profile_id)
                QMessageBox.information(self, "Erfolg", "Profil erstellt!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen: {str(e)}")
    
    def edit_profile(self):
        """Bearbeitet das ausgewählte Profil"""
        if not self.current_profile_id:
            return
        
        profile = self.db.get_profile(self.current_profile_id)
        if not profile:
            return
        
        dialog = ProfileDialog(self, profile['name'], profile['description'])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, description = dialog.get_data()
            try:
                self.db.update_profile(self.current_profile_id, name, description)
                self.load_profiles()
                self.select_profile(self.current_profile_id)
                QMessageBox.information(self, "Erfolg", "Profil aktualisiert!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren: {str(e)}")
    
    def delete_profile(self):
        """Löscht das ausgewählte Profil"""
        if not self.current_profile_id:
            return
        
        profile = self.db.get_profile(self.current_profile_id)
        if not profile:
            return
        
        reply = QMessageBox.question(
            self,
            "Profil löschen",
            f"Möchten Sie das Profil '{profile['name']}' wirklich löschen?\n"
            "Alle zugehörigen Makros werden ebenfalls gelöscht!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_profile(self.current_profile_id)
                self.current_profile_id = None
                self.load_profiles()
                self.lbl_name.setText("<i>Kein Profil ausgewählt</i>")
                self.lbl_description.setText("")
                self.lbl_macros.setText("")
                self.btn_edit.setEnabled(False)
                self.btn_delete.setEnabled(False)
                QMessageBox.information(self, "Erfolg", "Profil gelöscht!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen: {str(e)}")
    
    def select_profile(self, profile_id: int):
        """Wählt ein Profil aus"""
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == profile_id:
                self.profile_list.setCurrentItem(item)
                self.on_profile_clicked(item)
                break
    
    def get_selected_profile(self) -> int:
        """Gibt die ID des ausgewählten Profils zurück"""
        return self.current_profile_id

    def refresh_template_list(self):
        templates = _load_game_templates()
        self.template_list.clear()
        profiles = {p["id"]: p["name"] for p in self.db.get_profiles()}
        for t in templates:
            profile_name = profiles.get(t.get("profile_id"), "?")
            label = f"{t.get('name', '?')} ({profile_name})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, t)
            self.template_list.addItem(item)

    def on_template_selection_changed(self):
        has = self.template_list.currentItem() is not None
        self.btn_template_start.setEnabled(has)
        self.btn_template_delete.setEnabled(has)

    def create_game_template(self):
        profiles = self.db.get_profiles()
        if not profiles:
            QMessageBox.warning(self, "Hinweis", "Erstellen Sie zuerst ein Profil.")
            return
        name, ok = QInputDialog.getText(self, "Spiel-Vorlage", "Name der Vorlage (z. B. Spielname):")
        if not ok or not name.strip():
            return
        profile_names = [p["name"] for p in profiles]
        current_idx = 0
        if self.current_profile_id:
            for i, p in enumerate(profiles):
                if p["id"] == self.current_profile_id:
                    current_idx = i
                    break
        choice, ok = QInputDialog.getItem(self, "Spiel-Vorlage", "Profil:", profile_names, current_idx, False)
        if not ok:
            return
        profile_id = profiles[profile_names.index(choice)]["id"]
        window_filter, ok2 = QInputDialog.getText(self, "Spiel-Vorlage", "Fenster-Filter (optional, z. B. Spielname):", text="")
        if not ok2:
            return
        templates = _load_game_templates()
        templates.append({"name": name.strip(), "profile_id": profile_id, "window_filter": window_filter.strip()})
        _save_game_templates(templates)
        self.refresh_template_list()
        QMessageBox.information(self, "Erfolg", "Spiel-Vorlage erstellt.")

    def start_game_template(self):
        item = self.template_list.currentItem()
        if not item:
            return
        t = item.data(Qt.ItemDataRole.UserRole)
        profile_id = t.get("profile_id")
        window_filter = t.get("window_filter", "")
        self.select_profile(profile_id)
        if window_filter:
            QMessageBox.information(self, "Spiel-Vorlage gestartet", f"Profil geladen.\nFenster-Filter für Makros: {window_filter}")
        else:
            QMessageBox.information(self, "Spiel-Vorlage gestartet", "Profil geladen.")

    def delete_game_template(self):
        item = self.template_list.currentItem()
        if not item:
            return
        t = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Vorlage löschen",
            f"Vorlage '{t.get('name', '?')}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        templates = [x for x in _load_game_templates() if x.get("name") != t.get("name") or x.get("profile_id") != t.get("profile_id")]
        _save_game_templates(templates)
        self.refresh_template_list()


class ProfileDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten von Profilen"""
    
    def __init__(self, parent=None, name="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Profil" if not name else "Profil bearbeiten")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.txt_name = QLineEdit(name)
        layout.addWidget(self.txt_name)
        
        # Beschreibung
        layout.addWidget(QLabel("Beschreibung:"))
        self.txt_description = QTextEdit(description)
        self.txt_description.setMaximumHeight(100)
        layout.addWidget(self.txt_description)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        return self.txt_name.text(), self.txt_description.toPlainText()

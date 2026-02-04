"""
Template-Manager für Bild-Erkennung
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QLabel, QMessageBox, QInputDialog,
                             QDialog, QSpinBox, QFormLayout, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
from core.image_recognition import ImageRecognition
from PIL import ImageGrab
import numpy as np
import cv2


class RegionSelectorDialog(QDialog):
    """Dialog zum Auswählen eines Bildschirmbereichs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.region = None
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt das UI"""
        self.setWindowTitle("Bereich auswählen")
        
        layout = QVBoxLayout(self)
        
        info = QLabel("Geben Sie die Koordinaten des Bereichs ein:\n"
                     "(Tipp: Nutzen Sie ein Screenshot-Tool zum Ausmessen)")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        form = QFormLayout()
        
        self.spn_x = QSpinBox()
        self.spn_x.setRange(0, 9999)
        form.addRow("X:", self.spn_x)
        
        self.spn_y = QSpinBox()
        self.spn_y.setRange(0, 9999)
        form.addRow("Y:", self.spn_y)
        
        self.spn_width = QSpinBox()
        self.spn_width.setRange(1, 9999)
        self.spn_width.setValue(100)
        form.addRow("Breite:", self.spn_width)
        
        self.spn_height = QSpinBox()
        self.spn_height.setRange(1, 9999)
        self.spn_height.setValue(100)
        form.addRow("Höhe:", self.spn_height)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def get_region(self):
        """Gibt den ausgewählten Bereich zurück"""
        return (
            self.spn_x.value(),
            self.spn_y.value(),
            self.spn_width.value(),
            self.spn_height.value()
        )


class TemplateManagerWidget(QWidget):
    """Widget für Template-Verwaltung"""
    
    template_selected = pyqtSignal(str)  # Signal wenn Template ausgewählt
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_recognition = ImageRecognition()
        self.setup_ui()
        self.refresh_templates()
    
    def setup_ui(self):
        """Erstellt das UI"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_capture_full = QPushButton("📷 Vollbild erfassen")
        btn_capture_full.clicked.connect(self.capture_fullscreen)
        toolbar.addWidget(btn_capture_full)
        
        btn_capture_region = QPushButton("🖼️ Bereich erfassen")
        btn_capture_region.clicked.connect(self.capture_region)
        toolbar.addWidget(btn_capture_region)
        
        toolbar.addStretch()
        
        btn_test = QPushButton("🔍 Testen")
        btn_test.clicked.connect(self.test_template)
        toolbar.addWidget(btn_test)
        
        btn_delete = QPushButton("🗑️ Löschen")
        btn_delete.clicked.connect(self.delete_template)
        toolbar.addWidget(btn_delete)
        
        layout.addLayout(toolbar)
        
        # Template Liste
        self.list_templates = QListWidget()
        self.list_templates.itemClicked.connect(self.on_template_selected)
        self.list_templates.itemDoubleClicked.connect(self.test_template)
        layout.addWidget(self.list_templates)
        
        # Preview
        preview_group = QGroupBox("Vorschau")
        preview_layout = QVBoxLayout()
        
        self.lbl_preview = QLabel("Kein Template ausgewählt")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setMinimumHeight(200)
        self.lbl_preview.setStyleSheet("border: 1px solid gray;")
        preview_layout.addWidget(self.lbl_preview)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Info
        self.lbl_info = QLabel("Doppelklick zum Testen | Templates in data/templates/")
        self.lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_info)
    
    def refresh_templates(self):
        """Aktualisiert Template-Liste"""
        self.list_templates.clear()
        templates = self.image_recognition.list_templates()
        
        for template in templates:
            self.list_templates.addItem(f"🖼️ {template}")
        
        self.lbl_info.setText(f"{len(templates)} Templates verfügbar")
    
    def capture_fullscreen(self):
        """Erfasst Vollbild-Screenshot"""
        # Dialog minimieren
        self.window().showMinimized()
        
        # Kurz warten damit Fenster minimiert ist
        QTimer.singleShot(500, self._do_capture_fullscreen)
    
    def _do_capture_fullscreen(self):
        """Führt Vollbild-Erfassung aus"""
        name, ok = QInputDialog.getText(
            self,
            "Template Name",
            "Name für das Template:"
        )
        
        # Fenster wiederherstellen
        self.window().showNormal()
        
        if ok and name:
            try:
                path = self.image_recognition.save_template(name)
                self.refresh_templates()
                self.lbl_info.setText(f"Template gespeichert: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")
    
    def capture_region(self):
        """Erfasst Bereichs-Screenshot"""
        dialog = RegionSelectorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            region = dialog.get_region()
            
            # Dialog minimieren
            self.window().showMinimized()
            
            # Kurz warten
            QTimer.singleShot(500, lambda: self._do_capture_region(region))
    
    def _do_capture_region(self, region):
        """Führt Bereichs-Erfassung aus"""
        name, ok = QInputDialog.getText(
            self,
            "Template Name",
            "Name für das Template:"
        )
        
        # Fenster wiederherstellen
        self.window().showNormal()
        
        if ok and name:
            try:
                path = self.image_recognition.save_template(name, region)
                self.refresh_templates()
                self.lbl_info.setText(f"Template gespeichert: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")
    
    def delete_template(self):
        """Löscht ausgewähltes Template"""
        current_item = self.list_templates.currentItem()
        if not current_item:
            QMessageBox.information(self, "Hinweis", "Bitte Template auswählen")
            return
        
        template_name = current_item.text().replace("🖼️ ", "")
        
        reply = QMessageBox.question(
            self,
            "Template löschen",
            f"Möchten Sie '{template_name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.image_recognition.delete_template(template_name):
                self.refresh_templates()
                self.lbl_preview.clear()
                self.lbl_preview.setText("Kein Template ausgewählt")
                self.lbl_info.setText(f"Template gelöscht: {template_name}")
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Löschen")
    
    def test_template(self):
        """Testet ausgewähltes Template"""
        current_item = self.list_templates.currentItem()
        if not current_item:
            return
        
        template_name = current_item.text().replace("🖼️ ", "")
        
        self.lbl_info.setText(f"Suche nach '{template_name}'...")
        QTimer.singleShot(100, lambda: self._do_test_template(template_name))
    
    def _do_test_template(self, template_name: str):
        """Führt Template-Test aus"""
        try:
            match = self.image_recognition.find_template(template_name, confidence=0.7)
            
            if match:
                self.lbl_info.setText(
                    f"✅ Gefunden bei ({match.x}, {match.y}) | "
                    f"Konfidenz: {match.confidence:.2%}"
                )
                QMessageBox.information(
                    self,
                    "Template gefunden!",
                    f"Position: ({match.x}, {match.y})\n"
                    f"Größe: {match.width}x{match.height}\n"
                    f"Konfidenz: {match.confidence:.2%}"
                )
            else:
                self.lbl_info.setText("❌ Template nicht gefunden")
                QMessageBox.information(
                    self,
                    "Nicht gefunden",
                    f"Template '{template_name}' wurde nicht auf dem Bildschirm gefunden.\n"
                    f"(Mindest-Konfidenz: 70%)"
                )
        except Exception as e:
            self.lbl_info.setText(f"Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Testen: {e}")
    
    def on_template_selected(self, item):
        """Handler wenn Template ausgewählt wird"""
        template_name = item.text().replace("🖼️ ", "")
        
        # Template laden und anzeigen
        template = self.image_recognition.load_template(template_name)
        if template is not None:
            # OpenCV BGR zu RGB
            rgb_image = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            
            # Zu QImage konvertieren
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Als Pixmap anzeigen (skaliert)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.lbl_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_preview.setPixmap(scaled_pixmap)
            
            self.template_selected.emit(template_name)
        else:
            self.lbl_preview.setText("Fehler beim Laden")

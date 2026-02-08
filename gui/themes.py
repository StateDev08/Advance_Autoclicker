"""
Zentrale Theme- und Stylesheet-Verwaltung für Advanced Gaming.
Stellt mehrere Designs (Dark, Light, Gaming, Minimal, Classic) bereit.
"""

from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication


THEME_IDS = ("dark", "light", "gaming", "minimal", "classic")
DEFAULT_THEME = "dark"


def _make_stylesheet(
    bg: str,
    bg_alt: str,
    bg_widget: str,
    accent: str,
    text: str,
    text_dim: str,
    border: str,
    input_bg: str,
) -> str:
    """Baut ein globales Qt-Stylesheet aus Farbvariablen."""
    font_size = "9pt"
    if bg == "#1a1a2e": # Gaming theme usually needs more space/pop
        font_size = "10pt"

    return f"""
        QWidget {{
            background-color: {bg};
            color: {text};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: {font_size};
        }}
        QMainWindow, QDialog {{
            background-color: {bg};
        }}
        QTabWidget::pane {{
            border: 1px solid {border};
            background-color: {bg_alt};
            border-radius: 6px;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: {bg_alt};
            color: {text_dim};
            padding: 6px 12px;
            margin-right: 2px;
            border: 1px solid {border};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        QTabBar::tab:selected {{
            background-color: {bg};
            color: {accent};
            font-weight: bold;
            border-bottom: 2px solid {accent};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {bg_widget};
            color: {text};
        }}
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {border};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 5px;
            color: {accent};
        }}
        QPushButton {{
            background-color: {bg_widget};
            color: {text};
            border: 1px solid {border};
            border-radius: 5px;
            padding: 5px 10px;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {accent};
            color: {bg if accent != "#888888" else "#ffffff"};
            border-color: {accent};
        }}
        QPushButton:pressed {{
            background-color: {bg_alt};
        }}
        QPushButton:disabled {{
            background-color: {bg_alt};
            color: {text_dim};
            border: 1px solid {bg_alt};
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 4px;
            selection-background-color: {accent};
        }}
        QComboBox::drop-down {{
            border: none;
            background: transparent;
        }}
        QCheckBox, QRadioButton {{
            color: {text};
            spacing: 8px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {border};
            border-radius: 3px;
            background-color: {input_bg};
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {accent};
            border-color: {accent};
            image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
        }}
        QProgressBar {{
            border: 1px solid {border};
            border-radius: 6px;
            text-align: center;
            background-color: {bg_widget};
            height: 14px;
            font-size: 8pt;
        }}
        QProgressBar::chunk {{
            background-color: {accent};
            border-radius: 5px;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 0px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: none;
            min-height: 0px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            height: 0;
            width: 0;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 0px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: none;
            min-width: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
        QToolBar {{
            background-color: {bg_alt};
            border-bottom: 1px solid {border};
            spacing: 6px;
            padding: 4px;
        }}
        QStatusBar {{
            background-color: {bg_alt};
            color: {text_dim};
            border-top: 1px solid {border};
            font-size: 8pt;
        }}
        QMenuBar {{
            background-color: {bg};
            color: {text};
            border-bottom: 1px solid {border};
        }}
        QMenuBar::item:selected {{
            background-color: {accent};
            color: {bg};
        }}
        QMenu {{
            background-color: {bg_alt};
            color: {text};
            border: 1px solid {border};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 4px 20px 4px 10px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {accent};
            color: {bg};
        }}
        QHeaderView::section {{
            background-color: {bg_widget};
            color: {text};
            padding: 6px;
            border: none;
            border-right: 1px solid {border};
            border-bottom: 1px solid {border};
            font-weight: bold;
        }}
        QTableWidget, QListWidget {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            outline: none;
        }}
        QTableWidget::item, QListWidget::item {{
            padding: 4px;
            border-bottom: 1px solid {bg_alt};
        }}
        QTableWidget::item:selected, QListWidget::item:selected {{
            background-color: {accent};
            color: {bg};
            border-radius: 4px;
        }}
        QLabel {{
            background: transparent;
        }}
    """


# Theme-Definitionen: Farben für jedes Design
THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#2b2b2b",
        "bg_alt": "#1e1e1e",
        "bg_widget": "#3c3c3c",
        "accent": "#0d7377",
        "text": "#e0e0e0",
        "text_dim": "#a0a0a0",
        "border": "#404040",
        "input_bg": "#333333",
    },
    "light": {
        "bg": "#f5f5f5",
        "bg_alt": "#e8e8e8",
        "bg_widget": "#ffffff",
        "accent": "#0d7377",
        "text": "#212121",
        "text_dim": "#616161",
        "border": "#bdbdbd",
        "input_bg": "#ffffff",
    },
    "gaming": {
        "bg": "#1a1a2e",
        "bg_alt": "#16213e",
        "bg_widget": "#0f3460",
        "accent": "#00ff9d",
        "text": "#e0e0e0",
        "text_dim": "#88aacc",
        "border": "#2a4a6e",
        "input_bg": "#1a2a4a",
    },
    "minimal": {
        "bg": "#252525",
        "bg_alt": "#1a1a1a",
        "bg_widget": "#333333",
        "accent": "#888888",
        "text": "#cccccc",
        "text_dim": "#777777",
        "border": "#333333",
        "input_bg": "#2a2a2a",
    },
    "classic": {
        "bg": "#f0f0f0",
        "bg_alt": "#e0e0e0",
        "bg_widget": "#ffffff",
        "accent": "#0078d4",
        "text": "#000000",
        "text_dim": "#505050",
        "border": "#c0c0c0",
        "input_bg": "#ffffff",
    },
}


def get_stylesheet(theme_id: str) -> str:
    """Liefert das vollständige Stylesheet für das angegebene Theme."""
    if theme_id not in THEMES:
        theme_id = DEFAULT_THEME
    colors = THEMES[theme_id]
    return _make_stylesheet(
        bg=colors["bg"],
        bg_alt=colors["bg_alt"],
        bg_widget=colors["bg_widget"],
        accent=colors["accent"],
        text=colors["text"],
        text_dim=colors["text_dim"],
        border=colors["border"],
        input_bg=colors["input_bg"],
    )


def apply_theme(app: Optional[QApplication], theme_id: str) -> None:
    """Wendet das angegebene Theme auf die Anwendung an (globales Stylesheet)."""
    if theme_id not in THEMES:
        theme_id = DEFAULT_THEME
    sheet = get_stylesheet(theme_id)
    if app is not None:
        app.setStyle("Fusion")
        app.setStyleSheet(sheet)


def get_theme_display_name(theme_id: str) -> str:
    """Anzeigename des Themes für die Einstellungs-ComboBox."""
    names = {
        "dark": "Dark",
        "light": "Light",
        "gaming": "Gaming",
        "minimal": "Minimal",
        "classic": "Classic",
    }
    return names.get(theme_id, theme_id)

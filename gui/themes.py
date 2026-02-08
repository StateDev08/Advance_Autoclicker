"""
Zentrale Theme- und Stylesheet-Verwaltung für Advanced Gaming.
Stellt mehrere Designs (Dark, Light, Gaming, Minimal, Classic) bereit.
"""

from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication


THEME_IDS = ("dark", "light", "gaming", "minimal", "classic", "nord", "solarized", "midnight", "sakura")
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
    # Modernere Schriftarten bevorzugen
    font_family = "'Segoe UI', 'Inter', 'Roboto', sans-serif"

    return f"""
        QWidget {{
            background-color: {bg};
            color: {text};
            font-family: {font_family};
            font-size: {font_size};
            outline: none;
        }}
        QMainWindow, QDialog {{
            background-color: {bg};
        }}
        QTabWidget::pane {{
            border: 1px solid {border};
            background-color: {bg};
            border-radius: 8px;
            top: -1px;
            padding: 5px;
        }}
        QTabBar::tab {{
            background-color: {bg_alt};
            color: {text_dim};
            padding: 8px 16px;
            margin-right: 4px;
            border: 1px solid {border};
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            min-width: 80px;
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
            border-radius: 10px;
            margin-top: 15px;
            padding-top: 15px;
            background-color: {bg_alt};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 15px;
            padding: 0 8px;
            color: {accent};
        }}
        QPushButton {{
            background-color: {bg_widget};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 6px 12px;
            min-height: 24px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {accent};
            color: #ffffff;
            border-color: {accent};
        }}
        QPushButton:pressed {{
            background-color: {accent};
            opacity: 0.8;
        }}
        QPushButton:disabled {{
            background-color: {bg_alt};
            color: {text_dim};
            border: 1px solid {border};
        }}
        /* Spezielle Buttons */
        QPushButton#btn_play, QPushButton#btn_record {{
            background-color: #2ecc71;
            color: white;
            border: none;
            font-weight: bold;
        }}
        QPushButton#btn_stop {{
            background-color: #e74c3c;
            color: white;
            border: none;
            font-weight: bold;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 6px;
            selection-background-color: {accent};
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid {accent};
        }}
        QComboBox::drop-down {{
            border: none;
            background: transparent;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImdyYXkiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIyIj48cGF0aCBkPSJNNiA5bDYgNiA2LTYiLz48L3N2Zz4=);
            width: 12px;
            height: 12px;
        }}
        QCheckBox, QRadioButton {{
            color: {text};
            spacing: 8px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {border};
            border-radius: 4px;
            background-color: {input_bg};
        }}
        QCheckBox::indicator:checked {{
            background-color: {accent};
            border-color: {accent};
            image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
        }}
        QProgressBar {{
            border: 1px solid {border};
            border-radius: 8px;
            text-align: center;
            background-color: {bg_widget};
            height: 18px;
            font-size: 8pt;
            font-weight: bold;
        }}
        QProgressBar::chunk {{
            background-color: {accent};
            border-radius: 7px;
        }}
        QScrollBar:vertical {{
            background-color: {bg_alt};
            width: 12px;
            margin: 0;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {border};
            min-height: 20px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {accent};
        }}
        QScrollBar:horizontal {{
            background-color: {bg_alt};
            height: 12px;
            margin: 0;
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {border};
            min-width: 20px;
            border-radius: 6px;
            margin: 2px;
        }}
        QToolBar {{
            background-color: {bg};
            border-bottom: 1px solid {border};
            spacing: 10px;
            padding: 8px;
        }}
        QStatusBar {{
            background-color: {bg};
            color: {text_dim};
            border-top: 1px solid {border};
            font-size: 8pt;
            padding: 3px;
        }}
        QHeaderView::section {{
            background-color: {bg_alt};
            color: {text};
            padding: 8px;
            border: none;
            border-right: 1px solid {border};
            border-bottom: 1px solid {border};
            font-weight: bold;
        }}
        QTableWidget, QListWidget {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 8px;
            outline: none;
            gridline-color: {border};
        }}
        QTableWidget::item, QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {border};
        }}
        QTableWidget::item:selected, QListWidget::item:selected {{
            background-color: {accent};
            color: white;
        }}
        QListWidget::item:hover {{
            background-color: {bg_widget};
        }}
    """


# Theme-Definitionen: Farben für jedes Design (Modernisierte Palette)
THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#1e1e2e",      # Catppuccin Mocha Base
        "bg_alt": "#181825",  # Catppuccin Mocha Mantle
        "bg_widget": "#313244", # Catppuccin Mocha Surface0
        "accent": "#89b4fa",  # Catppuccin Mocha Blue
        "text": "#cdd6f4",    # Catppuccin Mocha Text
        "text_dim": "#a6adc8",# Catppuccin Mocha Subtext0
        "border": "#45475a",  # Catppuccin Mocha Surface1
        "input_bg": "#11111b",# Catppuccin Mocha Crust
    },
    "light": {
        "bg": "#eff1f5",      # Catppuccin Latte Base
        "bg_alt": "#e6e9ef",  # Catppuccin Latte Mantle
        "bg_widget": "#ccd0da", # Catppuccin Latte Surface0
        "accent": "#1e66f5",  # Catppuccin Latte Blue
        "text": "#4c4f69",    # Catppuccin Latte Text
        "text_dim": "#6c6f85",# Catppuccin Latte Subtext0
        "border": "#bcc0cc",  # Catppuccin Latte Surface1
        "input_bg": "#ffffff",
    },
    "gaming": {
        "bg": "#0f111a",      # Deep Cyberpunk
        "bg_alt": "#1a1c2e",
        "bg_widget": "#24283b",
        "accent": "#ff007c",  # Neon Pink
        "text": "#c0caf5",
        "text_dim": "#9aa5ce",
        "border": "#414868",
        "input_bg": "#16161e",
    },
    "minimal": {
        "bg": "#ffffff",
        "bg_alt": "#f5f5f5",
        "bg_widget": "#eeeeee",
        "accent": "#000000",
        "text": "#333333",
        "text_dim": "#666666",
        "border": "#dddddd",
        "input_bg": "#ffffff",
    },
    "classic": {
        "bg": "#f0f0f0",
        "bg_alt": "#e0e0e0",
        "bg_widget": "#d0d0d0",
        "accent": "#0056b3",
        "text": "#000000",
        "text_dim": "#404040",
        "border": "#a0a0a0",
        "input_bg": "#ffffff",
    },
    "nord": {
        "bg": "#2e3440",
        "bg_alt": "#242933",
        "bg_widget": "#3b4252",
        "accent": "#88c0d0",
        "text": "#eceff4",
        "text_dim": "#d8dee9",
        "border": "#4c566a",
        "input_bg": "#1d2128",
    },
    "solarized": {
        "bg": "#002b36",
        "bg_alt": "#073642",
        "bg_widget": "#586e75",
        "accent": "#268bd2",
        "text": "#839496",
        "text_dim": "#586e75",
        "border": "#073642",
        "input_bg": "#00212b",
    },
    "midnight": {
        "bg": "#000000",
        "bg_alt": "#0a0a0a",
        "bg_widget": "#1a1a1a",
        "accent": "#f1c40f",
        "text": "#ffffff",
        "text_dim": "#aaaaaa",
        "border": "#333333",
        "input_bg": "#000000",
    },
    "sakura": {
        "bg": "#fff5f7",
        "bg_alt": "#ffebee",
        "bg_widget": "#ffcdd2",
        "accent": "#e91e63",
        "text": "#5d4037",
        "text_dim": "#8d6e63",
        "border": "#f8bbd0",
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
        "nord": "Nord",
        "solarized": "Solarized Dark",
        "midnight": "Midnight Gold",
        "sakura": "Sakura Pink",
    }
    return names.get(theme_id, theme_id)

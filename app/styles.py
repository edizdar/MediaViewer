"""Dark theme styles for the Media Viewer application."""

# Color palette (Catppuccin Mocha inspired)
COLORS = {
    "base": "#1e1e2e",
    "mantle": "#181825",
    "crust": "#11111b",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay0": "#6c7086",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
    "blue": "#89b4fa",
    "green": "#a6e3a1",
    "red": "#f38ba8",
    "yellow": "#f9e2af",
    "peach": "#fab387",
    "lavender": "#b4befe",
}

DARK_THEME = f"""
/* ===== Global ===== */
QMainWindow {{
    background-color: {COLORS["base"]};
}}

QWidget {{
    background-color: {COLORS["base"]};
    color: {COLORS["text"]};
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}}

/* ===== Toolbar Containers ===== */
QWidget#topToolbar {{
    background-color: {COLORS["mantle"]};
    border-bottom: 1px solid {COLORS["surface0"]};
    padding: 4px 8px;
}}

QWidget#bottomToolbar {{
    background-color: {COLORS["mantle"]};
    border-top: 1px solid {COLORS["surface0"]};
    padding: 4px 8px;
}}

/* ===== Push Buttons ===== */
QPushButton {{
    background-color: {COLORS["surface0"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface1"]};
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 13px;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {COLORS["surface1"]};
    border-color: {COLORS["blue"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["surface2"]};
}}

QPushButton#accentButton {{
    background-color: {COLORS["blue"]};
    color: {COLORS["crust"]};
    border: none;
    font-weight: bold;
}}

QPushButton#accentButton:hover {{
    background-color: {COLORS["lavender"]};
}}

QPushButton#iconButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 16px;
    min-width: 32px;
    min-height: 32px;
}}

QPushButton#iconButton:hover {{
    background-color: {COLORS["surface0"]};
}}

QPushButton#iconButton:pressed {{
    background-color: {COLORS["surface1"]};
}}

/* ===== Fullscreen Overlay Buttons ===== */
QPushButton#fsExitBtn {{
    background-color: rgba(24, 24, 37, 0.88);
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface2"]};
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton#fsExitBtn:hover {{
    background-color: {COLORS["red"]};
    color: {COLORS["crust"]};
    border-color: {COLORS["red"]};
}}

QPushButton#fsNavBtn {{
    background-color: rgba(24, 24, 37, 0.75);
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface2"]};
    border-radius: 25px;
    font-size: 26px;
    font-weight: bold;
}}

QPushButton#fsNavBtn:hover {{
    background-color: {COLORS["blue"]};
    color: {COLORS["crust"]};
    border-color: {COLORS["blue"]};
}}

/* ===== Labels ===== */
QLabel {{
    color: {COLORS["text"]};
    background-color: transparent;
}}

QLabel#fileNameLabel {{
    color: {COLORS["text"]};
    font-size: 13px;
    font-weight: bold;
    padding: 0 12px;
}}

QLabel#infoLabel {{
    color: {COLORS["subtext"]};
    font-size: 12px;
    padding: 0 8px;
}}

QLabel#zoomLabel {{
    color: {COLORS["blue"]};
    font-size: 12px;
    font-weight: bold;
    min-width: 50px;
}}

QLabel#welcomeLabel {{
    color: {COLORS["overlay0"]};
    font-size: 18px;
}}

/* ===== Sliders ===== */
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {COLORS["surface1"]};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLORS["blue"]};
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS["lavender"]};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS["blue"]};
    border-radius: 2px;
}}

/* ===== Scroll Bars ===== */
QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
    width: 8px;
    height: 8px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {COLORS["surface1"]};
    border-radius: 4px;
    min-height: 20px;
    min-width: 20px;
}}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: {COLORS["surface2"]};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0px;
    width: 0px;
}}

QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}

/* ===== Graphics View (Image Viewer) ===== */
QGraphicsView {{
    background-color: {COLORS["crust"]};
    border: none;
}}

/* ===== Video Widget ===== */
QVideoWidget {{
    background-color: {COLORS["crust"]};
}}

/* ===== Separator ===== */
QFrame#separator {{
    background-color: {COLORS["surface0"]};
    max-width: 1px;
    max-height: 20px;
}}

/* ===== Tooltips ===== */
QToolTip {{
    background-color: {COLORS["surface0"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface1"]};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""

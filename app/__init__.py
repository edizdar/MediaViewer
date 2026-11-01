# Media Viewer — app package
from pathlib import Path
from PySide6.QtGui import QIcon

__version__ = "1.2.9"
APP_NAME = "Media Viewer"
APP_TITLE = f"Media Viewer v{__version__}"


def get_app_icon() -> QIcon:
    """Find and return the application QIcon."""
    # Check bundled PyInstaller _MEIPASS or source directory
    import sys
    base_dirs = []
    if hasattr(sys, "_MEIPASS"):
        base_dirs.append(Path(sys._MEIPASS))
    base_dirs.append(Path(__file__).resolve().parent.parent)

    for b in base_dirs:
        for fname in ("icon.ico", "icon.png"):
            p = b / "assets" / fname
            if p.is_file():
                return QIcon(str(p))
    return QIcon()

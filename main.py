"""Media Viewer — A photo and video viewer for Windows.

Usage:
    python main.py              # Launch with welcome screen
    python main.py <file>       # Open a specific file on launch
"""

import os
import sys
from pathlib import Path

# Use Qt Multimedia bundled FFmpeg backend with automatic hardware->software fallback.
# FFmpeg contains all universal codecs (H.264, HEVC/H.265, VP9, AV1, MPEG-4, etc.)
# directly embedded inside the application so that no missing codec errors ever occur.
os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
os.environ["QT_FFMPEG_DECODING_HW_DEVICE_TYPES"] = "d3d11va,dxva2,none"

# Windows Taskbar AppUserModelID: Ensures taskbar displays application logo instead of generic window icon
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("eroldizdar.mediaviewer.app.v1")
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app import APP_TITLE, get_app_icon
from app.main_window import MainWindow


def main() -> None:
    """Application entry point."""
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("MediaViewer")

    # Set application & taskbar icon
    app_icon = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Enable mouse tracking globally for fullscreen toolbar toggle
    app.setStyleSheet("")  # Ensure stylesheet system is initialized

    window = MainWindow()
    window.show()

    # Open file from command line argument
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if file_path.is_file():
            window.open_file(file_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

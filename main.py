"""Media Viewer — A photo and video viewer for Windows.

Usage:
    python main.py              # Launch with welcome screen
    python main.py <file>       # Open a specific file on launch
"""

import os
import sys
from pathlib import Path

# Configure Qt Multimedia FFmpeg hardware/software decoding fallback.
# Allows graceful fallback to CPU software decoding ('none') when D3D11VA/DXVA2 hardware
# decoding fails or when Windows HEVC/H.265 Media Foundation MFT is missing.
os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")
os.environ.setdefault("QT_FFMPEG_DECODING_HW_DEVICE_TYPES", "d3d11va,dxva2,none")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.main_window import MainWindow


def main() -> None:
    """Application entry point."""
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Media Viewer")
    app.setOrganizationName("MediaViewer")

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

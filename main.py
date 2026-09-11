"""Media Viewer — A photo and video viewer for Windows.

Usage:
    python main.py              # Launch with welcome screen
    python main.py <file>       # Open a specific file on launch
"""

import sys
from pathlib import Path

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

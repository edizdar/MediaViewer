"""Toolbar widgets for the Media Viewer application."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)

from app.localization import loc, get_localization


def _separator() -> QFrame:
    """Create a vertical separator line."""
    sep = QFrame()
    sep.setObjectName("separator")
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFixedWidth(1)
    sep.setFixedHeight(20)
    return sep


def _icon_button(text: str, tooltip: str = "") -> QPushButton:
    """Create a styled icon button."""
    btn = QPushButton(text)
    btn.setObjectName("iconButton")
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class TopToolbar(QWidget):
    """Top toolbar with file operations and navigation."""

    open_file_clicked = Signal()
    previous_clicked = Signal()
    next_clicked = Signal()
    fullscreen_clicked = Signal()
    playlist_toggled = Signal()
    help_clicked = Signal()
    language_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("topToolbar")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        # Open file button
        self._open_btn = QPushButton(loc("open_file_btn"))
        self._open_btn.setObjectName("accentButton")
        self._open_btn.setToolTip(loc("open_file_tip"))
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(self.open_file_clicked)
        layout.addWidget(self._open_btn)

        # Playlist toggle button
        self._playlist_btn = _icon_button("📋", loc("playlist_tip"))
        self._playlist_btn.clicked.connect(self.playlist_toggled)
        layout.addWidget(self._playlist_btn)

        layout.addWidget(_separator())

        # File name label
        self._file_label = QLabel("")
        self._file_label.setObjectName("fileNameLabel")
        self._file_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._file_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._file_label)

        # Navigation
        layout.addWidget(_separator())

        self._prev_btn = _icon_button("◀", loc("prev_tip"))
        self._prev_btn.clicked.connect(self.previous_clicked)
        layout.addWidget(self._prev_btn)

        self._counter_label = QLabel("")
        self._counter_label.setObjectName("infoLabel")
        self._counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counter_label.setMinimumWidth(60)
        layout.addWidget(self._counter_label)

        self._next_btn = _icon_button("▶", loc("next_tip"))
        self._next_btn.clicked.connect(self.next_clicked)
        layout.addWidget(self._next_btn)

        layout.addWidget(_separator())

        # Fullscreen button
        self._fullscreen_btn = _icon_button("⛶", loc("fullscreen_tip"))
        self._fullscreen_btn.setStyleSheet(
            "QPushButton { font-size: 20px; min-width: 36px; min-height: 36px; }"
        )
        self._fullscreen_btn.clicked.connect(self.fullscreen_clicked)
        layout.addWidget(self._fullscreen_btn)

        layout.addWidget(_separator())

        # Language toggle button
        curr_lang = get_localization().current_language.upper()
        self._lang_btn = _icon_button(f"🌐 {curr_lang}", loc("lang_tip"))
        self._lang_btn.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 13px; min-width: 48px; padding: 2px 6px; }"
        )
        self._lang_btn.clicked.connect(self.language_clicked)
        layout.addWidget(self._lang_btn)

        layout.addWidget(_separator())

        # Help / Guide button
        self._help_btn = _icon_button("❓", loc("help_tip"))
        self._help_btn.clicked.connect(self.help_clicked)
        layout.addWidget(self._help_btn)

    def retranslate_ui(self) -> None:
        """Update tooltips and labels when language changes."""
        lang = get_localization().current_language.upper()
        self._open_btn.setText(loc("open_file_btn"))
        self._open_btn.setToolTip(loc("open_file_tip"))
        self._playlist_btn.setToolTip(loc("playlist_tip"))
        self._prev_btn.setToolTip(loc("prev_tip"))
        self._next_btn.setToolTip(loc("next_tip"))
        self._fullscreen_btn.setToolTip(loc("fullscreen_tip"))
        self._lang_btn.setText(f"🌐 {lang}")
        self._lang_btn.setToolTip(loc("lang_tip"))
        self._help_btn.setToolTip(loc("help_tip"))

    def set_file_info(self, name: str, index: int, total: int) -> None:
        """Update the file name and navigation counter."""
        self._file_label.setText(name)
        if total > 0:
            self._counter_label.setText(f"{index + 1} / {total}")
        else:
            self._counter_label.setText("")

    def clear(self) -> None:
        """Clear file info display."""
        self._file_label.setText("")
        self._counter_label.setText("")


class BottomToolbar(QWidget):
    """Bottom toolbar with zoom, rotation controls, and file info."""

    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    fit_clicked = Signal()
    original_clicked = Signal()
    rotate_cw_clicked = Signal()
    rotate_ccw_clicked = Signal()
    crop_clicked = Signal()
    upscale_clicked = Signal()
    delete_clicked = Signal()
    adjustments_toggled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("bottomToolbar")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        # ── Image controls (left side) ──
        self._image_controls = QWidget()
        img_layout = QHBoxLayout(self._image_controls)
        img_layout.setContentsMargins(0, 0, 0, 0)
        img_layout.setSpacing(4)

        # Zoom controls
        self._zoom_out_btn = _icon_button("➖", loc("zoom_out_tip"))
        self._zoom_out_btn.clicked.connect(self.zoom_out_clicked)
        img_layout.addWidget(self._zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setObjectName("zoomLabel")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_layout.addWidget(self._zoom_label)

        self._zoom_in_btn = _icon_button("➕", loc("zoom_in_tip"))
        self._zoom_in_btn.clicked.connect(self.zoom_in_clicked)
        img_layout.addWidget(self._zoom_in_btn)

        img_layout.addWidget(_separator())

        # Fit / Original
        self._fit_btn = _icon_button("⊞", loc("fit_tip"))
        self._fit_btn.clicked.connect(self.fit_clicked)
        img_layout.addWidget(self._fit_btn)

        self._original_btn = _icon_button("1:1", loc("original_tip"))
        self._original_btn.clicked.connect(self.original_clicked)
        img_layout.addWidget(self._original_btn)

        img_layout.addWidget(_separator())

        # Rotate
        self._rotate_ccw_btn = _icon_button("↺", loc("rotate_ccw_tip"))
        self._rotate_ccw_btn.clicked.connect(self.rotate_ccw_clicked)
        img_layout.addWidget(self._rotate_ccw_btn)

        self._rotate_cw_btn = _icon_button("↻", loc("rotate_cw_tip"))
        self._rotate_cw_btn.clicked.connect(self.rotate_cw_clicked)
        img_layout.addWidget(self._rotate_cw_btn)

        img_layout.addWidget(_separator())

        # Crop button
        self._crop_btn = _icon_button("✂", loc("crop_tip"))
        self._crop_btn.clicked.connect(self.crop_clicked)
        img_layout.addWidget(self._crop_btn)

        # HD Upscale button
        self._upscale_btn = _icon_button("🖼️ HD", loc("upscale_tip"))
        self._upscale_btn.clicked.connect(self.upscale_clicked)
        img_layout.addWidget(self._upscale_btn)

        layout.addWidget(self._image_controls)

        # ── Spacer ──
        layout.addStretch()

        # ── File info (right side) ──
        self._info_label = QLabel("")
        self._info_label.setObjectName("infoLabel")
        self._info_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._info_label)

        layout.addWidget(_separator())

        # Delete button
        self._delete_btn = _icon_button("🗑", loc("delete_tip"))
        self._delete_btn.clicked.connect(self.delete_clicked)
        layout.addWidget(self._delete_btn)

        layout.addWidget(_separator())

        # Color adjustments toggle button
        self._adj_btn = _icon_button("🎨", loc("adj_tip"))
        self._adj_btn.clicked.connect(self.adjustments_toggled)
        layout.addWidget(self._adj_btn)

    def retranslate_ui(self) -> None:
        """Update tooltips when language changes."""
        self._zoom_out_btn.setToolTip(loc("zoom_out_tip"))
        self._zoom_in_btn.setToolTip(loc("zoom_in_tip"))
        self._fit_btn.setToolTip(loc("fit_tip"))
        self._original_btn.setToolTip(loc("original_tip"))
        self._rotate_ccw_btn.setToolTip(loc("rotate_ccw_tip"))
        self._rotate_cw_btn.setToolTip(loc("rotate_cw_tip"))
        self._crop_btn.setToolTip(loc("crop_tip"))
        self._upscale_btn.setToolTip(loc("upscale_tip"))
        self._delete_btn.setToolTip(loc("delete_tip"))
        self._adj_btn.setToolTip(loc("adj_tip"))

    def set_zoom_level(self, factor: float) -> None:
        """Update the zoom percentage display."""
        percent = int(factor * 100)
        self._zoom_label.setText(f"{percent}%")

    def set_file_info(self, info: str) -> None:
        """Set the file info text (dimensions, size, etc.)."""
        self._info_label.setText(info)

    def show_image_controls(self) -> None:
        """Show image-specific controls (zoom, rotate)."""
        self._image_controls.setVisible(True)

    def show_video_controls(self) -> None:
        """Hide image-specific controls when showing video."""
        self._image_controls.setVisible(False)

    def clear(self) -> None:
        """Reset toolbar to default state."""
        self._zoom_label.setText("100%")
        self._info_label.setText("")

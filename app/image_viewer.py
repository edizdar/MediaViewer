"""Image viewer widget with zoom, pan, and rotation support."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import (
    QPixmap, QWheelEvent, QMouseEvent, QTransform, QImage, QPainter,
)
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
)


class ImageViewer(QGraphicsView):
    """A graphics view widget for displaying and interacting with images.

    Supports:
    - Mouse wheel zoom with smooth scaling
    - Click-and-drag panning
    - Fit to window / original size
    - 90-degree rotation
    """

    zoom_changed = Signal(float)  # Emitted when zoom level changes (1.0 = 100%)
    double_clicked = Signal()  # Emitted on double-click (for fullscreen toggle)
    image_loaded = Signal(int, int)  # Emitted with (width, height) when image loads

    ZOOM_MIN = 0.05  # 5%
    ZOOM_MAX = 50.0  # 5000%
    ZOOM_STEP = 1.15  # 15% per wheel step

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._original_image: Optional[QImage] = None  # Kept for color adjustments
        self._zoom_factor: float = 1.0
        self._rotation: int = 0  # Degrees (0, 90, 180, 270)
        self._is_panning: bool = False
        self._pan_start = None
        self._fit_mode: bool = True  # Start in fit-to-window mode

        # View configuration
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setBackgroundBrush(Qt.GlobalColor.transparent)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def load_image(self, path: str | Path) -> bool:
        """Load and display an image from the given path. Returns True on success."""
        path = Path(path)

        # Load image
        image = QImage(str(path))
        if image.isNull():
            return False

        # Store original for color adjustments
        self._original_image = image.convertToFormat(QImage.Format.Format_ARGB32)
        pixmap = QPixmap.fromImage(image)

        # Clear previous content
        self._scene.clear()
        self._rotation = 0

        # Add pixmap to scene
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._pixmap_item.setTransformationMode(
            Qt.TransformationMode.SmoothTransformation
        )

        # Set scene rect to image size
        self._scene.setSceneRect(QRectF(pixmap.rect()))

        # Fit to window by default
        self._fit_mode = True
        self.fit_to_window()

        self.image_loaded.emit(pixmap.width(), pixmap.height())
        return True

    def clear(self) -> None:
        """Clear the current image."""
        self._scene.clear()
        self._pixmap_item = None
        self._original_image = None
        self._zoom_factor = 1.0
        self._rotation = 0

    def fit_to_window(self) -> None:
        """Scale the image to fit within the viewport while maintaining aspect ratio."""
        if self._pixmap_item is None:
            return

        self._fit_mode = True
        self.resetTransform()

        # Apply rotation
        if self._rotation != 0:
            self.rotate(self._rotation)

        # Calculate fit scale
        viewport_rect = self.viewport().rect()
        scene_rect = self._scene.sceneRect()

        if scene_rect.width() == 0 or scene_rect.height() == 0:
            return

        # Account for rotation when calculating dimensions
        if self._rotation in (90, 270):
            scale_x = viewport_rect.width() / scene_rect.height()
            scale_y = viewport_rect.height() / scene_rect.width()
        else:
            scale_x = viewport_rect.width() / scene_rect.width()
            scale_y = viewport_rect.height() / scene_rect.height()

        scale = min(scale_x, scale_y, 1.0)  # Don't upscale beyond 100%

        self.scale(scale, scale)
        self._zoom_factor = scale
        self.centerOn(self._pixmap_item)
        self.zoom_changed.emit(self._zoom_factor)

    def original_size(self) -> None:
        """Show the image at its original size (100%)."""
        if self._pixmap_item is None:
            return

        self._fit_mode = False
        self.resetTransform()

        if self._rotation != 0:
            self.rotate(self._rotation)

        self._zoom_factor = 1.0
        self.zoom_changed.emit(self._zoom_factor)
        self.centerOn(self._pixmap_item)

    def zoom_in(self) -> None:
        """Zoom in by one step."""
        self._apply_zoom(self.ZOOM_STEP)

    def zoom_out(self) -> None:
        """Zoom out by one step."""
        self._apply_zoom(1.0 / self.ZOOM_STEP)

    def zoom_to(self, factor: float) -> None:
        """Zoom to a specific factor (1.0 = 100%)."""
        if self._pixmap_item is None:
            return

        self._fit_mode = False
        ratio = factor / self._zoom_factor
        self.scale(ratio, ratio)
        self._zoom_factor = factor
        self.zoom_changed.emit(self._zoom_factor)

    def rotate_cw(self) -> None:
        """Rotate 90 degrees clockwise."""
        self._rotation = (self._rotation + 90) % 360
        self._apply_rotation()

    def rotate_ccw(self) -> None:
        """Rotate 90 degrees counter-clockwise."""
        self._rotation = (self._rotation - 90) % 360
        self._apply_rotation()

    def _apply_rotation(self) -> None:
        """Apply the current rotation and re-fit if in fit mode."""
        if self._fit_mode:
            self.fit_to_window()
        else:
            self.resetTransform()
            if self._rotation != 0:
                self.rotate(self._rotation)
            self.scale(self._zoom_factor, self._zoom_factor)
            self.zoom_changed.emit(self._zoom_factor)

    def _apply_zoom(self, factor: float) -> None:
        """Apply a relative zoom factor."""
        if self._pixmap_item is None:
            return

        self._fit_mode = False
        new_zoom = self._zoom_factor * factor

        # Clamp zoom level
        if new_zoom < self.ZOOM_MIN or new_zoom > self.ZOOM_MAX:
            return

        self.scale(factor, factor)
        self._zoom_factor = new_zoom

        # Keep centered when image fits within viewport or when zooming out
        rect = self.mapFromScene(self._scene.sceneRect()).boundingRect()
        if (
            rect.width() <= self.viewport().width()
            or rect.height() <= self.viewport().height()
            or factor < 1.0
        ):
            self.centerOn(self._pixmap_item)

        self.zoom_changed.emit(self._zoom_factor)

    # ── Event Handlers ──────────────────────────────────────────────────

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        if self._pixmap_item is None:
            return

        delta = event.angleDelta().y()
        if delta > 0:
            factor = self.ZOOM_STEP
        elif delta < 0:
            factor = 1.0 / self.ZOOM_STEP
        else:
            return

        self._apply_zoom(factor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start panning on middle or left button."""
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._is_panning = True
            self._pan_start = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle panning while dragging."""
        if self._is_panning and self._pan_start is not None:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on button release."""
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._is_panning = False
            self._pan_start = None
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Emit double_clicked signal for fullscreen toggle."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event) -> None:
        """Re-fit image when the widget is resized (if in fit mode)."""
        super().resizeEvent(event)
        if self._fit_mode and self._pixmap_item is not None:
            self.fit_to_window()

    @property
    def current_zoom(self) -> float:
        """Return the current zoom factor."""
        return self._zoom_factor

    def apply_adjustments(self, brightness: int, contrast: int, gamma: float) -> None:
        """Apply brightness/contrast/gamma adjustments using a LUT.

        Args:
            brightness: -100 to +100
            contrast:   -100 to +100
            gamma:      0.1 to 3.0  (1.0 = no change)
        """
        if self._original_image is None or self._pixmap_item is None:
            return

        # Fast path — no adjustments
        if brightness == 0 and contrast == 0 and abs(gamma - 1.0) < 0.01:
            pixmap = QPixmap.fromImage(self._original_image)
            self._pixmap_item.setPixmap(pixmap)
            return

        # ── Build 256-entry LUT ──
        contrast_factor = (100.0 + contrast) / 100.0
        inv_gamma = 1.0 / max(gamma, 0.01)

        lut = bytearray(256)
        for i in range(256):
            val = float(i)
            # Brightness shift
            val += brightness * 2.55
            # Contrast around midpoint
            val = (val - 128.0) * contrast_factor + 128.0
            # Gamma correction
            val = max(0.0, min(255.0, val))
            if inv_gamma != 1.0:
                val = 255.0 * pow(val / 255.0, inv_gamma)
            lut[i] = max(0, min(255, int(val + 0.5)))

        # ── Apply LUT to pixel data ──
        img = self._original_image  # Already ARGB32
        raw = img.bits().tobytes()
        data = bytearray(raw)

        # ARGB32 on little-endian = B G R A per pixel
        for i in range(0, len(data), 4):
            data[i] = lut[data[i]]          # B
            data[i + 1] = lut[data[i + 1]]  # G
            data[i + 2] = lut[data[i + 2]]  # R
            # data[i+3] = alpha — leave unchanged

        adjusted = QImage(
            bytes(data),
            img.width(),
            img.height(),
            img.bytesPerLine(),
            QImage.Format.Format_ARGB32,
        ).copy()  # .copy() ensures ownership of the data

        self._pixmap_item.setPixmap(QPixmap.fromImage(adjusted))


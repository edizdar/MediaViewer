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

from app.image_crop import CropOverlayItem, CropHUD


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
    crop_save_requested = Signal(QImage)  # Emitted when crop save is clicked
    crop_applied = Signal()  # Emitted when crop is applied to current view

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
        self._crop_item: Optional[CropOverlayItem] = None
        self._crop_hud: Optional[CropHUD] = None

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
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def load_image(self, path: str | Path) -> bool:
        """Load and display an image from the given path. Returns True on success."""
        self.cancel_crop()
        path = Path(path)

        # Load image
        image = QImage(str(path))
        if image.isNull():
            return False

        # Store original for color adjustments
        self._original_image = image.convertToFormat(QImage.Format.Format_ARGB32)
        pixmap = QPixmap.fromImage(self._original_image)

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
        self.cancel_crop()
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
        """Start panning on middle or left button (unless cropping)."""
        if self.is_cropping:
            if event.button() == Qt.MouseButton.MiddleButton:
                self._is_panning = True
                self._pan_start = event.position()
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
            super().mousePressEvent(event)
            return

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
        if self._is_panning and event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._is_panning = False
            self._pan_start = None
            if not self.is_cropping:
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Emit double_clicked signal for fullscreen toggle (disabled while cropping)."""
        if not self.is_cropping and event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event) -> None:
        """Re-fit image when the widget is resized (if in fit mode) and reposition HUD."""
        super().resizeEvent(event)
        if self._fit_mode and self._pixmap_item is not None and not self.is_cropping:
            self.fit_to_window()
        self._update_crop_hud_pos()

    # ── Crop API ────────────────────────────────────────────────────────

    @property
    def is_cropping(self) -> bool:
        """Return True if crop mode is currently active."""
        return self._crop_item is not None

    def start_crop(self) -> None:
        """Enter interactive crop mode."""
        if self._original_image is None or self._pixmap_item is None:
            return

        if self.is_cropping:
            return

        # If rotated, bake the rotation into original_image first so coordinates match 1:1
        if self._rotation != 0:
            t = QTransform()
            t.rotate(self._rotation)
            self._original_image = self._original_image.transformed(t)
            self._rotation = 0
            self._pixmap_item.setPixmap(QPixmap.fromImage(self._original_image))
            self._scene.setSceneRect(QRectF(self._original_image.rect()))
            self.fit_to_window()

        img_w = self._original_image.width()
        img_h = self._original_image.height()

        self._crop_item = CropOverlayItem(img_w, img_h)
        self._crop_item.rect_changed.connect(self._on_crop_rect_changed)
        self._scene.addItem(self._crop_item)

        # Create and display floating HUD
        self._crop_hud = CropHUD(self)
        self._crop_hud.apply_clicked.connect(self.apply_crop)
        self._crop_hud.save_clicked.connect(self.save_crop)
        self._crop_hud.cancel_clicked.connect(self.cancel_crop)
        self._crop_hud.ratio_changed.connect(self._crop_item.set_aspect_ratio)

        r = self._crop_item.crop_rect
        self._crop_hud.set_crop_dimensions(int(r.width()), int(r.height()))
        self._update_crop_hud_pos()
        self._crop_hud.show()
        self._crop_hud.raise_()

    def cancel_crop(self) -> None:
        """Exit crop mode without applying changes."""
        if self._crop_item is not None:
            if self._crop_item.scene() == self._scene:
                self._scene.removeItem(self._crop_item)
            self._crop_item = None

        if self._crop_hud is not None:
            self._crop_hud.hide()
            self._crop_hud.deleteLater()
            self._crop_hud = None

        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def apply_crop(self) -> None:
        """Apply current crop selection to displayed image in viewer."""
        if not self.is_cropping or self._original_image is None:
            return

        r = self._crop_item.crop_rect.toRect()
        r = r.intersected(self._original_image.rect())
        if r.width() >= 10 and r.height() >= 10:
            cropped = self._original_image.copy(r)
            self.cancel_crop()

            self._original_image = cropped
            self._pixmap_item.setPixmap(QPixmap.fromImage(self._original_image))
            self._scene.setSceneRect(QRectF(self._original_image.rect()))
            self.fit_to_window()
            self.image_loaded.emit(cropped.width(), cropped.height())
            self.crop_applied.emit()
        else:
            self.cancel_crop()

    def save_crop(self) -> None:
        """Request saving the current crop selection as a file."""
        if not self.is_cropping or self._original_image is None:
            return

        r = self._crop_item.crop_rect.toRect()
        r = r.intersected(self._original_image.rect())
        if r.width() >= 10 and r.height() >= 10:
            cropped = self._original_image.copy(r)
            self.crop_save_requested.emit(cropped)

    def _update_crop_hud_pos(self) -> None:
        if self._crop_hud is not None:
            self._crop_hud.adjustSize()
            hud_w = self._crop_hud.width()
            x = max(10, (self.viewport().width() - hud_w) // 2)
            self._crop_hud.move(x, 16)

    def _on_crop_rect_changed(self, rect: QRectF) -> None:
        if self._crop_hud is not None:
            self._crop_hud.set_crop_dimensions(int(rect.width()), int(rect.height()))

    @property
    def current_zoom(self) -> float:
        """Return the current zoom factor."""
        return self._zoom_factor

    def get_current_image(self) -> Optional[QImage]:
        """Return the current displayed QImage (including any applied color adjustments)."""
        if self._pixmap_item is not None:
            return self._pixmap_item.pixmap().toImage()
        return None

    def apply_adjustments(
        self, brightness: int, contrast: int, gamma: float, sharpness: int = 0
    ) -> None:
        """Apply brightness/contrast/gamma and unsharp mask sharpness adjustments.

        Args:
            brightness: -100 to +100
            contrast:   -100 to +100
            gamma:      0.1 to 3.0  (1.0 = no change)
            sharpness:  0 to 100%   (0 = no sharpening)
        """
        if self._original_image is None or self._pixmap_item is None:
            return

        # Fast path — no adjustments
        if (
            brightness == 0
            and contrast == 0
            and abs(gamma - 1.0) < 0.01
            and sharpness == 0
        ):
            self._pixmap_item.setPixmap(QPixmap.fromImage(self._original_image))
            self._pixmap_item.update()
            self.viewport().update()
            return

        # ── Build 256-entry LUT via NumPy ──
        import numpy as np

        contrast_factor = (100.0 + contrast) / 100.0
        inv_gamma = 1.0 / max(gamma, 0.01)

        indices = np.arange(256, dtype=np.float32)
        val = indices + (brightness * 2.55)
        val = (val - 128.0) * contrast_factor + 128.0
        np.clip(val, 0.0, 255.0, out=val)
        if abs(inv_gamma - 1.0) > 0.001:
            val = 255.0 * np.power(val / 255.0, inv_gamma)
        lut = np.clip(val + 0.5, 0, 255).astype(np.uint8)

        # ── Apply LUT to pixel data via NumPy vectorized indexing ──
        img = self._original_image  # ARGB32
        w, h = img.width(), img.height()
        bpl = img.bytesPerLine()

        raw = img.bits()
        arr = np.frombuffer(raw, dtype=np.uint8).reshape((h, bpl))
        pixel_bytes = arr[:, : w * 4].reshape((h, w, 4))

        out_pixels = pixel_bytes.copy()
        out_pixels[:, :, 0] = lut[pixel_bytes[:, :, 0]]  # B
        out_pixels[:, :, 1] = lut[pixel_bytes[:, :, 1]]  # G
        out_pixels[:, :, 2] = lut[pixel_bytes[:, :, 2]]  # R
        # out_pixels[:, :, 3] is Alpha — left untouched

        # ── Edge Sharpening (Unsharp Mask via Gaussian blur high-pass) ──
        if sharpness > 0:
            import cv2
            sigma = 1.0 + (sharpness / 100.0) * 1.5
            amount = (sharpness / 100.0) * 1.8
            bgr = out_pixels[:, :, :3]
            blurred = cv2.GaussianBlur(bgr, (0, 0), sigma)
            sharpened = cv2.addWeighted(bgr, 1.0 + amount, blurred, -amount, 0)
            out_pixels[:, :, :3] = np.clip(sharpened, 0, 255).astype(np.uint8)

        adjusted = QImage(
            out_pixels.data,
            w,
            h,
            w * 4,
            QImage.Format.Format_ARGB32,
        ).copy()

        self._pixmap_item.setPixmap(QPixmap.fromImage(adjusted))
        self._pixmap_item.update()
        self.viewport().update()


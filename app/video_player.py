"""Video player widget with zoom, keyboard pan, and playback controls."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QUrl, Slot, QSizeF, QPoint, QEvent, QTimer, QRectF
from PySide6.QtGui import QMouseEvent, QWheelEvent, QPainter, QColor, QDesktopServices, QImage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoFrame
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSizePolicy,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QMenu,
    QFileDialog,
    QMessageBox,
)

from app.video_trim import TrimSlider, VideoTrimPanel
from app.image_crop import CropOverlayItem


class VideoAdjustmentOverlay(QGraphicsItem):
    """Overlay item that renders real-time brightness, contrast, and gamma adjustments
    over the video in ZoomableVideoView, with smart quality enhancement support.
    """

    def __init__(self, target_item: QGraphicsVideoItem, parent=None) -> None:
        super().__init__(parent)
        self._target = target_item
        self.setZValue(50)  # Render on top of video item
        self._brightness: int = 0
        self._contrast: int = 0
        self._gamma: float = 1.0
        self._smart_enhance: bool = False
        self._adaptive_gamma_boost: float = 0.0
        self._adaptive_brightness_boost: int = 0

    def boundingRect(self) -> QRectF:
        return self._target.boundingRect()

    def set_adjustments(self, brightness: int, contrast: int, gamma: float) -> None:
        if (
            self._brightness == brightness
            and self._contrast == contrast
            and abs(self._gamma - gamma) < 0.005
        ):
            return
        self.prepareGeometryChange()
        self._brightness = brightness
        self._contrast = contrast
        self._gamma = gamma
        self.update()

    def set_smart_enhance(
        self, enabled: bool, adaptive_gamma: float = 0.0, adaptive_brightness: int = 0
    ) -> None:
        if (
            self._smart_enhance == enabled
            and abs(self._adaptive_gamma_boost - adaptive_gamma) < 0.01
            and self._adaptive_brightness_boost == adaptive_brightness
        ):
            return
        self.prepareGeometryChange()
        self._smart_enhance = enabled
        self._adaptive_gamma_boost = adaptive_gamma
        self._adaptive_brightness_boost = adaptive_brightness
        self.update()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        rect = self.boundingRect()
        if rect.isEmpty():
            return

        has_manual = (
            self._brightness != 0
            or self._contrast != 0
            or abs(self._gamma - 1.0) >= 0.01
        )

        if not self._smart_enhance and not has_manual:
            return

        painter.save()

        # ── 1. Smart Quality Enhancement (Vivid, Punchy & Clear) ──
        if self._smart_enhance:
            # 1a. Dehaze & Deep Contrast (ColorBurn)
            # Clears milky fog and deepens washed-out blacks without crushing detail
            burn_val = 242
            if self._adaptive_brightness_boost < 0:  # Bright scene
                burn_val = 238
            elif self._adaptive_brightness_boost > 0:  # Dark scene
                burn_val = 246
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_ColorBurn)
            painter.fillRect(rect, QColor(burn_val, burn_val, burn_val))

            # 1b. Dynamic Midtone Clarity & Shadow Lift (SoftLight)
            # Lifts shadow details so dark areas become clearly visible
            soft_alpha = 110 + int(self._adaptive_gamma_boost * 150)
            soft_alpha = max(60, min(170, soft_alpha))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SoftLight)
            painter.fillRect(rect, QColor(255, 255, 255, soft_alpha))

            # 1c. Vivid Vibrancy & Saturation Pop (Overlay with warm radiant tint)
            # Turns flat, muted video colors into vibrant, healthy, and vivid colors
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
            painter.fillRect(rect, QColor(255, 185, 95, 52))

            # 1d. Specular Highlight Brilliance (ColorDodge)
            # Brings out crisp sheen and reflections
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_ColorDodge)
            painter.fillRect(rect, QColor(22, 22, 22))

        # ── 2. Manual Adjustments (from Ctrl+J panel or sliders) ──
        if has_manual:
            # Brightness (Exposure Gain / Attenuation)
            if self._brightness > 0:
                val = int((self._brightness / 100.0) * 125)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_ColorDodge)
                painter.fillRect(rect, QColor(val, val, val))
            elif self._brightness < 0:
                factor = 1.0 - (-self._brightness / 100.0) * 0.85
                val = max(10, min(255, int(255 * factor)))
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
                painter.fillRect(rect, QColor(val, val, val))

            # Contrast (True S-Curve via ColorBurn & ColorDodge)
            if self._contrast > 0:
                burn = 255 - int((self._contrast / 100.0) * 60)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_ColorBurn)
                painter.fillRect(rect, QColor(burn, burn, burn))
                dodge = int((self._contrast / 100.0) * 55)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_ColorDodge)
                painter.fillRect(rect, QColor(dodge, dodge, dodge))
            elif self._contrast < 0:
                alpha = int((-self._contrast / 100.0) * 160)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.fillRect(rect, QColor(128, 128, 128, alpha))

            # Gamma (Midtone Curve)
            if self._gamma > 1.01:
                alpha = int(min((self._gamma - 1.0) / 1.5, 1.0) * 200)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SoftLight)
                painter.fillRect(rect, QColor(255, 255, 255, alpha))
            elif self._gamma < 0.99:
                alpha = int(min((1.0 - self._gamma) / 0.9, 1.0) * 200)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SoftLight)
                painter.fillRect(rect, QColor(0, 0, 0, alpha))

        painter.restore()


class CodecWarningBanner(QFrame):
    """Floating banner displayed when video frames cannot be decoded (e.g. missing HEVC/H.265 codec)."""

    transcode_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("codecWarningBanner")
        self.hide()

        self.setStyleSheet(
            """
            QFrame#codecWarningBanner {
                background-color: rgba(24, 24, 37, 0.95);
                border: 1.5px solid #f59e0b;
                border-radius: 8px;
            }
            QLabel#bannerTitle {
                color: #fbbf24;
                font-weight: bold;
                font-size: 13px;
            }
            QLabel#bannerText {
                color: #cdd6f4;
                font-size: 11px;
                line-height: 1.4;
            }
            QPushButton#codecBtn {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton#codecBtn:hover {
                background-color: #45475a;
                color: #ffffff;
                border-color: #f59e0b;
            }
            QPushButton#transcodeBtn {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton#transcodeBtn:hover {
                background-color: #106ebe;
            }
            QPushButton#closeBannerBtn {
                background: transparent;
                color: #6c7086;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 2px 6px;
            }
            QPushButton#closeBannerBtn:hover {
                color: #f38ba8;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(8)

        # Header: Icon + Title + Close button
        header = QHBoxLayout()
        header.setSpacing(8)

        self._title_label = QLabel("⚡ Görüntü Çözülemedi — Dahili Çözücü Hazır")
        self._title_label.setObjectName("bannerTitle")
        header.addWidget(self._title_label)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBannerBtn")
        close_btn.setToolTip("Bildirimi Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Body: Explanation
        self._body_label = QLabel(
            "Videonun sesi çalıyor ancak ekran kartınız bu video profilini doğrudan çizemedi.\n"
            "Harici hiçbir program yüklemeden, dahili FFmpeg motorumuzla videoyu anında uyumlu MP4 yapabilirsiniz."
        )
        self._body_label.setObjectName("bannerText")
        self._body_label.setWordWrap(True)
        layout.addWidget(self._body_label)

        # Actions row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        transcode_btn = QPushButton("⚡ Dahili FFmpeg ile Uyumlu Yap ve Oynat")
        transcode_btn.setObjectName("transcodeBtn")
        transcode_btn.setToolTip("Dahili FFmpeg motorumuzla videoyu standart H.264 formatına çevirip açar")
        transcode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        transcode_btn.clicked.connect(self.transcode_requested)
        btn_layout.addWidget(transcode_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def show_banner(self, custom_msg: Optional[str] = None) -> None:
        if custom_msg:
            self._body_label.setText(custom_msg)
        else:
            self._body_label.setText(
                "Videonun sesi çalıyor ancak ekran kartınız bu video profilini doğrudan çizemedi.\n"
                "Harici hiçbir program yüklemeden, dahili FFmpeg motorumuzla videoyu anında uyumlu MP4 yapabilirsiniz."
            )
        self.show()
        self.raise_()


class VideoOSDToast(QLabel):
    """Temporary on-screen display toast (e.g. '✨ Akıllı İyileştirme: AÇIK')."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("videoOSDToast")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, is_active: bool = True) -> None:
        self.setText(text)
        color = "#89b4fa" if is_active else "#a6adc8"
        border_col = "#89b4fa" if is_active else "#45475a"
        self.setStyleSheet(
            f"""
            QLabel#videoOSDToast {{
                background-color: rgba(24, 24, 37, 0.92);
                color: {color};
                font-size: 13px;
                font-weight: bold;
                border: 1.5px solid {border_col};
                border-radius: 16px;
                padding: 6px 18px;
            }}
            """
        )
        self.adjustSize()
        if self.parent():
            p = self.parent()
            x = (p.width() - self.width()) // 2
            y = 26
            self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start()


class ZoomableVideoView(QGraphicsView):
    """A QGraphicsView that displays video via QGraphicsVideoItem with
    mouse-wheel zoom and drag-to-pan support.
    """

    double_clicked = Signal()
    zoom_changed = Signal(float)
    crop_rect_changed = Signal(QRectF)
    transcode_requested = Signal()
    native_size_ready = Signal(QSizeF)

    ZOOM_MIN = 0.5
    ZOOM_MAX = 10.0
    ZOOM_STEP = 1.15

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._video_item = QGraphicsVideoItem()
        self._scene.addItem(self._video_item)

        self._overlay = VideoAdjustmentOverlay(self._video_item)
        self._scene.addItem(self._overlay)

        self._crop_item: Optional[CropOverlayItem] = None
        self._zoom: float = 1.0
        self._is_panning: bool = False
        self._pan_start = None

        # View configuration
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(Qt.GlobalColor.black)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

        # Fit video when its native size becomes known or when first frame arrives
        self._video_item.nativeSizeChanged.connect(self._on_native_size_changed)
        self._video_item.videoSink().videoFrameChanged.connect(self._on_video_frame_changed)

        # Floating codec / black-screen notification banner
        self._codec_banner = CodecWarningBanner(self.viewport())
        self._codec_banner.transcode_requested.connect(self.transcode_requested)

        # OSD Toast for mode toggles
        self._osd_toast = VideoOSDToast(self.viewport())

    @property
    def video_item(self) -> QGraphicsVideoItem:
        return self._video_item

    @property
    def is_zoomed(self) -> bool:
        return self._zoom > 1.01

    @property
    def current_zoom(self) -> float:
        return self._zoom

    def apply_adjustments(self, brightness: int, contrast: int, gamma: float) -> None:
        """Apply real-time color adjustments to the video overlay."""
        self._overlay.set_adjustments(brightness, contrast, gamma)
        self.viewport().update()

    def fit_video(self) -> None:
        """Reset zoom and fit the video to the view."""
        self.resetTransform()
        self._zoom = 1.0
        size = self._video_item.nativeSize()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            self._video_item.setSize(size)
            self._scene.setSceneRect(0, 0, size.width(), size.height())
            self.fitInView(self._video_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.centerOn(self._video_item)
            self._overlay.prepareGeometryChange()
            self._overlay.update()
        self.zoom_changed.emit(self._zoom)

    # ── Pan with keyboard ───────────────────────────────────────────────

    def pan_up(self, step: int = 60) -> None:
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - step)

    def pan_down(self, step: int = 60) -> None:
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + step)

    def pan_left(self, step: int = 60) -> None:
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - step)

    def pan_right(self, step: int = 60) -> None:
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + step)

    # ── Events ──────────────────────────────────────────────────────────

    def _on_native_size_changed(self, size: QSizeF) -> None:
        if size.isValid() and size.width() > 0 and size.height() > 0:
            self._video_item.setSize(size)
            self._scene.setSceneRect(0, 0, size.width(), size.height())
            self.fitInView(self._video_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.centerOn(self._video_item)
            self.hide_codec_banner()
            self.native_size_ready.emit(size)

    def _on_video_frame_changed(self, frame: QVideoFrame) -> None:
        if frame.isValid():
            size = frame.size()
            if size.width() > 0 and size.height() > 0:
                self.hide_codec_banner()
                cur = self._video_item.size()
                if (
                    cur.width() <= 0
                    or cur.height() <= 0
                    or cur == QSizeF(320, 240)
                    or self._scene.sceneRect().isEmpty()
                ):
                    fsize = QSizeF(size.width(), size.height())
                    self._video_item.setSize(fsize)
                    self._scene.setSceneRect(0, 0, fsize.width(), fsize.height())
                    self.fitInView(self._video_item, Qt.AspectRatioMode.KeepAspectRatio)
                    self.centerOn(self._video_item)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = self.ZOOM_STEP if delta > 0 else 1.0 / self.ZOOM_STEP
        new_zoom = self._zoom * factor

        if new_zoom < self.ZOOM_MIN or new_zoom > self.ZOOM_MAX:
            return

        self.scale(factor, factor)
        self._zoom = new_zoom

        # Center video when shrinking or if fits
        if self._zoom <= 1.01 or factor < 1.0:
            self.centerOn(self._video_item)

        self.zoom_changed.emit(self._zoom)

    # ── Video Spatial Crop API ──────────────────────────────────────────

    @property
    def is_cropping(self) -> bool:
        return self._crop_item is not None

    def start_crop(self) -> None:
        """Start interactive rectangular crop mode over video."""
        if self._crop_item is not None:
            return
        size = self._video_item.size()
        if not size.isValid() or size.width() <= 0 or size.height() <= 0:
            size = self._video_item.nativeSize()
        if not size.isValid() or size.width() <= 0 or size.height() <= 0:
            return

        w = int(size.width())
        h = int(size.height())
        self._crop_item = CropOverlayItem(w, h)
        self._crop_item.rect_changed.connect(self.crop_rect_changed)
        self._scene.addItem(self._crop_item)
        self.crop_rect_changed.emit(self._crop_item.crop_rect)

    def cancel_crop(self) -> None:
        """Exit crop mode."""
        if self._crop_item is not None:
            if self._crop_item.scene() == self._scene:
                self._scene.removeItem(self._crop_item)
            self._crop_item = None
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def set_crop_aspect_ratio(self, ratio: Optional[float]) -> None:
        if self._crop_item is not None:
            self._crop_item.set_aspect_ratio(ratio)

    def get_crop_box(self) -> Optional[tuple[int, int, int, int]]:
        if self._crop_item is not None:
            r = self._crop_item.crop_rect.toRect()
            return (r.x(), r.y(), r.width(), r.height())
        return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.is_cropping:
            if event.button() == Qt.MouseButton.MiddleButton:
                self._is_panning = True
                self._pan_start = event.position()
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
            super().mousePressEvent(event)
            return

        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self._is_panning = True
            self._pan_start = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
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
        if self._is_panning and event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self._is_panning = False
            self._pan_start = None
            if not self.is_cropping:
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if not self.is_cropping and event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    @property
    def is_codec_banner_visible(self) -> bool:
        return hasattr(self, "_codec_banner") and not self._codec_banner.isHidden()

    def show_codec_banner(self, custom_msg: Optional[str] = None) -> None:
        if hasattr(self, "_codec_banner"):
            self._codec_banner.show_banner(custom_msg)
            self._update_banner_geometry()

    def hide_codec_banner(self) -> None:
        if hasattr(self, "_codec_banner"):
            self._codec_banner.hide()

    def _update_banner_geometry(self) -> None:
        if hasattr(self, "_codec_banner") and not self._codec_banner.isHidden():
            vw = self.viewport().width()
            bw = min(max(320, vw - 40), 580)
            bh = self._codec_banner.sizeHint().height()
            bx = max(10, (vw - bw) // 2)
            self._codec_banner.setGeometry(bx, 20, bw, bh)

    def set_smart_enhance(
        self, enabled: bool, adaptive_gamma: float = 0.0, adaptive_brightness: int = 0
    ) -> None:
        self._overlay.set_smart_enhance(enabled, adaptive_gamma, adaptive_brightness)
        self.viewport().update()

    def show_osd(self, text: str, is_active: bool = True) -> None:
        if hasattr(self, "_osd_toast"):
            self._osd_toast.show_message(text, is_active)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_banner_geometry()
        if hasattr(self, "_osd_toast") and self._osd_toast.isVisible():
            x = (self.viewport().width() - self._osd_toast.width()) // 2
            self._osd_toast.move(x, 26)
        if abs(self._zoom - 1.0) < 0.02:
            self.fit_video()


class VideoPlayer(QWidget):
    """A video player widget with integrated playback controls.

    Uses QGraphicsVideoItem inside a zoomable QGraphicsView so the user
    can wheel-zoom into the video and pan with mouse drag or keyboard arrows.
    """

    double_clicked = Signal()  # For fullscreen toggle
    playback_started = Signal()
    playback_stopped = Signal()
    playback_error = Signal(str)  # Emitted when a codec/playback error occurs
    speed_changed = Signal(float)  # Emitted when playback speed changes
    trim_save_requested = Signal(Path, float, float, object)  # (path, start_sec, end_sec, crop_box)
    transcode_requested = Signal(Path)  # Emitted to convert video to compatible H.264 MP4
    enhance_save_requested = Signal(Path)  # Emitted to enhance and sharpen video via FFmpeg

    SPEED_PRESETS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._current_path: Optional[Path] = None
        self._is_previewing_trim: bool = False
        self._preview_end_ms: int = 0
        self._has_video_frame: bool = False

        # Smart enhance state
        self._smart_enhance_active: bool = False
        self._adaptive_gamma_boost: float = 0.0
        self._adaptive_brightness_boost: int = 0
        self._luminance_analyzed: bool = False

        # Codec / black screen check timer
        self._codec_check_timer = QTimer(self)
        self._codec_check_timer.setSingleShot(True)
        self._codec_check_timer.timeout.connect(self._check_codec_status)

        # ── Media components ──
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.7)
        self._audio_attached: bool = True

        # Zoomable video display
        self._video_view = ZoomableVideoView()
        self._video_view.double_clicked.connect(self.double_clicked)
        self._player.setVideoOutput(self._video_view.video_item)

        self._is_seeking = False
        self._playback_rate: float = 1.0

        self._setup_ui()
        self._connect_signals()

    # ── Zoom / Pan API (delegated to the view) ──────────────────────────

    @property
    def is_zoomed(self) -> bool:
        return self._video_view.is_zoomed

    def pan_up(self) -> None:
        self._video_view.pan_up()

    def pan_down(self) -> None:
        self._video_view.pan_down()

    def pan_left(self) -> None:
        self._video_view.pan_left()

    def pan_right(self) -> None:
        self._video_view.pan_right()

    def reset_zoom(self) -> None:
        self._video_view.fit_video()

    # ── UI Setup ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video display area (zoomable)
        layout.addWidget(self._video_view, stretch=1)

        # ── Controls bar ──
        controls = QWidget()
        controls.setObjectName("videoControls")
        controls.setStyleSheet(
            """
            QWidget#videoControls {
                background-color: #181825;
                border-top: 1px solid #313244;
                padding: 6px;
            }
            """
        )
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(12, 6, 12, 8)
        controls_layout.setSpacing(6)

        # Progress slider (with trim visualization)
        self._progress_slider = TrimSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 0)
        self._progress_slider.setToolTip("İlerleme")
        controls_layout.addWidget(self._progress_slider)

        # Video trim panel (collapsible)
        self._trim_panel = VideoTrimPanel()
        self._trim_panel.setVisible(False)
        controls_layout.addWidget(self._trim_panel)

        # Bottom row: play + time + volume
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        # Play/Pause
        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("iconButton")
        self._play_btn.setToolTip("Oynat / Duraklat (Space)")
        self._play_btn.setFixedSize(36, 36)
        bottom_row.addWidget(self._play_btn)

        # Stop
        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setObjectName("iconButton")
        self._stop_btn.setToolTip("Durdur")
        self._stop_btn.setFixedSize(36, 36)
        bottom_row.addWidget(self._stop_btn)

        # Time
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setObjectName("infoLabel")
        self._time_label.setMinimumWidth(120)
        bottom_row.addWidget(self._time_label)

        bottom_row.addStretch()

        # Trim button
        self._trim_btn = QPushButton("✂ Kırp")
        self._trim_btn.setObjectName("speedBtn")
        self._trim_btn.setToolTip("Video Süre Kesme / Kırpma (T)")
        self._trim_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._trim_btn.setFixedHeight(30)
        self._trim_btn.clicked.connect(self.toggle_trim)
        bottom_row.addWidget(self._trim_btn)

        # Smart Enhance button
        self._smart_enhance_btn = QPushButton("✨ İyileştir")
        self._smart_enhance_btn.setObjectName("speedBtn")
        self._smart_enhance_btn.setToolTip("Akıllı Kalite İyileştirme (E)")
        self._smart_enhance_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._smart_enhance_btn.setFixedHeight(30)
        self._smart_enhance_btn.clicked.connect(self.toggle_smart_enhance)
        bottom_row.addWidget(self._smart_enhance_btn)

        # Snapshot button
        self._snapshot_btn = QPushButton("📸 Kare Yakala")
        self._snapshot_btn.setObjectName("speedBtn")
        self._snapshot_btn.setToolTip("Videodan Orijinal Çözünürlükte Kare Yakala (S)")
        self._snapshot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._snapshot_btn.setFixedHeight(30)
        self._snapshot_btn.clicked.connect(self.capture_frame_and_save)
        bottom_row.addWidget(self._snapshot_btn)

        # Playback speed button
        self._speed_btn = QPushButton("1.0x")
        self._speed_btn.setObjectName("speedBtn")
        self._speed_btn.setToolTip("Oynatma Hızı: 1.0x ([ / ] kısayolları veya tekerlek ile değiştir)")
        self._speed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._speed_btn.setFixedSize(54, 30)
        self._speed_btn.clicked.connect(self._show_speed_menu)
        self._speed_btn.installEventFilter(self)
        bottom_row.addWidget(self._speed_btn)

        # Reset zoom button (visible when zoomed)
        self._reset_zoom_btn = QPushButton("1:1")
        self._reset_zoom_btn.setObjectName("iconButton")
        self._reset_zoom_btn.setToolTip("Yakınlaştırmayı Sıfırla")
        self._reset_zoom_btn.setFixedSize(36, 36)
        self._reset_zoom_btn.clicked.connect(self.reset_zoom)
        bottom_row.addWidget(self._reset_zoom_btn)

        # Mute
        self._mute_btn = QPushButton("🔊")
        self._mute_btn.setObjectName("iconButton")
        self._mute_btn.setToolTip("Sesi Kapat / Aç")
        self._mute_btn.setFixedSize(36, 36)
        bottom_row.addWidget(self._mute_btn)

        # Volume slider
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(70)
        self._volume_slider.setFixedWidth(100)
        self._volume_slider.setToolTip("Ses Seviyesi")
        bottom_row.addWidget(self._volume_slider)

        controls_layout.addLayout(bottom_row)
        layout.addWidget(controls)

    def _connect_signals(self) -> None:
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)

        self._play_btn.clicked.connect(self.play_pause)
        self._stop_btn.clicked.connect(self.stop)
        self._mute_btn.clicked.connect(self._toggle_mute)

        self._progress_slider.sliderPressed.connect(self._on_seek_start)
        self._progress_slider.sliderReleased.connect(self._on_seek_end)
        self._progress_slider.sliderMoved.connect(self._on_seek_moved)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)

        # Trim panel signals
        self._trim_panel.range_changed.connect(self._on_trim_range_changed)
        self._trim_panel.preview_requested.connect(self._on_trim_preview_requested)
        self._trim_panel.save_requested.connect(self._on_trim_save_requested)
        self._trim_panel.close_requested.connect(self.toggle_trim)
        self._trim_panel.crop_area_toggled.connect(self._on_crop_area_toggled)
        self._trim_panel.crop_ratio_changed.connect(self._video_view.set_crop_aspect_ratio)

        # Video view signals
        self._video_view.crop_rect_changed.connect(self._on_video_crop_rect_changed)
        self._video_view.native_size_ready.connect(self._on_native_size_ready)

        self._player.errorOccurred.connect(self._on_player_error)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

        self._video_view.video_item.videoSink().videoFrameChanged.connect(
            self._on_first_video_frame
        )

        # Transcode & context menu
        self._video_view.transcode_requested.connect(self._on_transcode_requested)
        self._video_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._video_view.customContextMenuRequested.connect(self._show_video_context_menu)

    def _attach_audio(self) -> None:
        """Ensure audio output is attached and enabled."""
        if not self._audio_attached:
            self._audio_attached = True
            self._player.setAudioOutput(self._audio_output)

    def _on_native_size_ready(self, size: QSizeF) -> None:
        if size.isValid() and size.width() > 0:
            self._has_video_frame = True
            self._codec_check_timer.stop()
            self._video_view.hide_codec_banner()

    def _on_first_video_frame(self, frame: QVideoFrame) -> None:
        if frame.isValid() and frame.size().width() > 0:
            self._current_frame = frame
            self._has_video_frame = True
            self._codec_check_timer.stop()
            self._video_view.hide_codec_banner()
            self._attach_audio()
            self._analyze_video_luminance(frame)

    def capture_frame(self) -> Optional[QImage]:
        """Capture the current video frame as an original-resolution QImage."""
        if hasattr(self, "_current_frame") and self._current_frame and self._current_frame.isValid():
            qimg = self._current_frame.toImage()
            if not qimg.isNull():
                return qimg
        return None

    def capture_frame_and_save(self) -> None:
        """Capture current video frame at full native resolution and save to disk."""
        qimg = self.capture_frame()
        if qimg is None:
            self._video_view.show_osd("⚠️ Kare Yakalanamadı", False)
            return

        default_name = "video_kare.png"
        default_dir = ""
        if self._current_path:
            sec = int(self._player.position() / 1000)
            default_name = f"{self._current_path.stem}_kare_{sec:03d}.png"
            default_dir = str(self._current_path.parent / default_name)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Video Karesini Kaydet (Snapshot)",
            default_dir,
            "PNG Dosyası (*.png);;JPEG Dosyası (*.jpg *.jpeg);;Tüm Dosyalar (*)",
        )
        if save_path:
            saved = qimg.save(save_path)
            if saved:
                self._video_view.show_osd(f"📸 Kare Kaydedildi: {Path(save_path).name}", True)
            else:
                QMessageBox.critical(self, "Hata", "Dosya diske kaydedilemedi.")

    def _analyze_video_luminance(self, frame: QVideoFrame) -> None:
        if self._luminance_analyzed:
            return
        if not frame.isValid():
            return
        try:
            qimg = frame.toImage()
            if qimg.isNull():
                return
            thumb = qimg.scaled(
                32, 32, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation
            )
            total_lum = 0.0
            for y in range(0, 32, 2):
                for x in range(0, 32, 2):
                    c = thumb.pixelColor(x, y)
                    lum = 0.2126 * c.red() + 0.7152 * c.green() + 0.0722 * c.blue()
                    total_lum += lum
            avg_lum = total_lum / 256.0
            self._luminance_analyzed = True

            # Dark video (< 75): extra shadow lifting
            if avg_lum < 75:
                self._adaptive_gamma_boost = 0.15
                self._adaptive_brightness_boost = 6
            elif avg_lum > 170:
                self._adaptive_gamma_boost = -0.08
                self._adaptive_brightness_boost = -3
            else:
                self._adaptive_gamma_boost = 0.0
                self._adaptive_brightness_boost = 0

            if self._smart_enhance_active:
                self._video_view.set_smart_enhance(
                    True, self._adaptive_gamma_boost, self._adaptive_brightness_boost
                )
        except Exception:
            pass

    def _on_transcode_requested(self) -> None:
        if self._current_path:
            self.transcode_requested.emit(self._current_path)

    def _on_enhance_save_requested(self) -> None:
        if self._current_path:
            self.enhance_save_requested.emit(self._current_path)

    def _check_codec_status(self) -> None:
        if not self._current_path or not self._player.hasVideo():
            return
        if self._has_video_frame:
            return

        item_size = self._video_view.video_item.size()
        native_size = self._video_view.video_item.nativeSize()
        has_dimensions = (
            (item_size.isValid() and item_size.width() > 0)
            or (native_size.isValid() and native_size.width() > 0)
        )
        if has_dimensions:
            self._has_video_frame = True
            self._video_view.hide_codec_banner()
            return

        # Genuine black screen: has video track, playing for > 4.5s, but 0 frames and 0 dimensions
        if (
            self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
            and self._player.position() > 4500
        ):
            self._video_view.show_codec_banner()

    def _show_video_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)

        is_playing = self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        play_act = menu.addAction("⏸ Duraklat" if is_playing else "▶ Oynat")
        play_act.triggered.connect(self.play_pause)

        is_muted = self._audio_output.isMuted()
        mute_act = menu.addAction("🔊 Sesi Aç" if is_muted else "🔇 Sesi Kapat")
        mute_act.triggered.connect(self._toggle_mute)

        trim_act = menu.addAction("✂ Videoyu Kırp (T)")
        trim_act.triggered.connect(self.toggle_trim)

        snap_act = menu.addAction("📸 Orijinal Çözünürlükte Kare Yakala (S)")
        snap_act.triggered.connect(self.capture_frame_and_save)

        menu.addSeparator()

        # Smart enhance live toggle
        smart_act = menu.addAction("✨ Akıllı Kalite İyileştirme (E)")
        smart_act.setCheckable(True)
        smart_act.setChecked(self._smart_enhance_active)
        smart_act.triggered.connect(self.toggle_smart_enhance)

        # Enhance export with FFmpeg
        enhance_save_act = menu.addAction("🎬 Videoyu İyileştirerek Kaydet (Netleştirme + Parazit Giderme)...")
        enhance_save_act.triggered.connect(self._on_enhance_save_requested)

        menu.addSeparator()

        transcode_act = menu.addAction("🔄 Uyumlu MP4 Formatına Dönüştür...")
        transcode_act.triggered.connect(self._on_transcode_requested)

        menu.addSeparator()

        speed_menu = menu.addMenu(f"Oynatma Hızı ({self._format_speed(self._playback_rate)})")
        for s in self.SPEED_PRESETS:
            label = self._format_speed(s)
            if abs(s - 1.0) < 0.01:
                label += " (Normal)"
            act = speed_menu.addAction(label)
            act.setCheckable(True)
            if abs(s - self._playback_rate) < 0.01:
                act.setChecked(True)
            act.triggered.connect(lambda checked=False, rate=s: self.set_playback_rate(rate))

        menu.exec(self._video_view.mapToGlobal(pos))

    # ── Playback Speed API ──────────────────────────────────────────────

    @property
    def playback_rate(self) -> float:
        return self._playback_rate

    @staticmethod
    def _format_speed(rate: float) -> str:
        if rate == int(rate):
            return f"{rate:.1f}x"
        s = f"{rate:.2f}".rstrip("0").rstrip(".")
        if "." not in s:
            return f"{s}.0x"
        return f"{s}x"

    def set_playback_rate(self, rate: float) -> None:
        rate = round(max(0.25, min(rate, 2.0)), 2)
        self._playback_rate = rate
        self._player.setPlaybackRate(rate)
        formatted = self._format_speed(rate)
        self._speed_btn.setText(formatted)
        self._speed_btn.setToolTip(f"Oynatma Hızı: {formatted} ([ / ] kısayolları veya tekerlek ile değiştir)")
        is_custom = abs(rate - 1.0) > 0.01
        self._speed_btn.setProperty("active", "true" if is_custom else "false")
        self._speed_btn.style().unpolish(self._speed_btn)
        self._speed_btn.style().polish(self._speed_btn)
        self.speed_changed.emit(rate)

    def increase_speed(self) -> None:
        current = self._playback_rate
        for s in self.SPEED_PRESETS:
            if s > current + 0.01:
                self.set_playback_rate(s)
                return

    def decrease_speed(self) -> None:
        current = self._playback_rate
        for s in reversed(self.SPEED_PRESETS):
            if s < current - 0.01:
                self.set_playback_rate(s)
                return

    def reset_speed(self) -> None:
        self.set_playback_rate(1.0)

    # ── Smart Quality Enhancement API ───────────────────────────────────

    @property
    def is_smart_enhanced(self) -> bool:
        return self._smart_enhance_active

    def toggle_smart_enhance(self) -> None:
        """Toggle real-time smart video quality enhancement."""
        self._smart_enhance_active = not self._smart_enhance_active
        self._update_smart_enhance()

    def set_smart_enhance(self, enabled: bool) -> None:
        self._smart_enhance_active = enabled
        self._update_smart_enhance()

    def _update_smart_enhance(self) -> None:
        self._smart_enhance_btn.setProperty("active", "true" if self._smart_enhance_active else "false")
        self._smart_enhance_btn.style().unpolish(self._smart_enhance_btn)
        self._smart_enhance_btn.style().polish(self._smart_enhance_btn)
        self._video_view.set_smart_enhance(
            self._smart_enhance_active,
            self._adaptive_gamma_boost,
            self._adaptive_brightness_boost,
        )
        msg = (
            "✨ Akıllı İyileştirme: AÇIK (Canlı & Net)"
            if self._smart_enhance_active
            else "⚪ Akıllı İyileştirme: KAPALI"
        )
        self._video_view.show_osd(msg, self._smart_enhance_active)

    def _show_speed_menu(self) -> None:
        menu = QMenu(self)
        for s in self.SPEED_PRESETS:
            label = self._format_speed(s)
            if abs(s - 1.0) < 0.01:
                label += " (Normal)"
            action = menu.addAction(label)
            action.setCheckable(True)
            if abs(s - self._playback_rate) < 0.01:
                action.setChecked(True)
            action.triggered.connect(lambda checked=False, rate=s: self.set_playback_rate(rate))

        btn_pos = self._speed_btn.mapToGlobal(QPoint(0, 0))
        menu_height = menu.sizeHint().height()
        menu.exec(QPoint(btn_pos.x(), btn_pos.y() - menu_height - 4))

    def eventFilter(self, watched, event) -> bool:
        if watched == self._speed_btn and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta > 0:
                self.increase_speed()
                return True
            elif delta < 0:
                self.decrease_speed()
                return True
        return super().eventFilter(watched, event)

    # ── Video Trim API ──────────────────────────────────────────────────

    @property
    def is_trimming(self) -> bool:
        return not self._trim_panel.isHidden()

    def toggle_trim(self) -> None:
        """Toggle video trim mode on or off."""
        is_visible = self._trim_panel.isHidden()
        self._trim_panel.setVisible(is_visible)

        # Style button to show active state
        self._trim_btn.setProperty("active", "true" if is_visible else "false")
        self._trim_btn.style().unpolish(self._trim_btn)
        self._trim_btn.style().polish(self._trim_btn)

        if is_visible:
            self._trim_panel.reset_for_video(self._player.duration())
            self._progress_slider.set_trim_range(
                True, self._trim_panel.start_ms, self._trim_panel.end_ms
            )
        else:
            self._is_previewing_trim = False
            self._progress_slider.set_trim_range(False, 0, 0)
            self._video_view.cancel_crop()

    def set_trim_in_point(self) -> None:
        """Set In-point (start) to current playback position."""
        if self._trim_panel.isVisible():
            self._trim_panel._set_start_to_current()

    def set_trim_out_point(self) -> None:
        """Set Out-point (end) to current playback position."""
        if self._trim_panel.isVisible():
            self._trim_panel._set_end_to_current()

    def _on_trim_range_changed(self, start_ms: int, end_ms: int) -> None:
        self._progress_slider.set_trim_range(True, start_ms, end_ms)

    def _on_trim_preview_requested(self, start_ms: int, end_ms: int) -> None:
        self._is_previewing_trim = True
        self._preview_end_ms = end_ms
        self._attach_audio()
        self._player.setPosition(start_ms)
        self._player.play()

    def _on_crop_area_toggled(self, active: bool) -> None:
        if active:
            self._video_view.start_crop()
        else:
            self._video_view.cancel_crop()

    def _on_video_crop_rect_changed(self, rect: QRectF) -> None:
        r = rect.toRect()
        self._trim_panel.set_crop_box(r.x(), r.y(), r.width(), r.height())

    def _on_trim_save_requested(
        self, start_sec: float, end_sec: float, crop_box: Optional[tuple[int, int, int, int]]
    ) -> None:
        if self._current_path:
            self.trim_save_requested.emit(self._current_path, start_sec, end_sec, crop_box)

    # ── Playback API ────────────────────────────────────────────────────

    def load_video(self, path: str | Path) -> None:
        self._current_path = Path(path).resolve()
        self._has_video_frame = False
        self._luminance_analyzed = False
        self._adaptive_gamma_boost = 0.0
        self._adaptive_brightness_boost = 0
        self._video_view.hide_codec_banner()
        self._codec_check_timer.start(5000)
        if self._smart_enhance_active:
            self._video_view.set_smart_enhance(True)

        self._player.stop()
        self._player.setAudioOutput(self._audio_output)
        self._audio_attached = True

        url = QUrl.fromLocalFile(str(self._current_path))
        self._player.setSource(url)
        self._play_btn.setText("▶")
        self._time_label.setText("00:00 / 00:00")
        self.set_playback_rate(1.0)
        self._video_view.fit_video()
        self._trim_panel.reset_for_video(0)
        self._player.play()

    def play_pause(self) -> None:
        self._attach_audio()
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def play(self) -> None:
        self._attach_audio()
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()
        self._progress_slider.setValue(0)
        self._time_label.setText("00:00 / 00:00")
        self.playback_stopped.emit()

    def apply_adjustments(self, brightness: int, contrast: int, gamma: float) -> None:
        """Apply brightness/contrast/gamma color adjustments to video."""
        self._video_view.apply_adjustments(brightness, contrast, gamma)

    def cleanup(self) -> None:
        self._codec_check_timer.stop()
        self._has_video_frame = False
        self._luminance_analyzed = False
        self._video_view.hide_codec_banner()
        self._player.stop()
        self._player.setSource(QUrl())
        self._current_path = None
        self._is_previewing_trim = False
        self._video_view.cancel_crop()
        if self._trim_panel.isVisible():
            self.toggle_trim()
        self.apply_adjustments(0, 0, 1.0)
        if self._smart_enhance_active:
            self._video_view.set_smart_enhance(True)

    def skip_forward(self, ms: int = 5000) -> None:
        new_pos = min(self._player.position() + ms, self._player.duration())
        self._player.setPosition(new_pos)

    def skip_backward(self, ms: int = 5000) -> None:
        new_pos = max(self._player.position() - ms, 0)
        self._player.setPosition(new_pos)

    # ── Private Slots ───────────────────────────────────────────────────

    @Slot(int)
    def _on_position_changed(self, position: int) -> None:
        if not self._is_seeking:
            self._progress_slider.setValue(position)
        duration = self._player.duration()
        self._time_label.setText(
            f"{self._format_time(position)} / {self._format_time(duration)}"
        )

        if self._is_previewing_trim and position >= self._preview_end_ms:
            self._player.pause()
            self._is_previewing_trim = False

        # Detect black screen (audio playing for > 5.0s with no video frame decoded)
        if (
            position > 5000
            and self._player.hasVideo()
            and not self._has_video_frame
            and not self._video_view.is_codec_banner_visible
        ):
            item_size = self._video_view.video_item.size()
            native_size = self._video_view.video_item.nativeSize()
            has_dimensions = (
                (item_size.isValid() and item_size.width() > 0)
                or (native_size.isValid() and native_size.width() > 0)
            )
            if not has_dimensions:
                self._video_view.show_codec_banner()
            else:
                self._has_video_frame = True
                self._video_view.hide_codec_banner()

        self._trim_panel.update_state(position, duration)

        # Ensure video is sized to native resolution and centered if not yet done
        native_size = self._video_view.video_item.nativeSize()
        if (
            native_size.isValid()
            and native_size.width() > 0
            and self._video_view.video_item.size() != native_size
        ):
            self._video_view.fit_video()

    @Slot(int)
    def _on_duration_changed(self, duration: int) -> None:
        self._progress_slider.setRange(0, duration)
        self._trim_panel.update_state(self._player.position(), duration)
        if self._trim_panel.isVisible():
            self._progress_slider.set_trim_range(
                True, self._trim_panel.start_ms, self._trim_panel.end_ms
            )

    @Slot(QMediaPlayer.PlaybackState)
    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_btn.setText("⏸")
            self._play_btn.setToolTip("Duraklat (Space)")
            if not self._video_view.is_zoomed:
                self._video_view.fit_video()
            self.playback_started.emit()
        else:
            self._play_btn.setText("▶")
            self._play_btn.setToolTip("Oynat (Space)")
            if state == QMediaPlayer.PlaybackState.StoppedState:
                self.playback_stopped.emit()

    @Slot(QMediaPlayer.MediaStatus)
    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status in (
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
        ):
            if not self._video_view.is_zoomed:
                self._video_view.fit_video()
            if not self._player.hasVideo():
                self._attach_audio()

    def _on_seek_start(self) -> None:
        self._is_seeking = True

    def _on_seek_end(self) -> None:
        self._is_seeking = False
        self._player.setPosition(self._progress_slider.value())

    def _on_seek_moved(self, position: int) -> None:
        duration = self._player.duration()
        self._time_label.setText(
            f"{self._format_time(position)} / {self._format_time(duration)}"
        )

    def _on_volume_changed(self, value: int) -> None:
        self._audio_output.setVolume(value / 100.0)
        self._update_volume_icon(value)

    def _toggle_mute(self) -> None:
        muted = not self._audio_output.isMuted()
        self._audio_output.setMuted(muted)
        if muted:
            self._mute_btn.setText("🔇")
        else:
            self._update_volume_icon(self._volume_slider.value())

    def _update_volume_icon(self, volume: int) -> None:
        if volume == 0:
            self._mute_btn.setText("🔇")
        elif volume < 33:
            self._mute_btn.setText("🔈")
        elif volume < 66:
            self._mute_btn.setText("🔉")
        else:
            self._mute_btn.setText("🔊")

    @staticmethod
    def _format_time(ms: int) -> str:
        if ms < 0:
            ms = 0
        total_seconds = ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @Slot(QMediaPlayer.Error, str)
    def _on_player_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        if error != QMediaPlayer.Error.NoError:
            self._video_view.show_codec_banner(
                f"Video oynatılırken hata oluştu ({error.name}):\n{error_string}\n"
                "Bu video için gerekli çözücü sistemde bulunamadı."
            )
            self.playback_error.emit(f"{error_string} (Hata Kodu: {error.name})")

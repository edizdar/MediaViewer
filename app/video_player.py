"""Video player widget with zoom, keyboard pan, and playback controls."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl, Slot, QSizeF
from PySide6.QtGui import QMouseEvent, QWheelEvent, QPainter
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSizePolicy,
    QGraphicsView,
    QGraphicsScene,
)


class ZoomableVideoView(QGraphicsView):
    """A QGraphicsView that displays video via QGraphicsVideoItem with
    mouse-wheel zoom and drag-to-pan support.
    """

    double_clicked = Signal()
    zoom_changed = Signal(float)

    ZOOM_MIN = 0.5
    ZOOM_MAX = 10.0
    ZOOM_STEP = 1.15

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._video_item = QGraphicsVideoItem()
        self._scene.addItem(self._video_item)

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
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

        # Fit video when its native size becomes known
        self._video_item.nativeSizeChanged.connect(self._on_native_size_changed)

    @property
    def video_item(self) -> QGraphicsVideoItem:
        return self._video_item

    @property
    def is_zoomed(self) -> bool:
        return self._zoom > 1.01

    @property
    def current_zoom(self) -> float:
        return self._zoom

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

    def mousePressEvent(self, event: QMouseEvent) -> None:
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
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self._is_panning = False
            self._pan_start = None
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # ── Media components ──
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.7)

        # Zoomable video display
        self._video_view = ZoomableVideoView()
        self._video_view.double_clicked.connect(self.double_clicked)
        self._player.setVideoOutput(self._video_view.video_item)

        self._is_seeking = False

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

        # Progress slider
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 0)
        self._progress_slider.setToolTip("İlerleme")
        controls_layout.addWidget(self._progress_slider)

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

        self._player.errorOccurred.connect(self._on_player_error)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

    # ── Playback API ────────────────────────────────────────────────────

    def load_video(self, path: str | Path) -> None:
        self._player.stop()
        url = QUrl.fromLocalFile(str(Path(path).resolve()))
        self._player.setSource(url)
        self._play_btn.setText("▶")
        self._time_label.setText("00:00 / 00:00")
        self._video_view.fit_video()
        self._player.play()

    def play_pause(self) -> None:
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()
        self._progress_slider.setValue(0)
        self._time_label.setText("00:00 / 00:00")
        self.playback_stopped.emit()

    def cleanup(self) -> None:
        self._player.stop()
        self._player.setSource(QUrl())

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
            self.playback_error.emit(f"{error_string} (Hata Kodu: {error.name})")

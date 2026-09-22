"""Main window — assembles all widgets and manages application logic."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QKeySequence, QShortcut, QDragEnterEvent, QDropEvent, QCursor
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QStackedWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QApplication,
)

from app.file_manager import FileManager
from app.image_viewer import ImageViewer
from app.video_player import VideoPlayer
from app.image_adjustments import AdjustmentsPanel
from app.playlist import PlaylistPanel
from app.toolbar import TopToolbar, BottomToolbar
from app.styles import DARK_THEME


class WelcomeWidget(QWidget):
    """Welcome screen shown when no file is open."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("📷  Media Viewer")
        title.setObjectName("welcomeLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #89b4fa;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Dosya açmak için Ctrl+O tuşuna basın\n"
            "veya bir dosyayı sürükleyip bırakın"
        )
        subtitle.setObjectName("welcomeLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; margin-top: 12px;")
        layout.addWidget(subtitle)


class MainWindow(QMainWindow):
    """Main application window for the Media Viewer."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Media Viewer")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        # Apply dark theme
        self.setStyleSheet(DARK_THEME)

        # Enable drag and drop
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        # ── Core components ──
        self._file_manager = FileManager()
        self._image_viewer = ImageViewer()
        self._video_player = VideoPlayer()
        self._welcome = WelcomeWidget()
        self._adjustments_panel = AdjustmentsPanel()
        self._adjustments_panel.setVisible(False)
        self._playlist_panel = PlaylistPanel()
        self._playlist_panel.setVisible(False)

        # Track current image dimensions
        self._current_image_size: Optional[tuple[int, int]] = None

        # ── Layout ──
        central = QWidget(self)
        central.setMouseTracking(True)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top toolbar
        self._top_toolbar = TopToolbar()
        main_layout.addWidget(self._top_toolbar)

        # ── Content area: playlist | stack | adjustments ──
        content_area = QHBoxLayout()
        content_area.setContentsMargins(0, 0, 0, 0)
        content_area.setSpacing(0)

        # Playlist panel (left side, toggled)
        content_area.addWidget(self._playlist_panel)

        # Stacked widget for content
        self._stack = QStackedWidget()
        self._stack.addWidget(self._welcome)      # index 0
        self._stack.addWidget(self._image_viewer)  # index 1
        self._stack.addWidget(self._video_player)  # index 2
        self._stack.setCurrentIndex(0)
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        content_area.addWidget(self._stack, stretch=1)

        # Adjustments panel (right side, toggled)
        content_area.addWidget(self._adjustments_panel)

        main_layout.addLayout(content_area, stretch=1)

        # Bottom toolbar
        self._bottom_toolbar = BottomToolbar()
        main_layout.addWidget(self._bottom_toolbar)

        # ── Fullscreen Overlay Floating Controls (Hidden by default) ──
        self._fs_exit_btn = QPushButton("✕  Çıkış", central)
        self._fs_exit_btn.setObjectName("fsExitBtn")
        self._fs_exit_btn.setToolTip("Tam Ekrandan Çık (Esc veya F11)")
        self._fs_exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_exit_btn.hide()
        self._fs_exit_btn.clicked.connect(self._exit_fullscreen)

        self._fs_prev_btn = QPushButton("❮", central)
        self._fs_prev_btn.setObjectName("fsNavBtn")
        self._fs_prev_btn.setToolTip("Önceki Dosya (←)")
        self._fs_prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_prev_btn.hide()
        self._fs_prev_btn.clicked.connect(self._on_nav_prev)

        self._fs_next_btn = QPushButton("❯", central)
        self._fs_next_btn.setObjectName("fsNavBtn")
        self._fs_next_btn.setToolTip("Sonraki Dosya (→)")
        self._fs_next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_next_btn.hide()
        self._fs_next_btn.clicked.connect(self._on_nav_next)

        # Timer to monitor cursor position in fullscreen (runs only in fullscreen)
        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(50)  # Check every 50ms
        self._hover_timer.timeout.connect(self._check_fullscreen_hover)

        self._connect_signals()
        self._setup_shortcuts()

        # Install application-level event filter for guaranteed key routing
        QApplication.instance().installEventFilter(self)

    def _connect_signals(self) -> None:
        """Wire up all signals between components."""
        # Top toolbar
        self._top_toolbar.open_file_clicked.connect(self.open_file_dialog)
        self._top_toolbar.previous_clicked.connect(self._on_nav_prev)
        self._top_toolbar.next_clicked.connect(self._on_nav_next)
        self._top_toolbar.fullscreen_clicked.connect(self._toggle_fullscreen)
        self._top_toolbar.playlist_toggled.connect(self._toggle_playlist)

        # Bottom toolbar
        self._bottom_toolbar.zoom_in_clicked.connect(self._image_viewer.zoom_in)
        self._bottom_toolbar.zoom_out_clicked.connect(self._image_viewer.zoom_out)
        self._bottom_toolbar.fit_clicked.connect(self._image_viewer.fit_to_window)
        self._bottom_toolbar.original_clicked.connect(self._image_viewer.original_size)
        self._bottom_toolbar.rotate_cw_clicked.connect(self._image_viewer.rotate_cw)
        self._bottom_toolbar.rotate_ccw_clicked.connect(self._image_viewer.rotate_ccw)
        self._bottom_toolbar.delete_clicked.connect(self._delete_current_file)
        self._bottom_toolbar.adjustments_toggled.connect(self._toggle_adjustments)

        # Image viewer
        self._image_viewer.zoom_changed.connect(self._bottom_toolbar.set_zoom_level)
        self._image_viewer.double_clicked.connect(self._toggle_fullscreen)
        self._image_viewer.image_loaded.connect(self._on_image_loaded)

        # Video player
        self._video_player.double_clicked.connect(self._toggle_fullscreen)
        self._video_player.playback_error.connect(self._on_playback_error)

        # Adjustments panel
        self._adjustments_panel.adjustments_changed.connect(
            self._on_adjustments_changed
        )

        # Playlist panel
        self._playlist_panel.file_selected.connect(
            lambda path: self.open_file(path)
        )
        self._playlist_panel._add_current_btn.clicked.connect(
            self._add_current_to_playlist
        )

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts."""
        shortcuts = {
            "Ctrl+O": self.open_file_dialog,
            "Ctrl++": self._image_viewer.zoom_in,
            "Ctrl+=": self._image_viewer.zoom_in,
            "Ctrl+-": self._image_viewer.zoom_out,
            "Ctrl+0": self._image_viewer.original_size,
            "Ctrl+F": self._image_viewer.fit_to_window,
            "R": self._image_viewer.rotate_cw,
            "Shift+R": self._image_viewer.rotate_ccw,
            "Delete": self._delete_current_file,
            "Ctrl+J": self._toggle_adjustments,
            "Ctrl+L": self._toggle_playlist,
        }

        for key, slot in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(slot)

    # ── Global Event Filter for Keys ───────────────────────────────────

    def eventFilter(self, watched, event) -> bool:
        """Intercept key presses globally so child widgets cannot swallow them."""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            in_video = self._stack.currentIndex() == 2
            video_zoomed = in_video and self._video_player.is_zoomed

            if key == Qt.Key.Key_Left:
                if video_zoomed:
                    self._video_player.pan_left()
                else:
                    self._on_nav_prev()
                return True

            elif key == Qt.Key.Key_Right:
                if video_zoomed:
                    self._video_player.pan_right()
                else:
                    self._on_nav_next()
                return True

            elif key == Qt.Key.Key_Up:
                if video_zoomed:
                    self._video_player.pan_up()
                    return True

            elif key == Qt.Key.Key_Down:
                if video_zoomed:
                    self._video_player.pan_down()
                    return True

            elif key == Qt.Key.Key_Space:
                if in_video:
                    self._video_player.play_pause()
                else:
                    self._on_nav_next()
                return True

            elif key == Qt.Key.Key_Escape:
                if self.isFullScreen():
                    self._exit_fullscreen()
                    return True

            elif key == Qt.Key.Key_F11:
                self._toggle_fullscreen()
                return True

            if in_video:
                text = event.text()
                if text == "[" or key == Qt.Key.Key_BracketLeft or text == "<":
                    self._video_player.decrease_speed()
                    return True
                elif text == "]" or key == Qt.Key.Key_BracketRight or text == ">":
                    self._video_player.increase_speed()
                    return True
                elif text == "\\" or key in (Qt.Key.Key_Backslash, Qt.Key.Key_Backspace):
                    self._video_player.reset_speed()
                    return True

        return super().eventFilter(watched, event)

    # ── Fullscreen Hover Detection (Only reveals when mouse is in zone) ──

    def _update_overlay_positions(self) -> None:
        """Calculate geometry for exit and nav buttons."""
        w = self.centralWidget().width()
        h = self.centralWidget().height()

        # Exit button at top-right
        btn_w = 96
        btn_h = 36
        self._fs_exit_btn.resize(btn_w, btn_h)
        self._fs_exit_btn.move(w - btn_w - 20, 16)

        # Nav buttons on left and right edges, vertically centered
        nav_w, nav_h = 46, 74
        self._fs_prev_btn.resize(nav_w, nav_h)
        self._fs_prev_btn.move(14, (h - nav_h) // 2)

        self._fs_next_btn.resize(nav_w, nav_h)
        self._fs_next_btn.move(w - nav_w - 14, (h - nav_h) // 2)

    def _check_fullscreen_hover(self) -> None:
        """Poll cursor position in fullscreen. Show buttons ONLY when cursor hovers in their zone."""
        if not self.isFullScreen():
            self._fs_exit_btn.hide()
            self._fs_prev_btn.hide()
            self._fs_next_btn.hide()
            self._hover_timer.stop()
            return

        # Get local coordinates of mouse relative to centralWidget
        global_pos = QCursor.pos()
        local_pos = self.centralWidget().mapFromGlobal(global_pos)
        x = local_pos.x()
        y = local_pos.y()
        w = self.centralWidget().width()
        h = self.centralWidget().height()

        # If cursor is outside the window, hide all
        if not (0 <= x <= w and 0 <= y <= h):
            self._fs_exit_btn.hide()
            self._fs_prev_btn.hide()
            self._fs_next_btn.hide()
            return

        self._update_overlay_positions()

        # 1. Top-Right: Exit button zone (only top-right corner)
        in_exit_zone = (x >= w - 160 and y <= 65) or self._fs_exit_btn.underMouse()
        if in_exit_zone:
            if not self._fs_exit_btn.isVisible():
                self._fs_exit_btn.show()
            self._fs_exit_btn.raise_()
        else:
            if self._fs_exit_btn.isVisible():
                self._fs_exit_btn.hide()

        # Check if multiple files exist for navigation
        has_multiple = (
            (self._playlist_panel.is_active and self._playlist_panel.manager.count > 1)
            or self._file_manager.file_count > 1
        )

        # 2. Left Edge: Prev button zone
        in_prev_zone = has_multiple and (
            (x <= 80 and h * 0.15 <= y <= h * 0.85) or self._fs_prev_btn.underMouse()
        )
        if in_prev_zone:
            if not self._fs_prev_btn.isVisible():
                self._fs_prev_btn.show()
            self._fs_prev_btn.raise_()
        else:
            if self._fs_prev_btn.isVisible():
                self._fs_prev_btn.hide()

        # 3. Right Edge: Next button zone
        in_next_zone = has_multiple and (
            (x >= w - 80 and h * 0.15 <= y <= h * 0.85) or self._fs_next_btn.underMouse()
        )
        if in_next_zone:
            if not self._fs_next_btn.isVisible():
                self._fs_next_btn.show()
            self._fs_next_btn.raise_()
        else:
            if self._fs_next_btn.isVisible():
                self._fs_next_btn.hide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isFullScreen():
            self._update_overlay_positions()

    # ── Navigation Dispatchers ──────────────────────────────────────────

    def _on_nav_next(self) -> None:
        """Go to the next file (playlist takes priority if active)."""
        if self._playlist_panel.is_active:
            self._playlist_next()
        else:
            self._next_file()

    def _on_nav_prev(self) -> None:
        """Go to the previous file (playlist takes priority if active)."""
        if self._playlist_panel.is_active:
            self._playlist_previous()
        else:
            self._previous_file()

    # ── File Operations ─────────────────────────────────────────────────

    def open_file_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Medya Dosyası Aç",
            "",
            self._file_manager.get_file_filter(),
        )
        if file_path:
            self.open_file(file_path)

    def open_file(self, path: str | Path) -> None:
        """Open and display the given file."""
        path = Path(path).resolve()

        if not path.is_file():
            QMessageBox.warning(self, "Hata", f"Dosya bulunamadı:\n{path}")
            return

        # Stop any current video playback
        self._video_player.cleanup()

        # Load file manager with directory contents
        self._file_manager.load_from_file(path)

        if self._file_manager.is_image(path):
            self._show_image(path)
        elif self._file_manager.is_video(path):
            self._show_video(path)
        else:
            QMessageBox.warning(
                self,
                "Desteklenmeyen Format",
                f"Bu dosya formatı desteklenmiyor:\n{path.suffix}",
            )
            return

        self._update_toolbar_info()

    def _show_image(self, path: Path) -> None:
        success = self._image_viewer.load_image(path)
        if not success:
            QMessageBox.warning(self, "Hata", f"Fotoğraf yüklenemedi:\n{path}")
            return

        self._stack.setCurrentIndex(1)
        self._bottom_toolbar.show_image_controls()
        self.setWindowTitle(f"{path.name} — Media Viewer")

        if self._adjustments_panel.has_adjustments():
            self._adjustments_panel.reset()

    def _show_video(self, path: Path) -> None:
        self._video_player.load_video(path)
        self._stack.setCurrentIndex(2)
        self._bottom_toolbar.show_video_controls()
        self._current_image_size = None
        self._bottom_toolbar.set_file_info(self._file_manager.get_file_size_str(path))
        self.setWindowTitle(f"{path.name} — Media Viewer")

    def _on_playback_error(self, err_msg: str) -> None:
        QMessageBox.warning(
            self,
            "Video Oynatma Hatası",
            f"Video oynatılamadı:\n{err_msg}\n\n"
            "Bu video formatı için gerekli codec sisteminizde eksik olabilir.\n"
            "(Örn: K-Lite Codec Pack veya HEVC Video Uzantısı gerekebilir.)"
        )

    def _on_image_loaded(self, width: int, height: int) -> None:
        self._current_image_size = (width, height)
        size_str = self._file_manager.get_file_size_str()
        self._bottom_toolbar.set_file_info(f"{width}×{height}  •  {size_str}")

    def _update_toolbar_info(self) -> None:
        current = self._file_manager.current_file
        if current:
            if self._playlist_panel.is_active:
                mgr = self._playlist_panel.manager
                self._top_toolbar.set_file_info(
                    f"📋 {current.name}",
                    mgr.current_index,
                    mgr.count,
                )
            else:
                self._top_toolbar.set_file_info(
                    current.name,
                    self._file_manager.current_index,
                    self._file_manager.file_count,
                )
        else:
            self._top_toolbar.clear()

    # ── Directory Navigation ────────────────────────────────────────────

    def _next_file(self) -> None:
        path = self._file_manager.next_file()
        if path:
            self._navigate_to(path)

    def _previous_file(self) -> None:
        path = self._file_manager.previous_file()
        if path:
            self._navigate_to(path)

    def _navigate_to(self, path: Path) -> None:
        self._video_player.cleanup()

        if self._file_manager.is_image(path):
            self._show_image(path)
        elif self._file_manager.is_video(path):
            self._show_video(path)

        self._update_toolbar_info()

    # ── Playlist Navigation ─────────────────────────────────────────────

    def _playlist_next(self) -> None:
        path_str = self._playlist_panel.next_file()
        if path_str:
            self._open_playlist_file(Path(path_str))

    def _playlist_previous(self) -> None:
        path_str = self._playlist_panel.previous_file()
        if path_str:
            self._open_playlist_file(Path(path_str))

    def _open_playlist_file(self, path: Path) -> None:
        """Open a file from the playlist without modifying file_manager navigation."""
        if not path.is_file():
            return

        self._video_player.cleanup()
        self._file_manager.load_from_file(path)

        if self._file_manager.is_image(path):
            self._show_image(path)
        elif self._file_manager.is_video(path):
            self._show_video(path)

        self._update_toolbar_info()

    def _add_current_to_playlist(self) -> None:
        current = self._file_manager.current_file
        if current:
            self._playlist_panel.add_current_file(current)

    # ── Fullscreen ──────────────────────────────────────────────────────

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self) -> None:
        self._top_toolbar.setVisible(False)
        self._bottom_toolbar.setVisible(False)
        self._adjustments_panel.setVisible(False)
        self._playlist_panel.setVisible(False)
        # Ensure buttons start hidden
        self._fs_exit_btn.hide()
        self._fs_prev_btn.hide()
        self._fs_next_btn.hide()
        self.showFullScreen()
        # Start hover detection timer
        self._hover_timer.start()

    def _exit_fullscreen(self) -> None:
        if not self.isFullScreen():
            return
        self._hover_timer.stop()
        self._fs_exit_btn.hide()
        self._fs_prev_btn.hide()
        self._fs_next_btn.hide()
        self._top_toolbar.setVisible(True)
        self._bottom_toolbar.setVisible(True)
        self.showNormal()

    # ── Panel Toggles ───────────────────────────────────────────────────

    def _toggle_adjustments(self) -> None:
        visible = not self._adjustments_panel.isVisible()
        self._adjustments_panel.setVisible(visible)

    def _toggle_playlist(self) -> None:
        visible = not self._playlist_panel.isVisible()
        self._playlist_panel.setVisible(visible)
        if visible:
            self._update_toolbar_info()

    def _on_adjustments_changed(
        self, brightness: int, contrast: int, gamma: float
    ) -> None:
        if self._stack.currentIndex() == 1:
            self._image_viewer.apply_adjustments(brightness, contrast, gamma)

    # ── Delete ──────────────────────────────────────────────────────────

    def _delete_current_file(self) -> None:
        current = self._file_manager.current_file
        if current is None:
            return

        reply = QMessageBox.question(
            self,
            "Dosyayı Sil",
            f"Bu dosyayı çöp kutusuna göndermek istediğinize emin misiniz?\n\n{current.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        file_to_delete = current
        next_path = self._file_manager.delete_current()

        try:
            from send2trash import send2trash

            send2trash(str(file_to_delete))
        except ImportError:
            try:
                file_to_delete.unlink()
            except OSError as e:
                QMessageBox.warning(self, "Hata", f"Dosya silinemedi:\n{e}")
                return

        if next_path:
            self._navigate_to(next_path)
            self._update_toolbar_info()
        else:
            self._stack.setCurrentIndex(0)
            self._top_toolbar.clear()
            self._bottom_toolbar.clear()
            self.setWindowTitle("Media Viewer")

    # ── Drag & Drop ─────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                suffix = Path(file_path).suffix.lower()
                if suffix in FileManager.ALL_EXTENSIONS:
                    self.open_file(file_path)
                    return
        event.ignore()

"""Video trimming components and FFmpeg background worker for Media Viewer."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QThread, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStyle,
    QStyleOptionSlider,
)


def get_ffmpeg_executable() -> Optional[str]:
    """Find a usable ffmpeg executable, trying imageio_ffmpeg first, then PATH."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    return None


class VideoTrimWorker(QThread):
    """Background worker thread that runs FFmpeg to trim a video segment."""

    finished = Signal(bool, str, str)  # (success, message, output_path)

    def __init__(
        self,
        ffmpeg_exe: str,
        input_path: Path,
        output_path: Path,
        start_sec: float,
        end_sec: float,
        parent=None,
    ):
        super().__init__(parent)
        self._ffmpeg = ffmpeg_exe
        self._input = input_path
        self._output = output_path
        self._start = max(0.0, start_sec)
        self._end = max(self._start + 0.1, end_sec)

    def run(self) -> None:
        start_str = f"{self._start:.3f}"
        end_str = f"{self._end:.3f}"

        # 1. Attempt lossless stream copy first (-c copy)
        cmd_copy = [
            self._ffmpeg,
            "-y",
            "-ss",
            start_str,
            "-to",
            end_str,
            "-i",
            str(self._input),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            str(self._output),
        ]

        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            res = subprocess.run(
                cmd_copy,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
            )

            # Check if output exists and is non-empty
            if res.returncode == 0 and self._output.is_file() and self._output.stat().st_size > 1024:
                self.finished.emit(True, "Kayıpsız kesme başarıyla tamamlandı.", str(self._output))
                return
        except Exception:
            pass

        # 2. Fallback to fast re-encode if stream copy fails
        cmd_reencode = [
            self._ffmpeg,
            "-y",
            "-ss",
            start_str,
            "-to",
            end_str,
            "-i",
            str(self._input),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "22",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(self._output),
        ]

        try:
            res2 = subprocess.run(
                cmd_reencode,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
            )

            if res2.returncode == 0 and self._output.is_file() and self._output.stat().st_size > 1024:
                self.finished.emit(True, "Yeniden kodlama ile video başarıyla kesildi.", str(self._output))
            else:
                err_msg = res2.stderr[-400:] if res2.stderr else "Bilinmeyen FFmpeg hatası."
                self.finished.emit(False, f"Kesme başarısız oldu:\n{err_msg}", "")
        except Exception as e:
            self.finished.emit(False, f"FFmpeg çalıştırma hatası: {e}", "")


class TrimSlider(QSlider):
    """QSlider that visually renders the trim range and markers on its track."""

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._trim_active = False
        self._start_ms = 0
        self._end_ms = 0

    def set_trim_range(self, active: bool, start_ms: int, end_ms: int) -> None:
        self._trim_active = active
        self._start_ms = start_ms
        self._end_ms = end_ms
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        if not self._trim_active or self.maximum() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider,
            opt,
            QStyle.SubControl.SC_SliderGroove,
            self,
        )

        max_val = max(1, self.maximum())
        clamped_start = max(0, min(self._start_ms, max_val))
        clamped_end = max(clamped_start, min(self._end_ms, max_val))

        track_left = groove_rect.left() + 6
        track_width = max(1, groove_rect.width() - 12)

        x_start = track_left + int((clamped_start / max_val) * track_width)
        x_end = track_left + int((clamped_end / max_val) * track_width)

        # Highlight band
        band_rect = QRect(
            x_start,
            groove_rect.top() - 1,
            max(2, x_end - x_start),
            groove_rect.height() + 2,
        )
        painter.fillRect(band_rect, QColor(137, 180, 250, 110))

        # Start and end tick markers
        pen_marker = QPen(QColor(166, 227, 161), 2.5)  # Light green for start
        painter.setPen(pen_marker)
        painter.drawLine(x_start, groove_rect.top() - 4, x_start, groove_rect.bottom() + 4)

        pen_marker.setColor(QColor(243, 139, 168))  # Red/pink for end
        painter.setPen(pen_marker)
        painter.drawLine(x_end, groove_rect.top() - 4, x_end, groove_rect.bottom() + 4)

        painter.end()


class VideoTrimPanel(QWidget):
    """Control panel for selecting video trim start and end points and exporting."""

    preview_requested = Signal(int, int)  # (start_ms, end_ms)
    save_requested = Signal(float, float)  # (start_sec, end_sec)
    close_requested = Signal()
    range_changed = Signal(int, int)  # (start_ms, end_ms)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoTrimPanel")
        self.setStyleSheet(
            """
            QWidget#videoTrimPanel {
                background-color: #11111b;
                border-top: 1px solid #313244;
                border-bottom: 1px solid #313244;
                padding: 6px;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 12px;
            }
            QLabel#badge {
                background-color: #313244;
                color: #89b4fa;
                font-weight: bold;
                border-radius: 4px;
                padding: 2px 8px;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 3px 8px;
                font-size: 12px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QPushButton#setStartBtn {
                border-color: #a6e3a1;
                color: #a6e3a1;
                font-weight: bold;
            }
            QPushButton#setStartBtn:hover {
                background-color: rgba(166, 227, 161, 0.2);
            }
            QPushButton#setEndBtn {
                border-color: #f38ba8;
                color: #f38ba8;
                font-weight: bold;
            }
            QPushButton#setEndBtn:hover {
                background-color: rgba(243, 139, 168, 0.2);
            }
            QPushButton#actionSave {
                background-color: #a6e3a1;
                color: #11111b;
                border: none;
                font-weight: bold;
                padding: 4px 12px;
            }
            QPushButton#actionSave:hover {
                background-color: #94e2d5;
            }
            QPushButton#actionPreview {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
                font-weight: bold;
                padding: 4px 10px;
            }
            QPushButton#actionPreview:hover {
                background-color: #b4befe;
            }
            """
        )

        self._start_ms: int = 0
        self._end_ms: int = 0
        self._duration_ms: int = 0
        self._current_pos_ms: int = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 4, 10, 4)
        main_layout.setSpacing(6)

        # ── Row 1: Markers & Time displays ──
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        # Header
        title = QLabel("✂ Video Kırp:")
        title.setStyleSheet("font-weight: bold; color: #fab387;")
        row1.addWidget(title)

        # In-point (Start)
        self._set_start_btn = QPushButton("[ Başlangıç Belirle (I)")
        self._set_start_btn.setObjectName("setStartBtn")
        self._set_start_btn.setToolTip("Mevcut oynatma konumunu başlangıç olarak ayarlar (Kısayol: I)")
        self._set_start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_start_btn.clicked.connect(self._set_start_to_current)
        row1.addWidget(self._set_start_btn)

        self._start_label = QLabel("00:00.0")
        self._start_label.setObjectName("badge")
        row1.addWidget(self._start_label)

        btn_start_dec = QPushButton("◀")
        btn_start_dec.setToolTip("Başlangıcı 0.5 sn geri al")
        btn_start_dec.setFixedWidth(24)
        btn_start_dec.clicked.connect(lambda: self.adjust_start(-500))
        row1.addWidget(btn_start_dec)

        btn_start_inc = QPushButton("▶")
        btn_start_inc.setToolTip("Başlangıcı 0.5 sn ileri al")
        btn_start_inc.setFixedWidth(24)
        btn_start_inc.clicked.connect(lambda: self.adjust_start(500))
        row1.addWidget(btn_start_inc)

        row1.addSpacing(12)

        # Out-point (End)
        self._set_end_btn = QPushButton("Bitiş Belirle ] (O)")
        self._set_end_btn.setObjectName("setEndBtn")
        self._set_end_btn.setToolTip("Mevcut oynatma konumunu bitiş olarak ayarlar (Kısayol: O)")
        self._set_end_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_end_btn.clicked.connect(self._set_end_to_current)
        row1.addWidget(self._set_end_btn)

        self._end_label = QLabel("00:00.0")
        self._end_label.setObjectName("badge")
        row1.addWidget(self._end_label)

        btn_end_dec = QPushButton("◀")
        btn_end_dec.setToolTip("Bitişi 0.5 sn geri al")
        btn_end_dec.setFixedWidth(24)
        btn_end_dec.clicked.connect(lambda: self.adjust_end(-500))
        row1.addWidget(btn_end_dec)

        btn_end_inc = QPushButton("▶")
        btn_end_inc.setToolTip("Bitişi 0.5 sn ileri al")
        btn_end_inc.setFixedWidth(24)
        btn_end_inc.clicked.connect(lambda: self.adjust_end(500))
        row1.addWidget(btn_end_inc)

        row1.addSpacing(12)

        # Selected Duration badge
        self._duration_badge = QLabel("Süre: 00:00.0")
        self._duration_badge.setObjectName("badge")
        self._duration_badge.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        row1.addWidget(self._duration_badge)

        row1.addStretch()

        # ── Row 2: Actions ──
        # Preview Selection
        preview_btn = QPushButton("▶ Seçimi Oynat")
        preview_btn.setObjectName("actionPreview")
        preview_btn.setToolTip("Yalnızca seçilen zaman aralığını oynatır")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.clicked.connect(self._on_preview_clicked)
        row1.addWidget(preview_btn)

        # Save Trim
        save_btn = QPushButton("💾 Kes ve Kaydet")
        save_btn.setObjectName("actionSave")
        save_btn.setToolTip("Seçilen video kesitini kayıpsız olarak yeni bir dosyaya kaydeder")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save_clicked)
        row1.addWidget(save_btn)

        # Close
        close_btn = QPushButton("✕")
        close_btn.setToolTip("Kırpma panelini kapat")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close_requested)
        row1.addWidget(close_btn)

        main_layout.addLayout(row1)

    @staticmethod
    def _format_time(ms: int) -> str:
        s, msec = divmod(max(0, ms), 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        tenths = msec // 100
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}.{tenths}"
        return f"{m:02d}:{s:02d}.{tenths}"

    def update_state(self, current_pos_ms: int, total_duration_ms: int) -> None:
        """Called as video plays to keep tracking position and total duration."""
        self._current_pos_ms = current_pos_ms
        if total_duration_ms != self._duration_ms and total_duration_ms > 0:
            self._duration_ms = total_duration_ms
            if self._end_ms == 0 or self._end_ms > total_duration_ms:
                self._end_ms = total_duration_ms
                self._update_display()

    def reset_for_video(self, duration_ms: int) -> None:
        """Reset markers for newly loaded video."""
        self._duration_ms = duration_ms
        self._start_ms = 0
        self._end_ms = duration_ms
        self._update_display()

    def _set_start_to_current(self) -> None:
        pos = min(self._current_pos_ms, max(0, self._end_ms - 200))
        self._start_ms = pos
        self._update_display()

    def _set_end_to_current(self) -> None:
        pos = max(self._current_pos_ms, self._start_ms + 200)
        if self._duration_ms > 0:
            pos = min(pos, self._duration_ms)
        self._end_ms = pos
        self._update_display()

    def adjust_start(self, delta_ms: int) -> None:
        new_start = max(0, min(self._start_ms + delta_ms, self._end_ms - 200))
        self._start_ms = new_start
        self._update_display()

    def adjust_end(self, delta_ms: int) -> None:
        max_dur = self._duration_ms if self._duration_ms > 0 else 999999999
        new_end = max(self._start_ms + 200, min(self._end_ms + delta_ms, max_dur))
        self._end_ms = new_end
        self._update_display()

    def _update_display(self) -> None:
        self._start_label.setText(self._format_time(self._start_ms))
        self._end_label.setText(self._format_time(self._end_ms))
        duration = max(0, self._end_ms - self._start_ms)
        self._duration_badge.setText(f"Süre: {self._format_time(duration)}")
        self.range_changed.emit(self._start_ms, self._end_ms)

    def _on_preview_clicked(self) -> None:
        self.preview_requested.emit(self._start_ms, self._end_ms)

    def _on_save_clicked(self) -> None:
        start_sec = self._start_ms / 1000.0
        end_sec = self._end_ms / 1000.0
        self.save_requested.emit(start_sec, end_sec)

    @property
    def start_ms(self) -> int:
        return self._start_ms

    @property
    def end_ms(self) -> int:
        return self._end_ms

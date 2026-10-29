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
    QComboBox,
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
    """Background worker thread that runs FFmpeg to trim and/or crop a video segment."""

    finished = Signal(bool, str, str)  # (success, message, output_path)

    def __init__(
        self,
        ffmpeg_exe: str,
        input_path: Path,
        output_path: Path,
        start_sec: float,
        end_sec: float,
        crop_box: Optional[tuple[int, int, int, int]] = None,  # (x, y, w, h)
        parent=None,
    ):
        super().__init__(parent)
        self._ffmpeg = ffmpeg_exe
        self._input = input_path
        self._output = output_path
        self._start = max(0.0, start_sec)
        self._end = max(self._start + 0.1, end_sec)
        self._crop_box = crop_box

    def run(self) -> None:
        start_str = f"{self._start:.3f}"
        end_str = f"{self._end:.3f}"

        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # ── Case A: Spatial Rectangular Crop requested ──
        if self._crop_box is not None:
            raw_x, raw_y, raw_w, raw_h = self._crop_box
            # Ensure dimensions are positive even numbers (required by libx264 YUV420p)
            w = max(2, int(raw_w) - (int(raw_w) % 2))
            h = max(2, int(raw_h) - (int(raw_h) % 2))
            x = max(0, int(raw_x) - (int(raw_x) % 2))
            y = max(0, int(raw_y) - (int(raw_y) % 2))

            cmd_crop = [
                self._ffmpeg,
                "-y",
                "-ss", start_str,
                "-to", end_str,
                "-i", str(self._input),
                "-vf", f"crop={w}:{h}:{x}:{y}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-avoid_negative_ts", "make_zero",
                str(self._output),
            ]

            try:
                res = subprocess.run(
                    cmd_crop,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    startupinfo=startupinfo,
                )
                if res.returncode == 0 and self._output.is_file() and self._output.stat().st_size > 1024:
                    self.finished.emit(True, "Video alanı ve süresi başarıyla kırpıldı.", str(self._output))
                    return
                else:
                    err_msg = res.stderr[-400:] if res.stderr else "Bilinmeyen FFmpeg kırpma hatası."
                    self.finished.emit(False, f"Video kırpma başarısız oldu:\n{err_msg}", "")
                    return
            except Exception as e:
                self.finished.emit(False, f"FFmpeg çalıştırma hatası: {e}", "")
                return

        # ── Case B: Pure Time Trim (Lossless stream copy) ──
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


class VideoTranscodeWorker(QThread):
    """Background worker thread that transcodes an incompatible or black-screen video
    into standard, universally compatible H.264 MP4 with AAC audio (YUV420p).
    """

    finished = Signal(bool, str, str)  # (success, message, output_path)

    def __init__(
        self,
        ffmpeg_exe: str,
        input_path: Path,
        output_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ffmpeg = ffmpeg_exe
        self._input = input_path
        self._output = output_path

    def run(self) -> None:
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Transcode video to standard H.264 High/Main profile with universal YUV420p pixel format
        # and standard AAC stereo audio, ensuring compatibility across all Windows systems and players.
        cmd = [
            self._ffmpeg,
            "-y",
            "-i",
            str(self._input),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "22",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(self._output),
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
            )

            if res.returncode == 0 and self._output.is_file() and self._output.stat().st_size > 1024:
                self.finished.emit(True, "Video başarıyla uyumlu MP4 formatına dönüştürüldü.", str(self._output))
            else:
                err_msg = res.stderr[-400:] if res.stderr else "Bilinmeyen FFmpeg dönüştürme hatası."
                self.finished.emit(False, f"Dönüştürme başarısız oldu:\n{err_msg}", "")
        except Exception as e:
            self.finished.emit(False, f"FFmpeg çalıştırma hatası: {e}", "")


class VideoEnhanceWorker(QThread):
    """Background worker thread that enhances video quality using FFmpeg:
    - hqdn3d (3D spatial/temporal denoise to remove compression grain)
    - unsharp (intelligent edge sharpening)
    - eq (dynamic range, color vibrancy, and shadow lift)
    """

    finished = Signal(bool, str, str)  # (success, message, output_path)

    def __init__(
        self,
        ffmpeg_exe: str,
        input_path: Path,
        output_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ffmpeg = ffmpeg_exe
        self._input = input_path
        self._output = output_path

    def run(self) -> None:
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        vf_filters = (
            "hqdn3d=1.5:1.5:4:4,"
            "unsharp=5:5:0.8:5:5:0.0,"
            "eq=contrast=1.12:brightness=0.03:saturation=1.16:gamma=1.10"
        )

        cmd = [
            self._ffmpeg,
            "-y",
            "-i",
            str(self._input),
            "-vf",
            vf_filters,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(self._output),
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
            )

            if res.returncode == 0 and self._output.is_file() and self._output.stat().st_size > 1024:
                self.finished.emit(True, "Video kalitesi başarıyla artırıldı ve netleştirildi.", str(self._output))
            else:
                err_msg = res.stderr[-400:] if res.stderr else "Bilinmeyen FFmpeg iyileştirme hatası."
                self.finished.emit(False, f"İyileştirme başarısız oldu:\n{err_msg}", "")
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
    """Control panel for selecting video trim start/end points and spatial crop rectangle."""

    preview_requested = Signal(int, int)  # (start_ms, end_ms)
    save_requested = Signal(float, float, object)  # (start_sec, end_sec, crop_box or None)
    close_requested = Signal()
    range_changed = Signal(int, int)  # (start_ms, end_ms)
    crop_area_toggled = Signal(bool)
    crop_ratio_changed = Signal(object)  # float or None

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
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #89b4fa;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
                border: 1px solid #45475a;
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
            QPushButton#cropAreaBtn[active="true"] {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
                font-weight: bold;
            }
            QPushButton#cropAreaBtn[active="true"]:hover {
                background-color: #b4befe;
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
        self._crop_area_active: bool = False
        self._current_crop_box: Optional[tuple[int, int, int, int]] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 4, 10, 4)
        main_layout.setSpacing(6)

        # ── Row 1: Time Range / Trimming ──
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

        # Close
        close_btn = QPushButton("✕")
        close_btn.setToolTip("Kırpma panelini kapat")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close_requested)
        row1.addWidget(close_btn)

        main_layout.addLayout(row1)

        # ── Row 2: Spatial Area Crop & Export Actions ──
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        # Area Crop Toggle Button
        self._crop_area_btn = QPushButton("📐 Alan Kırp (Genişlik × Yükseklik)")
        self._crop_area_btn.setObjectName("cropAreaBtn")
        self._crop_area_btn.setToolTip("Videoda ekrandan genişlik ve yükseklik seçerek kırpma yapmayı sağlar")
        self._crop_area_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._crop_area_btn.clicked.connect(self._toggle_crop_area)
        row2.addWidget(self._crop_area_btn)

        # Dimension display for crop box
        self._crop_size_label = QLabel("📐 0 × 0 px")
        self._crop_size_label.setObjectName("badge")
        self._crop_size_label.setStyleSheet("color: #89b4fa; font-weight: bold;")
        self._crop_size_label.setVisible(False)
        row2.addWidget(self._crop_size_label)

        # Aspect ratio selector
        self._crop_ratio_combo = QComboBox()
        self._crop_ratio_combo.addItem("Serbest", None)
        self._crop_ratio_combo.addItem("16:9 (Yatay)", 16.0 / 9.0)
        self._crop_ratio_combo.addItem("9:16 (Dikey / Reels)", 9.0 / 16.0)
        self._crop_ratio_combo.addItem("1:1 (Kare)", 1.0)
        self._crop_ratio_combo.addItem("4:3 (Standart)", 4.0 / 3.0)
        self._crop_ratio_combo.currentIndexChanged.connect(self._on_ratio_changed)
        self._crop_ratio_combo.setVisible(False)
        row2.addWidget(self._crop_ratio_combo)

        row2.addStretch()

        # Preview Selection
        preview_btn = QPushButton("▶ Seçimi Oynat")
        preview_btn.setObjectName("actionPreview")
        preview_btn.setToolTip("Yalnızca seçilen zaman aralığını oynatır")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.clicked.connect(self._on_preview_clicked)
        row2.addWidget(preview_btn)

        # Save Trim / Crop
        save_btn = QPushButton("💾 Kes ve Kaydet")
        save_btn.setObjectName("actionSave")
        save_btn.setToolTip("Seçilen video kesitini (ve varsa kırpılan alanı) yeni bir dosyaya kaydeder")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save_clicked)
        row2.addWidget(save_btn)

        main_layout.addLayout(row2)

    def _toggle_crop_area(self) -> None:
        self._crop_area_active = not self._crop_area_active
        self._crop_area_btn.setProperty("active", "true" if self._crop_area_active else "false")
        self._crop_area_btn.style().unpolish(self._crop_area_btn)
        self._crop_area_btn.style().polish(self._crop_area_btn)
        self._crop_size_label.setVisible(self._crop_area_active)
        self._crop_ratio_combo.setVisible(self._crop_area_active)
        self.crop_area_toggled.emit(self._crop_area_active)

    def _on_ratio_changed(self, index: int) -> None:
        ratio = self._crop_ratio_combo.currentData()
        self.crop_ratio_changed.emit(ratio)

    def set_crop_box(self, x: int, y: int, w: int, h: int) -> None:
        self._current_crop_box = (x, y, w, h)
        self._crop_size_label.setText(f"📐 {w} × {h} px")

    @property
    def is_crop_area_active(self) -> bool:
        return self._crop_area_active

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
        self._crop_area_active = False
        self._crop_area_btn.setProperty("active", "false")
        self._crop_area_btn.style().unpolish(self._crop_area_btn)
        self._crop_area_btn.style().polish(self._crop_area_btn)
        self._crop_size_label.setVisible(False)
        self._crop_ratio_combo.setVisible(False)
        self._current_crop_box = None
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
        crop_box = self._current_crop_box if self._crop_area_active else None
        self.save_requested.emit(start_sec, end_sec, crop_box)

    @property
    def start_ms(self) -> int:
        return self._start_ms

    @property
    def end_ms(self) -> int:
        return self._end_ms

    @property
    def start_ms(self) -> int:
        return self._start_ms

    @property
    def end_ms(self) -> int:
        return self._end_ms

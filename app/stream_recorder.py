"""High-performance background stream recorder for live network streams (RTSP, HLS, M3U, HTTP)."""

from datetime import datetime
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QProcess, QTimer, Signal
import imageio_ffmpeg


class StreamRecorder(QObject):
    """Records live network streams to MP4 or TS video files using bundled FFmpeg."""

    recording_started = Signal(str)  # output_path
    recording_tick = Signal(int, int)  # elapsed_seconds, bytes_written
    recording_finished = Signal(str, int, int)  # output_path, elapsed_seconds, bytes_written
    recording_error = Signal(str)  # error_message

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._process: Optional[QProcess] = None
        self._output_path: str = ""
        self._elapsed_seconds: int = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._stopping: bool = False

    @property
    def is_recording(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    @property
    def output_path(self) -> str:
        return self._output_path

    @property
    def elapsed_seconds(self) -> int:
        return self._elapsed_seconds

    def start_recording(self, stream_url: str, output_path: str) -> bool:
        """Start recording a live stream to output_path."""
        if self.is_recording:
            return False

        if not stream_url or not output_path:
            self.recording_error.emit("Geçersiz akış adresi veya kayıt dosyası yolu.")
            return False

        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as e:
            self.recording_error.emit(f"FFmpeg bulunamadı: {e}")
            return False

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path = str(out_path)
        self._elapsed_seconds = 0
        self._stopping = False

        args = ["-y"]

        # If RTSP, use TCP transport to eliminate UDP packet dropping
        if stream_url.lower().startswith("rtsp://"):
            args.extend(["-rtsp_transport", "tcp"])

        args.extend([
            "-i", stream_url,
            "-c", "copy",
        ])

        # If MP4 container, write faststart header
        if str(out_path).lower().endswith((".mp4", ".m4v")):
            args.extend(["-movflags", "+faststart"])

        args.append(str(out_path))

        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._on_process_error)

        self._process.start(ffmpeg_exe, args)
        if not self._process.waitForStarted(3000):
            self.recording_error.emit("Kayıt başlatılamadı (FFmpeg çalıştırılamadı).")
            self._process = None
            return False

        self._timer.start()
        self.recording_started.emit(self._output_path)
        return True

    def stop_recording(self) -> None:
        """Gracefully stop recording by sending 'q' to FFmpeg."""
        if not self.is_recording or self._stopping:
            return

        self._stopping = True
        self._timer.stop()

        if self._process:
            try:
                # Send 'q\n' to request graceful shutdown and moov atom finalization
                self._process.write(b"q\n")
                if not self._process.waitForFinished(3500):
                    self._process.terminate()
                    if not self._process.waitForFinished(2000):
                        self._process.kill()
            except Exception:
                if self._process:
                    self._process.kill()

    def _on_tick(self) -> None:
        self._elapsed_seconds += 1
        file_size = 0
        try:
            if os.path.exists(self._output_path):
                file_size = os.path.getsize(self._output_path)
        except Exception:
            pass
        self.recording_tick.emit(self._elapsed_seconds, file_size)

    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._timer.stop()
        final_size = 0
        file_exists = False
        try:
            if os.path.exists(self._output_path):
                final_size = os.path.getsize(self._output_path)
                file_exists = final_size > 0
        except Exception:
            pass

        output_path = self._output_path
        elapsed = self._elapsed_seconds
        self._process = None
        self._stopping = False

        if file_exists:
            self.recording_finished.emit(output_path, elapsed, final_size)
        else:
            self.recording_error.emit("Kayıt tamamlanamadı veya dosya oluşturulamadı.")

    def _on_process_error(self, error: QProcess.ProcessError) -> None:
        if self._stopping:
            return
        self._timer.stop()
        self.recording_error.emit(f"Kayıt işlemi sırasında hata oluştu: {error.name}")

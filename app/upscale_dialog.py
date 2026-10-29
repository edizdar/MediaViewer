"""Dialog and worker for smart HD photo upscaling (Lanczos-4 + edge sharpening)."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QFrame,
)


def perform_smart_hd_upscale(
    image: QImage,
    scale_factor: int = 2,
    sharpen: bool = True,
    denoise: bool = False,
) -> QImage:
    """Upscale QImage using Lanczos-4 interpolation, edge sharpening, and optional denoising."""
    w, h = image.width(), image.height()
    bpl = image.bytesPerLine()
    raw = image.bits()
    arr = np.frombuffer(raw, dtype=np.uint8).reshape((h, bpl))
    bgr = arr[:, : w * 4].reshape((h, w, 4))[:, :, :3]

    if denoise:
        bgr = cv2.bilateralFilter(bgr, 7, 40, 40)

    # 1. Lanczos-4 high-resolution sinc resampling
    new_w, new_h = w * scale_factor, h * scale_factor
    up = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # 2. Edge sharpening to retain crispness and micro-contrast
    if sharpen:
        sigma = 1.1 + (scale_factor * 0.1)
        blurred = cv2.GaussianBlur(up, (0, 0), sigma)
        up = cv2.addWeighted(up, 1.45, blurred, -0.45, 0)
        up = np.clip(up, 0, 255).astype(np.uint8)

    # Convert back to RGBA QImage
    rgba = cv2.cvtColor(up, cv2.COLOR_BGR2RGBA)
    return QImage(
        rgba.data, new_w, new_h, new_w * 4, QImage.Format.Format_RGBA8888
    ).copy()


class UpscaleWorker(QThread):
    finished = Signal(bool, str, object)  # success, message, QImage

    def __init__(
        self,
        image: QImage,
        scale_factor: int,
        sharpen: bool,
        denoise: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._image = image
        self._scale = scale_factor
        self._sharpen = sharpen
        self._denoise = denoise

    def run(self) -> None:
        try:
            res = perform_smart_hd_upscale(
                self._image,
                self._scale,
                self._sharpen,
                self._denoise,
            )
            self.finished.emit(True, "Tamamlandı", res)
        except Exception as e:
            self.finished.emit(False, str(e), None)


class UpscaleDialog(QDialog):
    """Dialog allowing user to choose 2x / 4x HD upscale with sharpening options."""

    upscaled_image_ready = Signal(str)  # emitted with path of saved upscaled image

    def __init__(self, current_image: QImage, current_path: Optional[Path], parent=None) -> None:
        super().__init__(parent)
        self._source_image = current_image
        self._source_path = current_path
        self._worker: Optional[UpscaleWorker] = None
        self._result_image: Optional[QImage] = None

        self.setWindowTitle("Resmi HD Yap & Büyüt (Smart Upscaling)")
        self.setFixedWidth(460)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QRadioButton {
                color: #cdd6f4;
                font-size: 13px;
                padding: 4px;
            }
            QRadioButton:hover {
                color: #89b4fa;
            }
            QCheckBox {
                color: #a6adc8;
                font-size: 12px;
                padding: 2px;
            }
            QCheckBox:hover {
                color: #cdd6f4;
            }
            QPushButton#accentBtn {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 9px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#accentBtn:hover {
                background-color: #106ebe;
            }
            QPushButton#cancelBtn {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton#cancelBtn:hover {
                background-color: #45475a;
            }
            QProgressBar {
                background-color: #313244;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 4px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(14)

        # Title & Description
        title = QLabel("🖼️  Resmi HD / 4K Çözünürlüğe Yükselt")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        layout.addWidget(title)

        desc = QLabel(
            "Lanczos-4 algoritması ve kenar keskinleştirme filtreleri kullanarak "
            "fotoğrafın piksellerini bozmadan detaylı ve net şekilde büyütür."
        )
        desc.setStyleSheet("color: #a6adc8; font-size: 12px; line-height: 1.4;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Info Box (Current Size)
        w, h = self._source_image.width(), self._source_image.height()
        mp = (w * h) / 1_000_000.0
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background-color: #181825; border: 1px solid #313244; border-radius: 6px; padding: 10px;"
        )
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 6, 8, 6)
        
        cur_lbl = QLabel(f"<b>Mevcut Boyut:</b> {w} × {h} px  <span style='color: #89b4fa;'>({mp:.2f} Megapiksel)</span>")
        info_layout.addWidget(cur_lbl)
        layout.addWidget(info_frame)

        # Scale options
        scale_title = QLabel("<b>Büyütme Oranı:</b>")
        layout.addWidget(scale_title)

        self._btn_group = QButtonGroup(self)
        self._radio_2x = QRadioButton(f"<b>2x HD Büyütme</b>  →  {w * 2} × {h * 2} px  (Tavsiye Edilen)")
        self._radio_2x.setChecked(True)
        self._btn_group.addButton(self._radio_2x, 2)
        layout.addWidget(self._radio_2x)

        self._radio_4x = QRadioButton(f"<b>4x Ultra HD Büyütme</b>  →  {w * 4} × {h * 4} px  (Büyük Ekranlar/Baskı)")
        self._btn_group.addButton(self._radio_4x, 4)
        layout.addWidget(self._radio_4x)

        # Options checkboxes
        opt_title = QLabel("<b>İyileştirme Seçenekleri:</b>")
        layout.addWidget(opt_title)

        self._chk_sharpen = QCheckBox("Akıllı Kenar Keskinleştirme (Unsharp Mask) Uygula")
        self._chk_sharpen.setChecked(True)
        layout.addWidget(self._chk_sharpen)

        self._chk_denoise = QCheckBox("Parazit ve Kumlanmayı Gider (Denoise)")
        self._chk_denoise.setChecked(True)
        layout.addWidget(self._chk_denoise)

        # Progress bar (indeterminate)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Buttons
        layout.addSpacing(6)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._start_btn = QPushButton("💾  HD Olarak Kaydet...")
        self._start_btn.setObjectName("accentBtn")
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self._start_upscaling)
        btn_layout.addWidget(self._start_btn)

        layout.addLayout(btn_layout)

    def _start_upscaling(self) -> None:
        scale = 2 if self._radio_2x.isChecked() else 4
        sharpen = self._chk_sharpen.isChecked()
        denoise = self._chk_denoise.isChecked()

        # Ask save file path first
        default_name = "resim_HD.png"
        default_dir = ""
        if self._source_path:
            default_name = f"{self._source_path.stem}_{scale}x_HD{self._source_path.suffix}"
            default_dir = str(self._source_path.parent / default_name)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "HD Fotoğrafı Kaydet",
            default_dir,
            "PNG Dosyası (*.png);;JPEG Dosyası (*.jpg *.jpeg);;Tüm Dosyalar (*)",
        )
        if not save_path:
            return

        self._save_target_path = Path(save_path)
        self._start_btn.setEnabled(False)
        self._start_btn.setText("İşleniyor...")
        self._progress.setVisible(True)

        self._worker = UpscaleWorker(
            self._source_image,
            scale,
            sharpen,
            denoise,
            parent=self,
        )
        self._worker.finished.connect(self._on_upscale_finished)
        self._worker.start()

    def _on_upscale_finished(self, success: bool, msg: str, result_image: Optional[QImage]) -> None:
        self._progress.setVisible(False)
        self._start_btn.setEnabled(True)
        self._start_btn.setText("💾  HD Olarak Kaydet...")

        if success and result_image is not None:
            # Save image
            saved = result_image.save(str(self._save_target_path))
            if saved:
                reply = QMessageBox.question(
                    self,
                    "HD İyileştirme Tamamlandı",
                    f"Fotoğraf başarıyla HD olarak büyütüldü ve kaydedildi:\n{self._save_target_path.name}\n\n"
                    "Yeni HD fotoğrafı şimdi görüntüleyicide açmak ister misiniz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                self.accept()
                if reply == QMessageBox.StandardButton.Yes:
                    self.upscaled_image_ready.emit(str(self._save_target_path))
            else:
                QMessageBox.critical(self, "Hata", "Dosya diske kaydedilemedi.")
        else:
            QMessageBox.critical(self, "Hata", f"HD büyütme işlemi başarısız oldu:\n{msg}")

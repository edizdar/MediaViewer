"""Help and User Guide dialog with FAQ and feature documentation."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTextBrowser,
    QPushButton,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
)
from app import __version__, APP_NAME
from app.updater import UpdateCheckWorker, UpdateDialog, UpdateInfo
from app.localization import loc, get_localization


class HelpDialog(QDialog):
    """Modern User Guide, Shortcuts and FAQ Dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — {loc('help_title')}")
        self.resize(760, 560)
        self.setMinimumSize(600, 420)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                border-radius: 8px;
                background-color: #181825;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #181825;
                color: #a6adc8;
                border: 1px solid #313244;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #313244;
                color: #89b4fa;
                font-weight: bold;
                border-color: #89b4fa;
            }
            QTabBar::tab:hover:!selected {
                background-color: #262738;
                color: #cdd6f4;
            }
            QTextBrowser {
                background-color: #181825;
                color: #cdd6f4;
                border: none;
                padding: 12px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }
            QPushButton#closeBtn {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 22px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#closeBtn:hover {
                background-color: #106ebe;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(12)

        # Header with Logo & Title
        header = QHBoxLayout()
        header.setSpacing(10)
        title_icon = QLabel("📚")
        title_icon.setStyleSheet("font-size: 24px;")
        header.addWidget(title_icon)

        title_label = QLabel(f"<b>{APP_NAME} v{__version__}</b> — {loc('help_title')}")
        title_label.setStyleSheet("font-size: 16px; color: #89b4fa;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget(self)

        tab_shortcuts = QTextBrowser()
        tab_shortcuts.setOpenExternalLinks(True)
        tab_shortcuts.setHtml(self._get_shortcuts_html())
        tabs.addTab(tab_shortcuts, loc("tab_shortcuts"))

        tab_features = QTextBrowser()
        tab_features.setOpenExternalLinks(True)
        tab_features.setHtml(self._get_features_html())
        tabs.addTab(tab_features, loc("tab_features"))

        tab_faq = QTextBrowser()
        tab_faq.setOpenExternalLinks(True)
        tab_faq.setHtml(self._get_faq_html())
        tabs.addTab(tab_faq, loc("tab_faq"))

        tab_about = QTextBrowser()
        tab_about.setOpenExternalLinks(True)
        tab_about.setHtml(self._get_about_html())
        tabs.addTab(tab_about, loc("tab_about"))

        layout.addWidget(tabs)

        # Bottom Bar with Update Check & Close Button
        bottom_bar = QHBoxLayout()

        self._check_update_btn = QPushButton(loc("check_updates"))
        self._check_update_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #89b4fa;
                border-color: #89b4fa;
            }
            """
        )
        self._check_update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._check_update_btn.clicked.connect(self._manual_check_update)
        bottom_bar.addWidget(self._check_update_btn)

        bottom_bar.addStretch()
        close_btn = QPushButton(loc("close_btn"))
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)
        layout.addLayout(bottom_bar)

    def _manual_check_update(self) -> None:
        self._check_update_btn.setEnabled(False)
        self._check_update_btn.setText(loc("checking_updates"))

        self._update_worker = UpdateCheckWorker(self)
        self._update_worker.finished_check.connect(self._on_manual_check_finished)
        self._update_worker.start()

    def _on_manual_check_finished(
        self, success: bool, info: UpdateInfo, msg: str
    ) -> None:
        self._check_update_btn.setEnabled(True)
        self._check_update_btn.setText(loc("check_updates"))

        if success and info:
            if info.is_newer:
                dlg = UpdateDialog(info, self)
                dlg.exec()
            else:
                QMessageBox.information(
                    self,
                    loc("check_updates"),
                    loc("update_already_latest").format(__version__),
                )
        else:
            QMessageBox.warning(
                self,
                loc("check_updates"),
                loc("update_failed"),
            )

    def _get_shortcuts_html(self) -> str:
        css = """
        <style>
            body { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            h3 { color: #89b4fa; border-bottom: 1px solid #313244; padding-bottom: 4px; margin-top: 14px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
            th { text-align: left; color: #a6adc8; font-size: 12px; padding: 6px 8px; border-bottom: 1px solid #45475a; }
            td { padding: 6px 8px; border-bottom: 1px solid #313244; font-size: 13px; }
            kbd { background-color: #313244; border: 1px solid #45475a; border-radius: 4px; padding: 2px 7px; color: #f9e2af; font-family: Consolas, monospace; font-size: 12px; font-weight: bold; }
        </style>
        """
        if get_localization().current_language == "en":
            return f"""
            {css}
            <h3>🖼️ Photo Viewing & Editing</h3>
            <table>
                <tr><th>Shortcut</th><th>Description</th></tr>
                <tr><td><kbd>Mouse Wheel</kbd></td><td>Center-based zoom in / zoom out</td></tr>
                <tr><td><kbd>Left Click Drag</kbd></td><td>Pan zoomed image</td></tr>
                <tr><td><kbd>F</kbd></td><td>Fit image to window</td></tr>
                <tr><td><kbd>0</kbd></td><td>Original 1:1 pixel size (100% Zoom)</td></tr>
                <tr><td><kbd>R</kbd> / <kbd>L</kbd></td><td>Rotate 90° Clockwise / Counter-Clockwise</td></tr>
                <tr><td><kbd>C</kbd></td><td>Toggle crop mode (interactive aspect ratios)</td></tr>
                <tr><td><kbd>Ctrl + J</kbd></td><td>Color adjustments panel (Brightness, Contrast, Gamma, Sharpness)</td></tr>
                <tr><td><kbd>Ctrl + Shift + U</kbd></td><td><b>Smart HD Upscale (2x / 4x Lanczos-4)</b></td></tr>
                <tr><td><kbd>Delete</kbd></td><td>Send current file to Recycle Bin with confirmation</td></tr>
            </table>

            <h3>🎬 Video Playback & Editing</h3>
            <table>
                <tr><th>Shortcut</th><th>Description</th></tr>
                <tr><td><kbd>Space</kbd></td><td>Play / Pause</td></tr>
                <tr><td><kbd>Ctrl + R</kbd></td><td><b>🔴 Record / Stop Live Network Stream</b> (RTSP / M3U)</td></tr>
                <tr><td><kbd>E</kbd></td><td><b>✨ Live Smart Video Enhancement (Vibrant & Sharp Mode)</b></td></tr>
                <tr><td><kbd>S</kbd></td><td><b>📸 Snapshot full-res frame from video</b></td></tr>
                <tr><td><kbd>C</kbd></td><td>Video trim & crop panel</td></tr>
                <tr><td><kbd>←</kbd> / <kbd>→</kbd></td><td>Seek 5 seconds backward / forward</td></tr>
                <tr><td><kbd>↑</kbd> / <kbd>↓</kbd></td><td>Volume Up / Down</td></tr>
                <tr><td><kbd>M</kbd></td><td>Mute / Unmute audio</td></tr>
                <tr><td><kbd>1</kbd> .. <kbd>4</kbd></td><td>Playback Speed: 0.5x, 1.0x, 1.5x, 2.0x</td></tr>
            </table>

            <h3>🌐 General, Streams & Navigation</h3>
            <table>
                <tr><th>Shortcut</th><th>Description</th></tr>
                <tr><td><kbd>Alt + M</kbd> / <kbd>F10</kbd></td><td><b>☰ Main Application Menu</b></td></tr>
                <tr><td><kbd>Ctrl + O</kbd></td><td>Open File dialog</td></tr>
                <tr><td><kbd>Ctrl + U</kbd></td><td><b>📺 Open Network Stream (RTSP / HLS / M3U)</b></td></tr>
                <tr><td><kbd>Ctrl + L</kbd></td><td>Playlist sidebar toggle</td></tr>
                <tr><td><kbd>Alt + ←</kbd> / <kbd>Alt + →</kbd></td><td>Previous / Next media file in directory</td></tr>
                <tr><td><kbd>F11</kbd> / <kbd>Double Click</kbd></td><td><b>Smart Fullscreen Mode</b></td></tr>
                <tr><td><kbd>F1</kbd></td><td>Open this User Guide & Help dialog</td></tr>
            </table>
            """

        return f"""
        {css}
        <h3>🖼️ Fotoğraf Görüntüleme & Düzenleme</h3>
        <table>
            <tr><th>Kısayol</th><th>Açıklama</th></tr>
            <tr><td><kbd>Fare Tekerleği</kbd></td><td>Merkez odaklı yakınlaştırma ve uzaklaştırma (Zoom)</td></tr>
            <tr><td><kbd>Fare Sol Tuş</kbd></td><td>Yakınlaştırılmış görseli kaydırma (Pan)</td></tr>
            <tr><td><kbd>F</kbd></td><td>Görseli ekrana sığdır (Fit to Window)</td></tr>
            <tr><td><kbd>0</kbd></td><td>Orijinal piksel boyutuna getir (%100 Zoom)</td></tr>
            <tr><td><kbd>R</kbd> / <kbd>L</kbd></td><td>Fotoğrafı 90° Sağa / Sola Döndür</td></tr>
            <tr><td><kbd>C</kbd></td><td>Kırpma modunu aç / kapat (Özel en-boy oranlarıyla kırpma)</td></tr>
            <tr><td><kbd>Ctrl + J</kbd></td><td>Renk & Netlik Ayarları Panelini Aç/Kapat (Parlaklık, Kontrast, Gamma, Netlik)</td></tr>
            <tr><td><kbd>Ctrl + Shift + U</kbd></td><td><b>Resmi HD Yap ve Büyüt (2x / 4x Smart Upscale)</b></td></tr>
            <tr><td><kbd>Delete</kbd></td><td>Mevcut dosyayı onay alarak Geri Dönüşüm Kutusuna gönder</td></tr>
        </table>

        <h3>🎬 Video Oynatma & Düzenleme</h3>
        <table>
            <tr><th>Kısayol</th><th>Açıklama</th></tr>
            <tr><td><kbd>Space</kbd></td><td>Oynat / Duraklat</td></tr>
            <tr><td><kbd>Ctrl + R</kbd></td><td><b>🔴 Canlı Yayını Kaydet / Durdur</b> (RTSP / M3U)</td></tr>
            <tr><td><kbd>E</kbd></td><td><b>✨ Akıllı Canlı Video İyileştirme (Canlı & Net Modu)</b></td></tr>
            <tr><td><kbd>S</kbd></td><td><b>📸 Videodan Orijinal Çözünürlükte Kare Yakala (Snapshot)</b></td></tr>
            <tr><td><kbd>C</kbd></td><td>Video Kırpma & Kesme Panelini Aç / Kapat</td></tr>
            <tr><td><kbd>←</kbd> / <kbd>→</kbd></td><td>5 Saniye Geri / İleri Sar</td></tr>
            <tr><td><kbd>↑</kbd> / <kbd>↓</kbd></td><td>Ses Seviyesini Artır / Azalt</td></tr>
            <tr><td><kbd>M</kbd></td><td>Sesi Kapat / Aç (Mute)</td></tr>
            <tr><td><kbd>1</kbd> .. <kbd>4</kbd></td><td>Oynatma Hızı: 0.5x, 1.0x, 1.5x, 2.0x</td></tr>
        </table>

        <h3>🌐 Genel, Akışlar & Gezinme</h3>
        <table>
            <tr><th>Kısayol</th><th>Açıklama</th></tr>
            <tr><td><kbd>Alt + M</kbd> / <kbd>F10</kbd></td><td><b>☰ Ana Uygulama Menüsü</b></td></tr>
            <tr><td><kbd>Ctrl + O</kbd></td><td>Dosya Aç iletişim kutusu</td></tr>
            <tr><td><kbd>Ctrl + U</kbd></td><td><b>📺 Ağ Akışı Aç (RTSP / HLS / M3U)</b></td></tr>
            <tr><td><kbd>Ctrl + L</kbd></td><td>Oynatma Listesi / Galeri Kenar Çubuğu Aç/Kapat</td></tr>
            <tr><td><kbd>Alt + ←</kbd> / <kbd>Alt + →</kbd></td><td>Klasördeki Önceki / Sonraki Medya Dosyası</td></tr>
            <tr><td><kbd>F11</kbd> / <kbd>Çift Tık</kbd></td><td><b>Akıllı Tam Ekran Modu</b> (Sıfır dikkat dağıtıcı)</td></tr>
            <tr><td><kbd>F1</kbd></td><td>Bu Kullanım Kılavuzu & Yardım Penceresini Aç</td></tr>
        </table>
        """

    def _get_features_html(self) -> str:
        if get_localization().current_language == "en":
            return """
            <style>
                body { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
                .card { background-color: #262738; border-left: 4px solid #89b4fa; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; }
                .card-title { font-weight: bold; color: #89b4fa; font-size: 14px; margin-bottom: 4px; }
                .card-body { color: #cdd6f4; font-size: 12.5px; line-height: 1.5; }
            </style>

            <div class="card">
                <div class="card-title">🛡️ 100% Embedded Codec Engine (Zero External Dependencies)</div>
                <div class="card-body">
                    All major video and image formats (HEVC/H.265, AV1, VP9, H.264, MPEG-4, ProRes, WebP, etc.) are decoded with built-in FFmpeg 7.1 and avcodec. No codec packs or Microsoft Store extensions required.
                </div>
            </div>

            <div class="card">
                <div class="card-title">✨ Live Smart Video Enhancement (E key)</div>
                <div class="card-body">
                    Pressing <code>E</code> during video playback activates a real-time 4-stage processing engine: clears haze/fog, lifts dark shadows without blowing out highlights, and enriches colors for cinematic clarity.
                </div>
            </div>

            <div class="card">
                <div class="card-title">🔍 Smart Photo Sharpness & Clarity</div>
                <div class="card-body">
                    The <code>Ctrl+J</code> panel features a <b>Sharpness</b> slider and <b>Smart Enhance</b> button to rescue soft or slightly out-of-focus photos using adaptive edge micro-contrast.
                </div>
            </div>

            <div class="card">
                <div class="card-title">🖼️ 2x / 4x Smart HD Upscale (Lanczos-4)</div>
                <div class="card-body">
                    Upscale small or older images to 2x (HD) or 4x (Ultra HD) resolution without pixelation using intelligent edge-preserving Lanczos-4 filters.
                </div>
            </div>

            <div class="card">
                <div class="card-title">📸 One-Click Video Snapshot (S key)</div>
                <div class="card-body">
                    Instantly save full-resolution lossless frames from any playing or paused video (1080p, 4K) directly to disk or clipboard.
                </div>
            </div>

            <div class="card">
                <div class="card-title">📺 Live Network Streams & IPTV (Ctrl+U)</div>
                <div class="card-body">
                    Watch RTSP security cameras, HLS (.m3u8), and M3U IPTV channels directly. Right-click any M3U file in Windows Explorer and choose "Open With &rarr; Media Viewer" to automatically import all channels into the filmstrip panel. Supports Low-Latency mode for IP cams and Balanced mode for IPTV.
                </div>
            </div>

            <div class="card">
                <div class="card-title">🔴 Live Stream Recording (Ctrl+R)</div>
                <div class="card-body">
                    Record live RTSP cameras or M3U streams directly to your disk as lossless MP4, TS, or MKV video files with zero CPU overhead using direct bitstream copy. Includes live duration counter and instant playback upon stopping.
                </div>
            </div>

            <div class="card">
                <div class="card-title">🎨 Operating Modes: Simple vs. Advanced Editing</div>
                <div class="card-body">
                    Switch between <b>Simple Mode</b> (pure, minimalist distraction-free viewing) and <b>Advanced Mode</b> (full photo/video color grading, trimming, cropping, upscaling, and stream tools) via the top-left menu.
                </div>
            </div>
            """

        return """
        <style>
            body { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            .card { background-color: #262738; border-left: 4px solid #89b4fa; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; }
            .card-title { font-weight: bold; color: #89b4fa; font-size: 14px; margin-bottom: 4px; }
            .card-body { color: #cdd6f4; font-size: 12.5px; line-height: 1.5; }
        </style>

        <div class="card">
            <div class="card-title">🛡️ %100 Dahili Kodek Sistemi (Sıfır Dış Bağımlılık)</div>
            <div class="card-body">
                HEVC / H.265, AV1, VP9, H.264, MPEG-4, ProRes vb. tüm video formatları uygulamanın içerisine gömülü FFmpeg 7.1 ve avcodec kütüphaneleriyle çözülür. K-Lite veya Microsoft Store'dan harici kodek satın alıp kurmanıza kesinlikle gerek yoktur.
            </div>
        </div>

        <div class="card">
            <div class="card-title">✨ Canlı Akıllı Video İyileştirme (E Tuşu)</div>
            <div class="card-body">
                Oynatma sırasında <code>E</code> tuşuna bastığınızda, 4 aşamalı profesyonel motor devreye girer: Sis & pus temizlenir, karanlık sahnelerdeki gölgeler patlatılmadan açılır ve solgun renkler canlandırılarak sinematik netlik sağlanır.
            </div>
        </div>

        <div class="card">
            <div class="card-title">🔍 Fotoğraflarda Akıllı Netleştirme & Keskinlik</div>
            <div class="card-body">
                <code>Ctrl+J</code> panelindeki <b>Netlik (Keskinlik)</b> kaydırıcısı ve <b>Akıllı Ayarla</b> butonu, odak kaçmış veya yumuşak fotoğrafları kenar mikro-kontrastıyla jilet gibi keskinleştirir.
            </div>
        </div>

        <div class="card">
            <div class="card-title">🖼️ 2x / 4x Akıllı HD Büyütme (Lanczos-4 Smart Upscale)</div>
            <div class="card-body">
                Küçük veya eski fotoğraflarınızı pikselleri bozmadan, akıllı kenar korumalı Lanczos-4 algoritmasıyla 2 katı (HD) veya 4 katı (Ultra HD) çözünürlüğe büyüterek kaydedebilirsiniz.
            </div>
        </div>

        <div class="card">
            <div class="card-title">📸 Videodan Tek Tuşla Kare Yakalama (S Tuşu)</div>
            <div class="card-body">
                Videoyu izlerken tam o anki kareyi orijinal çözünürlüğünde (Full HD / 4K) tek tıkla kayıpsız fotoğraf olarak kaydedebilir veya panoya kopyalayabilirsiniz.
            </div>
        </div>

        <div class="card">
            <div class="card-title">✂️ Akıllı Video ve Fotoğraf Kırpma (C Tuşu)</div>
            <div class="card-body">
                Videolarda hem süre aralığını (Başlangıç/Bitiş) hem de kadrajı (Genişlik/Yükseklik) belirleyerek ister kayıpsız ister optimize MP4 olarak tek tıkla dışa aktarabilirsiniz.
            </div>
        </div>

        <div class="card">
            <div class="card-title">📺 Canlı Ağ Akışları & IPTV Oynatma (Ctrl+U)</div>
            <div class="card-body">
                RTSP IP kameralarını, HLS (.m3u8) canlı yayınlarını ve M3U IPTV listelerini doğrudan oynatın. Windows'ta herhangi bir .m3u dosyasına sağ tıklayıp <b>"Birlikte Aç &rarr; Media Viewer"</b> seçtiğinizde tüm kanallar otomatik olarak sol oynatma listesine yüklenir ve ilk kanal başlar. IP kameralar için <b>⚡ Düşük Gecikme</b>, IPTV için <b>⚖️ Dengeli Tampon</b> modları mevcuttur.
            </div>
        </div>

        <div class="card">
            <div class="card-title">🔴 Canlı Yayını Video Olarak Kaydetme (Ctrl+R)</div>
            <div class="card-body">
                İzlediğiniz canlı RTSP kamerasını veya IPTV kanalını tek tıkla doğrudan MP4, TS veya MKV formatında video dosyası olarak bilgisayarınıza kaydedebilirsiniz. Doğrudan kopyalama modunu kullandığı için bilgisayarı yormaz ve yayın kalitesini %100 kayıpsız korur.
            </div>
        </div>

        <div class="card">
            <div class="card-title">🎨 Çalışma Modları: Basit İzleme vs. Gelişmiş Düzenleme</div>
            <div class="card-body">
                Sol üstteki <b>☰ Menü &gt; Çalışma Modu</b> altından tek tıkla <b>👁️ Basit Mod</b> (dikkat dağıtmayan, sade ve hızlı medya izleme) veya <b>🛠️ Gelişmiş Mod</b> (tüm renk ayarları, kırpma, kesme, HD büyütme ve akış araçları) arasında geçiş yapabilirsiniz.
            </div>
        </div>

        <div class="card">
            <div class="card-title">📋 M3U Standart Dışa Aktarma (#EXTM3U)</div>
            <div class="card-body">
                Oynatma listesi panelindeki <b>💾 Kaydet</b> butonu ile oluşturduğunuz medya ve kanal listelerini VLC ve diğer tüm oynatıcılarla uyumlu standart <code>#EXTM3U</code> formatında kaydedebilirsiniz.
            </div>
        </div>
        """

    def _get_faq_html(self) -> str:
        if get_localization().current_language == "en":
            return """
            <style>
                body { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
                .q { color: #fbbf24; font-weight: bold; font-size: 13.5px; margin-top: 14px; margin-bottom: 4px; }
                .a { color: #cdd6f4; font-size: 13px; line-height: 1.5; background-color: #262738; padding: 8px 12px; border-radius: 6px; }
            </style>

            <div class="q">❓ Question: Will HEVC/H.265 videos show a black screen on other computers?</div>
            <div class="a">
                <b>No.</b> Media Viewer features an embedded FFmpeg engine with CPU software decoder fallbacks. It plays smoothly on any system without extra codec packs.
            </div>

            <div class="q">❓ Question: Does "Smart Enhance" alter or damage the original file?</div>
            <div class="a">
                <b>Never.</b> Real-time enhancement is applied purely to the rendering pipeline on screen. The original file remains untouched.
            </div>

            <div class="q">❓ Question: Which formats are supported?</div>
            <div class="a">
                <b>Images:</b> JPG, JPEG, PNG, GIF, BMP, WEBP, TIFF, ICO, SVG.<br>
                <b>Videos:</b> MP4, MKV, MOV, AVI, WEBM, FLV, TS, M4V, WMV.<br>
                <b>Streams:</b> RTSP, HLS (.m3u8), M3U, HTTP Live, RTMP.
            </div>

            <div class="q">❓ Question: How do I record live RTSP or M3U streams?</div>
            <div class="a">
                When any live network stream is playing, simply click the <b>🔴 Record Stream</b> button on the player controls or press <b>Ctrl+R</b>. You will be prompted for a destination path (MP4, TS, or MKV). When finished, click <b>⏹️ Stop Recording</b> to instantly save and play the file.
            </div>

            <div class="q">❓ Question: What is the difference between Simple Mode and Advanced Mode?</div>
            <div class="a">
                <b>Simple Mode</b> hides the editing buttons and color adjustment panel, offering a pure, fast, lightweight viewing experience. <b>Advanced Mode</b> enables trimming, cropping, color corrections, upscaling, and stream recording. You can switch anytime via the top-left menu (<code>Alt+M</code>).
            </div>
            """

        return """
        <style>
            body { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            .q { color: #fbbf24; font-weight: bold; font-size: 13.5px; margin-top: 14px; margin-bottom: 4px; }
            .a { color: #cdd6f4; font-size: 13px; line-height: 1.5; background-color: #262738; padding: 8px 12px; border-radius: 6px; }
        </style>

        <div class="q">❓ Soru: Başka bilgisayarlarda HEVC/H.265 videolarda siyah ekran olur mu?</div>
        <div class="a">
            <b>Hayır, olmaz.</b> Media Viewer dahili FFmpeg motorunu ve CPU yazılım çözücüsünü doğrudan uygulama içine gömmüştür. Bilgisayarda kodek paketi olmasa dahi gömülü çözücümüz videoyu sorunsuz açar.
        </div>

        <div class="q">❓ Soru: "Akıllı İyileştirme" orijinal video veya fotoğraf dosyama zarar verir mi?</div>
        <div class="a">
            <b>Kesinlikle hayır.</b> Canlı izleme sırasında yapılan iyileştirmeler tamamen ekrandaki gerçek zamanlı görüntü katmanına uygulanır, orijinal dosyanızı asla değiştirmez.
        </div>

        <div class="q">❓ Soru: Hangi dosya formatları destekleniyor?</div>
        <div class="a">
            <b>Fotoğraflar:</b> JPG, JPEG, PNG, GIF, BMP, WEBP, TIFF, ICO, SVG.<br>
            <b>Videolar:</b> MP4, MKV, MOV, AVI, WEBM, FLV, TS, M4V, WMV.<br>
            <b>Canlı Yayınlar & Akışlar:</b> RTSP, HLS (.m3u8), M3U, HTTP Canlı, RTMP.
        </div>

        <div class="q">❓ Soru: Canlı RTSP veya M3U yayınlarını nasıl kaydederim?</div>
        <div class="a">
            Herhangi bir canlı ağ akışı oynatılırken alt kontrol çubuğunda beliren <b>🔴 Yayını Kaydet</b> butonuna basabilir veya <b>Ctrl+R</b> kısayolunu kullanabilirsiniz. Kaydetmek istediğiniz konumu seçtikten sonra canlı kayıt başlar; durdurmak için <b>⏹️ Kaydı Durdur</b> butonuna basmanız yeterlidir. Dosya doğrudan MP4, TS veya MKV olarak kaydedilir.
        </div>

        <div class="q">❓ Soru: "Basit Mod" ile "Gelişmiş Mod" arasındaki fark nedir?</div>
        <div class="a">
            <b>Basit Mod</b> düzenleme, kırpma ve renk araçlarını gizleyerek uygulamayı yalnızca hızlı ve sade bir izleyici haline getirir. <b>Gelişmiş Mod</b> ise kırpma, renk ayarları, netleştirme, HD büyütme ve yayın kaydı gibi tüm profesyonel araçları aktif eder. Sol üstteki <code>☰ Menü</code>den (<code>Alt+M</code>) dilediğiniz zaman değiştirebilirsiniz.
        </div>
        """

    def _get_about_html(self) -> str:
        desc_tr = "Windows 10 ve 11 için geliştirilmiş, hafif, donanım hızlandırmalı ve %100 dahili kodek içeren modern fotoğraf ve video görüntüleyici."
        desc_en = "Modern, lightweight, hardware-accelerated photo and video viewer with 100% embedded codecs for Windows 10 & 11."
        desc = desc_en if get_localization().current_language == "en" else desc_tr
        ver_label = f"Version {__version__} — Portable Edition" if get_localization().current_language == "en" else f"Sürüm {__version__} — Taşınabilir (Portable) Sürüm"

        return f"""
        <style>
            body {{ color: #cdd6f4; font-family: 'Segoe UI', sans-serif; text-align: center; padding-top: 20px; }}
            h2 {{ color: #89b4fa; margin-bottom: 2px; }}
            .ver {{ color: #a6adc8; font-size: 13px; margin-bottom: 16px; }}
            .desc {{ color: #cdd6f4; font-size: 13.5px; line-height: 1.6; max-width: 500px; margin: 0 auto 20px auto; }}
            .link {{ color: #89b4fa; text-decoration: none; font-weight: bold; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #6c7086; }}
        </style>

        <h2>Media Viewer</h2>
        <div class="ver">{ver_label}</div>
        <div class="desc">
            {desc}
        </div>
        <p>
            Developer: <b>Erol Dizdar</b><br>
            Web: <a class="link" href="https://www.eroldizdar.tr">https://www.eroldizdar.tr</a><br>
            Repository: <a class="link" href="https://github.com/edizdar/MediaViewer">github.com/edizdar/MediaViewer</a>
        </p>
        <div class="footer">
            Python 3.10 &bull; PySide6 (Qt 6.8) &bull; FFmpeg 7.1 &bull; OpenCV &bull; Pillow
        </div>
        """

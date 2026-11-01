"""Dialog for opening and managing network streams (RTSP, HLS, M3U, HTTP)."""

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QMessageBox,
)

from app.i18n import loc

DEFAULT_SAMPLE_STREAMS = [
    {
        "name": "Big Buck Bunny (HLS Canlı/VOD)",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "buffer_mode": "balanced",
    },
    {
        "name": "Sintel (HLS Multi-Quality)",
        "url": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",
        "buffer_mode": "balanced",
    },
    {
        "name": "Tears of Steel (HLS Demo)",
        "url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "buffer_mode": "balanced",
    },
]


class NetworkStreamDialog(QDialog):
    """Dialog allowing users to enter a network stream URL or pick from saved streams."""

    stream_selected = Signal(str, str, str)  # url, name, buffer_mode

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ağ Akışı Aç (RTSP / HLS / M3U)")
        self.resize(520, 420)
        self.setModal(True)

        self._streams_file = Path.home() / ".mediaviewer" / "saved_streams.json"
        self._saved_streams: list[dict] = []
        self._load_saved_streams()

        self._init_ui()

    def _load_saved_streams(self) -> None:
        if self._streams_file.exists():
            try:
                with open(self._streams_file, "r", encoding="utf-8") as f:
                    self._saved_streams = json.load(f)
            except Exception:
                self._saved_streams = list(DEFAULT_SAMPLE_STREAMS)
        else:
            self._saved_streams = list(DEFAULT_SAMPLE_STREAMS)
            self._save_streams_to_disk()

    def _save_streams_to_disk(self) -> None:
        try:
            self._streams_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._streams_file, "w", encoding="utf-8") as f:
                json.dump(self._saved_streams, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_new_stream_tab(), "Yeni Akış Aç")
        self._tabs.addTab(self._create_saved_streams_tab(), "Kayıtlı Akışlar")
        main_layout.addWidget(self._tabs)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("İptal")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._play_btn = QPushButton("▶ Oynat")
        self._play_btn.setStyleSheet("font-weight: bold; background-color: #007acc; color: white;")
        self._play_btn.clicked.connect(self._on_play_clicked)
        btn_layout.addWidget(self._play_btn)

        main_layout.addLayout(btn_layout)

    def _create_new_stream_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # URL Input
        layout.addWidget(QLabel("Akış URL Adresi (RTSP, HLS .m3u8, HTTP, M3U):"))
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("rtsp://, https://.../stream.m3u8 veya http://...")
        self._url_input.textChanged.connect(self._on_url_changed)
        layout.addWidget(self._url_input)

        # Name Input
        layout.addWidget(QLabel("Akış / Kanal Adı (İsteğe bağlı):"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Örn: Salon Güvenlik Kamerası, Spor TV")
        layout.addWidget(self._name_input)

        # Buffer Latency Options
        layout.addWidget(QLabel("Ağ & Tampon Bellek Modu:"))
        buf_layout = QHBoxLayout()
        self._btn_group = QButtonGroup(self)

        self._radio_low_latency = QRadioButton("⚡ Düşük Gecikme (IP Kamera / RTSP)")
        self._radio_balanced = QRadioButton("⚖️ Dengeli (IPTV / HLS / Canlı Yayın)")
        self._radio_balanced.setChecked(True)

        self._btn_group.addButton(self._radio_low_latency, 1)
        self._btn_group.addButton(self._radio_balanced, 2)
        buf_layout.addWidget(self._radio_low_latency)
        buf_layout.addWidget(self._radio_balanced)
        layout.addLayout(buf_layout)

        # Save Stream Checkbox
        self._save_check = QCheckBox("Bu akışı kayıtlılara ekle")
        self._save_check.setChecked(True)
        layout.addWidget(self._save_check)

        layout.addStretch()
        return widget

    def _create_saved_streams_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Kayıtlı ve Örnek Akışlar:"))
        self._stream_list = QListWidget()
        self._stream_list.itemDoubleClicked.connect(self._on_saved_item_double_clicked)
        self._populate_saved_list()
        layout.addWidget(self._stream_list)

        actions_layout = QHBoxLayout()
        self._del_stream_btn = QPushButton("🗑️ Seçileni Sil")
        self._del_stream_btn.clicked.connect(self._on_delete_saved_stream)
        actions_layout.addWidget(self._del_stream_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        return widget

    def _populate_saved_list(self) -> None:
        self._stream_list.clear()
        for s in self._saved_streams:
            mode_badge = "⚡ Düşük Gecikme" if s.get("buffer_mode") == "low_latency" else "⚖️ Dengeli"
            item_text = f"{s.get('name', 'Akış')}  [{mode_badge}]\n  {s.get('url', '')}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, s)
            self._stream_list.addItem(item)

    def _on_url_changed(self, text: str) -> None:
        t = text.strip().lower()
        if t.startswith("rtsp://"):
            self._radio_low_latency.setChecked(True)
        elif t.endswith(".m3u8") or t.endswith(".m3u") or "hls" in t:
            self._radio_balanced.setChecked(True)

    def _on_play_clicked(self) -> None:
        if self._tabs.currentIndex() == 0:
            # From New Stream Tab
            url = self._url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir akış adresi girin.")
                return

            name = self._name_input.text().strip()
            if not name:
                name = url.split("/")[-1].split("?")[0] or "Ağ Akışı"

            buffer_mode = "low_latency" if self._radio_low_latency.isChecked() else "balanced"

            if self._save_check.isChecked():
                # Add or update in saved list
                self._saved_streams = [s for s in self._saved_streams if s.get("url") != url]
                self._saved_streams.insert(0, {
                    "name": name,
                    "url": url,
                    "buffer_mode": buffer_mode,
                })
                self._save_streams_to_disk()
                self._populate_saved_list()

            self.stream_selected.emit(url, name, buffer_mode)
            self.accept()
        else:
            # From Saved Streams Tab
            cur_item = self._stream_list.currentItem()
            if not cur_item:
                QMessageBox.warning(self, "Uyarı", "Lütfen listeden bir akış seçin.")
                return
            data = cur_item.data(Qt.ItemDataRole.UserRole)
            if data:
                self.stream_selected.emit(
                    data.get("url", ""),
                    data.get("name", "Akış"),
                    data.get("buffer_mode", "balanced")
                )
                self.accept()

    def _on_saved_item_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.stream_selected.emit(
                data.get("url", ""),
                data.get("name", "Akış"),
                data.get("buffer_mode", "balanced")
            )
            self.accept()

    def _on_delete_saved_stream(self) -> None:
        cur_row = self._stream_list.currentRow()
        if cur_row >= 0 and cur_row < len(self._saved_streams):
            del self._saved_streams[cur_row]
            self._save_streams_to_disk()
            self._populate_saved_list()

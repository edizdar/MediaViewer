"""Update checker and notification system for Media Viewer using GitHub Releases API."""

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
)

from app import __version__, APP_NAME
from app.localization import loc

REPO_URL = "https://api.github.com/repos/edizdar/MediaViewer/releases/latest"
RELEASE_PAGE_URL = "https://github.com/edizdar/MediaViewer/releases"


def parse_version(v_str: str) -> Tuple[int, ...]:
    """Convert version strings like 'v1.2.0' or '1.2.0' into comparable integer tuples."""
    v_clean = re.sub(r"^[vV]", "", v_str.strip())
    parts = []
    for p in v_clean.split("."):
        digits = re.findall(r"\d+", p)
        parts.append(int(digits[0]) if digits else 0)
    return tuple(parts)


@dataclass
class UpdateInfo:
    tag_name: str
    release_name: str
    body: str
    html_url: str
    download_url: str
    is_newer: bool
    current_version: str


def check_github_for_updates(timeout: int = 4) -> Optional[UpdateInfo]:
    """Query GitHub API to check for a newer release."""
    try:
        req = urllib.request.Request(
            REPO_URL,
            headers={"User-Agent": "MediaViewer-Update-Checker", "Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        name = data.get("name", tag)
        body = data.get("body", "")
        html_url = data.get("html_url", RELEASE_PAGE_URL)

        # Find direct asset download URL if available, fallback to html_url
        download_url = html_url
        assets = data.get("assets", [])
        for a in assets:
            if a.get("name", "").endswith(".exe"):
                download_url = a.get("browser_download_url", html_url)
                break

        latest_tuple = parse_version(tag)
        current_tuple = parse_version(__version__)

        is_newer = latest_tuple > current_tuple

        return UpdateInfo(
            tag_name=tag,
            release_name=name,
            body=body,
            html_url=html_url,
            download_url=download_url,
            is_newer=is_newer,
            current_version=__version__,
        )
    except Exception:
        return None


class UpdateCheckWorker(QThread):
    """Background worker thread to check for updates without blocking the UI."""

    # Emitted when check completes: (success, UpdateInfo or None, message)
    finished_check = Signal(bool, object, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def run(self) -> None:
        info = check_github_for_updates(timeout=5)
        if info is not None:
            if info.is_newer:
                self.finished_check.emit(True, info, f"Yeni sürüm mevcut: {info.tag_name}")
            else:
                self.finished_check.emit(True, info, "En güncel sürümü kullanıyorsunuz.")
        else:
            self.finished_check.emit(False, None, "Güncelleme sunucusuna bağlanılamadı.")


class UpdateDialog(QDialog):
    """Modern modal dialog displaying detailed update changelog and download action."""

    def __init__(self, info: UpdateInfo, parent=None) -> None:
        super().__init__(parent)
        self._info = info
        self.setWindowTitle(loc("update_dialog_title"))
        self.resize(580, 440)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel#updateTitle {
                color: #89b4fa;
                font-size: 17px;
                font-weight: bold;
            }
            QLabel#verLabel {
                color: #a6adc8;
                font-size: 13px;
            }
            QTextBrowser {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }
            QPushButton#downloadBtn {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 9px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#downloadBtn:hover {
                background-color: #106ebe;
            }
            QPushButton#laterBtn {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton#laterBtn:hover {
                background-color: #45475a;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(12)

        # Header
        top_row = QHBoxLayout()
        icon_lbl = QLabel("🎉")
        icon_lbl.setStyleSheet("font-size: 26px;")
        top_row.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel(loc("update_dialog_header").format(info.tag_name))
        title.setObjectName("updateTitle")
        title_box.addWidget(title)

        ver = QLabel(loc("update_dialog_sub").format(__version__, info.tag_name))
        ver.setObjectName("verLabel")
        title_box.addWidget(ver)
        top_row.addLayout(title_box)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Changelog Body
        body_label = QLabel(loc("update_dialog_notes"))
        layout.addWidget(body_label)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        # Format body markdown-like headers and bullets to HTML
        formatted_body = self._format_changelog_html(info.body)
        browser.setHtml(formatted_body)
        layout.addWidget(browser)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        later_btn = QPushButton(loc("update_dialog_later"))
        later_btn.setObjectName("laterBtn")
        later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        later_btn.clicked.connect(self.reject)
        btn_layout.addWidget(later_btn)

        download_btn = QPushButton(loc("update_dialog_dl_btn"))
        download_btn.setObjectName("downloadBtn")
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.clicked.connect(self._on_download_clicked)
        btn_layout.addWidget(download_btn)

        layout.addLayout(btn_layout)

    def _format_changelog_html(self, text: str) -> str:
        if not text:
            return loc("update_dialog_no_notes")
        html = text.replace("\n", "<br>")
        # bold
        html = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html)
        return f"<div style='color: #cdd6f4;'>{html}</div>"

    def _on_download_clicked(self) -> None:
        QDesktopServices.openUrl(QUrl(self._info.download_url))
        self.accept()


class UpdateNotificationBanner(QFrame):
    """Non-intrusive floating banner that slides in at the top of the main window."""

    view_details_requested = Signal(object)  # emitted with UpdateInfo

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("updateBanner")
        self._info: Optional[UpdateInfo] = None
        self.hide()

        self.setStyleSheet(
            """
            QFrame#updateBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #1e1e2e);
                border-bottom: 2px solid #3b82f6;
                padding: 6px 14px;
            }
            QLabel#bannerText {
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#actionBtn {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#actionBtn:hover {
                background-color: #2563eb;
            }
            QPushButton#secondaryBtn {
                background-color: rgba(255, 255, 255, 0.1);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QPushButton#secondaryBtn:hover {
                background-color: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }
            QPushButton#dismissBtn {
                background: transparent;
                color: #94a3b8;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 2px 6px;
            }
            QPushButton#dismissBtn:hover {
                color: #f87171;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Message
        self._msg_label = QLabel()
        self._msg_label.setObjectName("bannerText")
        layout.addWidget(self._msg_label)

        layout.addStretch()

        # View details button
        self._details_btn = QPushButton(loc("update_banner_details"))
        self._details_btn.setObjectName("secondaryBtn")
        self._details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._details_btn.clicked.connect(self._on_details_clicked)
        layout.addWidget(self._details_btn)

        # Quick download button
        self._download_btn = QPushButton(loc("update_banner_download"))
        self._download_btn.setObjectName("actionBtn")
        self._download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._download_btn.clicked.connect(self._on_download_clicked)
        layout.addWidget(self._download_btn)

        # Dismiss button
        dismiss_btn = QPushButton("✕")
        dismiss_btn.setObjectName("dismissBtn")
        dismiss_btn.setToolTip("Bildirimi Kapat")
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dismiss_btn.clicked.connect(self.hide)
        layout.addWidget(dismiss_btn)

    def show_update(self, info: UpdateInfo) -> None:
        self._info = info
        self._msg_label.setText(
            loc("update_banner_msg").format(info.tag_name, __version__)
        )
        self._details_btn.setText(loc("update_banner_details"))
        self._download_btn.setText(loc("update_banner_download"))
        self.show()

    def _on_details_clicked(self) -> None:
        if self._info:
            self.view_details_requested.emit(self._info)

    def _on_download_clicked(self) -> None:
        if self._info:
            QDesktopServices.openUrl(QUrl(self._info.download_url))

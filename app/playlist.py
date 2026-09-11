"""Playlist panel and manager for the Media Viewer application."""

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QFileDialog,
    QAbstractItemView,
    QSizePolicy,
)

from app.file_manager import FileManager

# ── Playlist file format ────────────────────────────────────────────────
PLAYLIST_FILTER = "Oynatma Listesi (*.mvpl);;JSON Dosyaları (*.json);;Tüm Dosyalar (*)"


class PlaylistManager:
    """Data model: an ordered list of media file paths with a cursor."""

    def __init__(self) -> None:
        self._files: list[Path] = []
        self._current_index: int = -1
        self._name: str = "Yeni Liste"
        self._save_path: Optional[Path] = None
        self._modified: bool = False

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def files(self) -> list[Path]:
        return list(self._files)

    @property
    def count(self) -> int:
        return len(self._files)

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def current_file(self) -> Optional[Path]:
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None

    @property
    def is_empty(self) -> bool:
        return len(self._files) == 0

    @property
    def is_modified(self) -> bool:
        return self._modified

    @property
    def save_path(self) -> Optional[Path]:
        return self._save_path

    # ── Mutation ────────────────────────────────────────────────────────

    def add_file(self, path: Path) -> None:
        """Add a single file to the end of the playlist."""
        path = Path(path).resolve()
        if path.suffix.lower() in FileManager.ALL_EXTENSIONS:
            self._files.append(path)
            self._modified = True
            if self._current_index == -1:
                self._current_index = 0

    def add_files(self, paths: list[Path]) -> None:
        for p in paths:
            self.add_file(p)

    def remove_at(self, index: int) -> None:
        if 0 <= index < len(self._files):
            self._files.pop(index)
            self._modified = True
            if self._current_index >= len(self._files):
                self._current_index = len(self._files) - 1

    def move_up(self, index: int) -> bool:
        if index > 0:
            self._files[index], self._files[index - 1] = (
                self._files[index - 1],
                self._files[index],
            )
            self._modified = True
            if self._current_index == index:
                self._current_index = index - 1
            elif self._current_index == index - 1:
                self._current_index = index
            return True
        return False

    def move_down(self, index: int) -> bool:
        if index < len(self._files) - 1:
            self._files[index], self._files[index + 1] = (
                self._files[index + 1],
                self._files[index],
            )
            self._modified = True
            if self._current_index == index:
                self._current_index = index + 1
            elif self._current_index == index + 1:
                self._current_index = index
            return True
        return False

    def clear(self) -> None:
        self._files.clear()
        self._current_index = -1
        self._modified = True

    # ── Navigation ──────────────────────────────────────────────────────

    def go_to(self, index: int) -> Optional[Path]:
        if 0 <= index < len(self._files):
            self._current_index = index
            return self.current_file
        return None

    def next_file(self) -> Optional[Path]:
        if not self._files:
            return None
        self._current_index = (self._current_index + 1) % len(self._files)
        return self.current_file

    def previous_file(self) -> Optional[Path]:
        if not self._files:
            return None
        self._current_index = (self._current_index - 1) % len(self._files)
        return self.current_file

    # ── Persistence ─────────────────────────────────────────────────────

    def save(self, path: Path) -> None:
        data = {
            "name": self._name,
            "files": [str(f) for f in self._files],
        }
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix(".mvpl")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._save_path = path
        self._modified = False

    def load(self, path: Path) -> bool:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self._name = data.get("name", Path(path).stem)
            self._files = [Path(f) for f in data.get("files", [])]
            # Remove non-existent files silently
            self._files = [f for f in self._files if f.exists()]
            self._current_index = 0 if self._files else -1
            self._save_path = Path(path)
            self._modified = False
            return True
        except (json.JSONDecodeError, KeyError, OSError):
            return False

    def new(self, name: str = "Yeni Liste") -> None:
        self._files.clear()
        self._current_index = -1
        self._name = name
        self._save_path = None
        self._modified = False


# ── Helpers ─────────────────────────────────────────────────────────────

def _file_icon(path: Path) -> str:
    """Return an emoji icon based on file type."""
    ext = path.suffix.lower()
    if ext in FileManager.IMAGE_EXTENSIONS:
        return "🖼"
    elif ext in FileManager.VIDEO_EXTENSIONS:
        return "🎬"
    return "📄"


def _small_button(text: str, tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(28)
    btn.setStyleSheet(
        """
        QPushButton {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #45475a;
            border-color: #89b4fa;
        }
        QPushButton:pressed {
            background-color: #585b70;
        }
        """
    )
    return btn


# ── Panel Widget ────────────────────────────────────────────────────────


class PlaylistPanel(QWidget):
    """Left-side panel for managing and navigating playlists."""

    file_selected = Signal(str)       # path of file to open
    playlist_changed = Signal(bool)   # True if playlist has items (active)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("playlistPanel")
        self.setFixedWidth(260)
        self.setStyleSheet(
            """
            QWidget#playlistPanel {
                background-color: #181825;
                border-right: 1px solid #313244;
            }
            """
        )

        self._manager = PlaylistManager()
        self._setup_ui()
        self._connect_signals()

    @property
    def manager(self) -> PlaylistManager:
        return self._manager

    @property
    def is_active(self) -> bool:
        """True when the playlist has items and the panel is visible."""
        return self.isVisible() and not self._manager.is_empty

    # ── UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Title
        title = QLabel("📋  Oynatma Listesi")
        title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #cdd6f4; padding-bottom: 2px;"
        )
        layout.addWidget(title)

        # Playlist name
        self._name_label = QLabel("Yeni Liste")
        self._name_label.setStyleSheet(
            "font-size: 12px; color: #a6adc8; padding-bottom: 4px;"
        )
        layout.addWidget(self._name_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #313244; max-height: 1px;")
        layout.addWidget(sep)

        # ── Top buttons: New, Open, Save ──
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        self._new_btn = _small_button("📄 Yeni", "Yeni oynatma listesi")
        top_row.addWidget(self._new_btn)

        self._open_btn = _small_button("📂 Aç", "Oynatma listesi aç")
        top_row.addWidget(self._open_btn)

        self._save_btn = _small_button("💾 Kaydet", "Oynatma listesini kaydet")
        top_row.addWidget(self._save_btn)

        layout.addLayout(top_row)

        # ── File list ──
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._list_widget.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
        )
        self._list_widget.setStyleSheet(
            """
            QListWidget {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 4px;
                color: #cdd6f4;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 5px 8px;
                border-bottom: 1px solid #313244;
            }
            QListWidget::item:selected {
                background-color: #313244;
                color: #89b4fa;
            }
            QListWidget::item:hover {
                background-color: #282839;
            }
            """
        )
        layout.addWidget(self._list_widget, stretch=1)

        # ── Item count ──
        self._count_label = QLabel("0 dosya")
        self._count_label.setStyleSheet("font-size: 11px; color: #6c7086;")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._count_label)

        # ── Bottom buttons: Add, Remove, Move, Clear ──
        add_row = QHBoxLayout()
        add_row.setSpacing(4)

        self._add_current_btn = _small_button("+ Mevcut", "Görüntülenen dosyayı ekle")
        add_row.addWidget(self._add_current_btn)

        self._add_files_btn = _small_button("+ Dosya", "Dosyalar seç ve ekle")
        add_row.addWidget(self._add_files_btn)

        layout.addLayout(add_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(4)

        self._remove_btn = _small_button("✕", "Seçili dosyayı kaldır")
        self._remove_btn.setFixedWidth(36)
        action_row.addWidget(self._remove_btn)

        self._up_btn = _small_button("▲", "Yukarı taşı")
        self._up_btn.setFixedWidth(36)
        action_row.addWidget(self._up_btn)

        self._down_btn = _small_button("▼", "Aşağı taşı")
        self._down_btn.setFixedWidth(36)
        action_row.addWidget(self._down_btn)

        action_row.addStretch()

        self._clear_btn = _small_button("🗑 Temizle", "Listeyi temizle")
        action_row.addWidget(self._clear_btn)

        layout.addLayout(action_row)

    def _connect_signals(self) -> None:
        self._new_btn.clicked.connect(self._on_new)
        self._open_btn.clicked.connect(self._on_open)
        self._save_btn.clicked.connect(self._on_save)
        self._add_files_btn.clicked.connect(self._on_add_files)
        self._add_current_btn.clicked.connect(self._on_add_current_request)
        self._remove_btn.clicked.connect(self._on_remove)
        self._up_btn.clicked.connect(self._on_move_up)
        self._down_btn.clicked.connect(self._on_move_down)
        self._clear_btn.clicked.connect(self._on_clear)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

    # ── Public API ──────────────────────────────────────────────────────

    def add_current_file(self, path: Path) -> None:
        """Add a file to the playlist (called by MainWindow)."""
        self._manager.add_file(path)
        self._refresh_list()

    def highlight_current(self, index: int) -> None:
        """Highlight the currently playing item."""
        if 0 <= index < self._list_widget.count():
            self._list_widget.setCurrentRow(index)

    def next_file(self) -> Optional[str]:
        path = self._manager.next_file()
        if path:
            self.highlight_current(self._manager.current_index)
            return str(path)
        return None

    def previous_file(self) -> Optional[str]:
        path = self._manager.previous_file()
        if path:
            self.highlight_current(self._manager.current_index)
            return str(path)
        return None

    # ── Private Slots ───────────────────────────────────────────────────

    def _on_new(self) -> None:
        self._manager.new()
        self._refresh_list()
        self._name_label.setText("Yeni Liste")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Oynatma Listesi Aç", "", PLAYLIST_FILTER
        )
        if path:
            if self._manager.load(Path(path)):
                self._name_label.setText(self._manager.name)
                self._refresh_list()
                # Auto-play first file
                first = self._manager.go_to(0)
                if first:
                    self.highlight_current(0)
                    self.file_selected.emit(str(first))

    def _on_save(self) -> None:
        if self._manager.save_path:
            self._manager.save(self._manager.save_path)
        else:
            self._on_save_as()

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Oynatma Listesini Kaydet",
            self._manager.name + ".mvpl",
            PLAYLIST_FILTER,
        )
        if path:
            self._manager.name = Path(path).stem
            self._name_label.setText(self._manager.name)
            self._manager.save(Path(path))

    def _on_add_files(self) -> None:
        file_filter = FileManager.get_file_filter()
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Dosyaları Ekle", "", file_filter
        )
        if paths:
            self._manager.add_files([Path(p) for p in paths])
            self._refresh_list()

    def _on_add_current_request(self) -> None:
        """Emit a signal so MainWindow can provide the current file."""
        # This is handled via a direct connection in MainWindow
        pass  # Placeholder — MainWindow connects this button directly

    def _on_remove(self) -> None:
        row = self._list_widget.currentRow()
        if row >= 0:
            self._manager.remove_at(row)
            self._refresh_list()

    def _on_move_up(self) -> None:
        row = self._list_widget.currentRow()
        if self._manager.move_up(row):
            self._refresh_list()
            self._list_widget.setCurrentRow(row - 1)

    def _on_move_down(self) -> None:
        row = self._list_widget.currentRow()
        if self._manager.move_down(row):
            self._refresh_list()
            self._list_widget.setCurrentRow(row + 1)

    def _on_clear(self) -> None:
        self._manager.clear()
        self._refresh_list()

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        row = self._list_widget.row(item)
        path = self._manager.go_to(row)
        if path:
            self.file_selected.emit(str(path))

    # ── Refresh ─────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        """Rebuild the QListWidget from the manager's file list."""
        self._list_widget.clear()
        for f in self._manager.files:
            icon = _file_icon(f)
            item = QListWidgetItem(f"{icon}  {f.name}")
            item.setToolTip(str(f))
            self._list_widget.addItem(item)

        count = self._manager.count
        self._count_label.setText(
            f"{count} dosya" if count != 1 else "1 dosya"
        )

        if self._manager.current_index >= 0:
            self._list_widget.setCurrentRow(self._manager.current_index)

        self.playlist_changed.emit(not self._manager.is_empty)

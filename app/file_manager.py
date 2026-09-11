"""File manager for navigating media files in a directory."""

from pathlib import Path
from typing import Optional


class FileManager:
    """Manages a list of media files in a directory and provides navigation."""

    IMAGE_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp",
        ".tiff", ".tif", ".ico", ".svg",
    }

    VIDEO_EXTENSIONS = {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
        ".webm", ".m4v", ".mpg", ".mpeg", ".3gp",
    }

    ALL_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

    def __init__(self) -> None:
        self._files: list[Path] = []
        self._current_index: int = -1
        self._directory: Optional[Path] = None

    def load_from_file(self, file_path: str | Path) -> None:
        """Load all supported media files from the directory of the given file."""
        path = Path(file_path).resolve()
        if not path.is_file():
            return

        self._directory = path.parent
        self._scan_directory()

        # Set current index to the opened file
        try:
            self._current_index = self._files.index(path)
        except ValueError:
            self._current_index = 0 if self._files else -1

    def _scan_directory(self) -> None:
        """Scan the current directory for supported media files."""
        if self._directory is None:
            return

        self._files = sorted(
            [
                f
                for f in self._directory.iterdir()
                if f.is_file() and f.suffix.lower() in self.ALL_EXTENSIONS
            ],
            key=lambda f: f.name.lower(),
        )

    @property
    def current_file(self) -> Optional[Path]:
        """Return the current file path, or None if no files are loaded."""
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None

    @property
    def current_index(self) -> int:
        """Return the current file index (0-based)."""
        return self._current_index

    @property
    def file_count(self) -> int:
        """Return total number of media files in the directory."""
        return len(self._files)

    @property
    def has_files(self) -> bool:
        """Return True if there are any files loaded."""
        return len(self._files) > 0

    def next_file(self) -> Optional[Path]:
        """Move to the next file and return its path. Wraps around."""
        if not self._files:
            return None
        self._current_index = (self._current_index + 1) % len(self._files)
        return self.current_file

    def previous_file(self) -> Optional[Path]:
        """Move to the previous file and return its path. Wraps around."""
        if not self._files:
            return None
        self._current_index = (self._current_index - 1) % len(self._files)
        return self.current_file

    def is_image(self, path: Optional[Path] = None) -> bool:
        """Check if the given path (or current file) is an image."""
        p = path or self.current_file
        if p is None:
            return False
        return p.suffix.lower() in self.IMAGE_EXTENSIONS

    def is_video(self, path: Optional[Path] = None) -> bool:
        """Check if the given path (or current file) is a video."""
        p = path or self.current_file
        if p is None:
            return False
        return p.suffix.lower() in self.VIDEO_EXTENSIONS

    def delete_current(self) -> Optional[Path]:
        """Remove the current file from the list and return the next file to show.

        Note: This only removes from the internal list, not from disk.
        """
        if not self._files or self._current_index < 0:
            return None

        self._files.pop(self._current_index)

        if not self._files:
            self._current_index = -1
            return None

        # Adjust index
        if self._current_index >= len(self._files):
            self._current_index = len(self._files) - 1

        return self.current_file

    @staticmethod
    def get_file_filter() -> str:
        """Return a file dialog filter string for supported formats."""
        img_exts = " ".join(f"*{ext}" for ext in sorted(FileManager.IMAGE_EXTENSIONS))
        vid_exts = " ".join(f"*{ext}" for ext in sorted(FileManager.VIDEO_EXTENSIONS))
        all_exts = f"{img_exts} {vid_exts}"

        return (
            f"Tüm Medya Dosyaları ({all_exts});;"
            f"Fotoğraflar ({img_exts});;"
            f"Videolar ({vid_exts});;"
            f"Tüm Dosyalar (*)"
        )

    def get_file_size_str(self, path: Optional[Path] = None) -> str:
        """Return human-readable file size."""
        p = path or self.current_file
        if p is None or not p.exists():
            return ""

        size = p.stat().st_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

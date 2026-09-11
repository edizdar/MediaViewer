"""Image adjustment panel for brightness, contrast, and gamma correction."""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QFrame,
)


class AdjustmentSlider(QWidget):
    """A labeled slider with value display and optional decimal formatting."""

    value_changed = Signal(int)

    def __init__(
        self,
        label: str,
        min_val: int,
        max_val: int,
        default: int,
        divisor: int = 1,
        suffix: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._default = default
        self._divisor = divisor
        self._suffix = suffix

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        # Label + value row
        label_row = QHBoxLayout()
        name_label = QLabel(label)
        name_label.setStyleSheet("font-size: 12px; color: #a6adc8;")
        label_row.addWidget(name_label)
        label_row.addStretch()

        self._value_label = QLabel(self._format_value(default))
        self._value_label.setStyleSheet(
            "font-size: 12px; color: #89b4fa; font-weight: bold; min-width: 44px;"
        )
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_row.addWidget(self._value_label)
        layout.addLayout(label_row)

        # Slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(min_val, max_val)
        self._slider.setValue(default)
        self._slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._slider)

    def _format_value(self, value: int) -> str:
        if self._divisor != 1:
            return f"{value / self._divisor:.2f}{self._suffix}"
        return f"{value}{self._suffix}"

    def _on_changed(self, value: int) -> None:
        self._value_label.setText(self._format_value(value))
        self.value_changed.emit(value)

    def value(self) -> int:
        return self._slider.value()

    def reset(self) -> None:
        self._slider.setValue(self._default)


class AdjustmentsPanel(QWidget):
    """Side panel with brightness, contrast, and gamma sliders.

    Emits adjustments_changed(brightness, contrast, gamma) with a debounce
    so that heavy LUT recalculations only happen after the user pauses sliding.
    """

    adjustments_changed = Signal(int, int, float)  # brightness, contrast, gamma

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("adjustmentsPanel")
        self.setFixedWidth(250)
        self.setStyleSheet(
            """
            QWidget#adjustmentsPanel {
                background-color: #181825;
                border-left: 1px solid #313244;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        # Title
        title = QLabel("🎨  Renk Ayarları")
        title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #cdd6f4; padding-bottom: 4px;"
        )
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #313244; max-height: 1px;")
        layout.addWidget(sep)

        # ── Brightness ──
        self._brightness = AdjustmentSlider(
            "☀  Parlaklık", -100, 100, 0
        )
        self._brightness.value_changed.connect(self._schedule_update)
        layout.addWidget(self._brightness)

        # ── Contrast ──
        self._contrast = AdjustmentSlider(
            "◑  Kontrast", -100, 100, 0
        )
        self._contrast.value_changed.connect(self._schedule_update)
        layout.addWidget(self._contrast)

        # ── Gamma ── (stored as 10..300 → 0.10..3.00)
        self._gamma = AdjustmentSlider(
            "γ  Gamma", 10, 300, 100, divisor=100
        )
        self._gamma.value_changed.connect(self._schedule_update)
        layout.addWidget(self._gamma)

        layout.addStretch()

        # ── Reset button ──
        reset_btn = QPushButton("↺  Sıfırla")
        reset_btn.setToolTip("Tüm renk ayarlarını varsayılana döndür")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self.reset)
        layout.addWidget(reset_btn)

        # Debounce timer — prevent heavy computation on every slider tick
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._emit_changes)

    # ── Public API ──────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset all sliders to their defaults."""
        self._brightness.reset()
        self._contrast.reset()
        self._gamma.reset()
        self._emit_changes()

    def has_adjustments(self) -> bool:
        """Return True if any adjustment differs from the default."""
        return (
            self._brightness.value() != 0
            or self._contrast.value() != 0
            or self._gamma.value() != 100
        )

    # ── Private ─────────────────────────────────────────────────────────

    def _schedule_update(self) -> None:
        self._timer.start()

    def _emit_changes(self) -> None:
        gamma = self._gamma.value() / 100.0
        self.adjustments_changed.emit(
            self._brightness.value(),
            self._contrast.value(),
            gamma,
        )

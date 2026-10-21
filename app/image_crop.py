"""Interactive image cropping components for Media Viewer."""

from typing import Optional
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPainterPath,
    QCursor,
)
from PySide6.QtWidgets import (
    QGraphicsObject,
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGraphicsSceneMouseEvent,
)


class CropOverlayItem(QGraphicsObject):
    """Interactive crop selection overlay item in QGraphicsScene.

    Allows resizing via 8 handles, moving the selection, aspect ratio locking,
    and visual feedback with darkened exterior and rule-of-thirds grid.
    """

    rect_changed = Signal(QRectF)

    HANDLE_SIZE = 10
    HANDLE_HIT_RADIUS = 12

    # Handle identifiers
    NONE = 0
    HANDLE_TL = 1
    HANDLE_T = 2
    HANDLE_TR = 3
    HANDLE_R = 4
    HANDLE_BR = 5
    HANDLE_B = 6
    HANDLE_BL = 7
    HANDLE_L = 8
    MOVE = 9
    CREATE = 10

    def __init__(self, image_width: int, image_height: int, parent=None):
        super().__init__(parent)
        self.setZValue(100)
        self._image_rect = QRectF(0, 0, image_width, image_height)

        # Default crop rect: 80% centered
        w = image_width * 0.8
        h = image_height * 0.8
        x = (image_width - w) / 2.0
        y = (image_height - h) / 2.0
        self._crop_rect = QRectF(x, y, w, h)

        self._aspect_ratio: Optional[float] = None  # width / height or None
        self._active_action = self.NONE
        self._drag_start_pos = QPointF()
        self._drag_start_rect = QRectF()

        self.setAcceptHoverEvents(True)

    @property
    def crop_rect(self) -> QRectF:
        return self._crop_rect.normalized()

    def set_aspect_ratio(self, ratio: Optional[float]) -> None:
        """Set fixed aspect ratio (width / height) or None for freeform."""
        self._aspect_ratio = ratio
        if ratio is not None and ratio > 0:
            # Re-adjust current crop rect to match aspect ratio
            r = self._crop_rect.normalized()
            center = r.center()
            current_ratio = r.width() / max(r.height(), 1)
            if current_ratio > ratio:
                new_w = r.height() * ratio
                new_h = r.height()
            else:
                new_w = r.width()
                new_h = r.width() / ratio

            new_x = center.x() - new_w / 2.0
            new_y = center.y() - new_h / 2.0
            self._crop_rect = self._clamp_rect(QRectF(new_x, new_y, new_w, new_h))
            self.prepareGeometryChange()
            self.update()
            self.rect_changed.emit(self.crop_rect)

    def boundingRect(self) -> QRectF:
        return self._image_rect

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        r = self._crop_rect.normalized()

        # 1. Darken outer area
        full_path = QPainterPath()
        full_path.addRect(self._image_rect)
        crop_path = QPainterPath()
        crop_path.addRect(r)
        mask_path = full_path.subtracted(crop_path)
        painter.fillPath(mask_path, QColor(0, 0, 0, 160))

        # 2. Border
        pen_border = QPen(QColor(137, 180, 250), 2.0)  # Catppuccin Blue
        painter.setPen(pen_border)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(r)

        # 3. Rule of thirds grid
        grid_pen = QPen(QColor(255, 255, 255, 75), 1.0, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        x1 = r.left() + r.width() / 3.0
        x2 = r.left() + r.width() * 2.0 / 3.0
        y1 = r.top() + r.height() / 3.0
        y2 = r.top() + r.height() * 2.0 / 3.0
        painter.drawLine(QPointF(x1, r.top()), QPointF(x1, r.bottom()))
        painter.drawLine(QPointF(x2, r.top()), QPointF(x2, r.bottom()))
        painter.drawLine(QPointF(r.left(), y1), QPointF(r.right(), y1))
        painter.drawLine(QPointF(r.left(), y2), QPointF(r.right(), y2))

        # 4. Handles (8 handles)
        handle_size = self.HANDLE_SIZE
        painter.setPen(QPen(QColor(24, 24, 37), 1.5))
        painter.setBrush(QBrush(QColor(255, 255, 255)))

        for _, pt in self._get_handles(r).items():
            handle_rect = QRectF(
                pt.x() - handle_size / 2.0,
                pt.y() - handle_size / 2.0,
                handle_size,
                handle_size,
            )
            painter.drawRect(handle_rect)

        painter.restore()

    def _get_handles(self, r: QRectF) -> dict[int, QPointF]:
        """Compute points for all 8 handles."""
        return {
            self.HANDLE_TL: r.topLeft(),
            self.HANDLE_T: QPointF(r.center().x(), r.top()),
            self.HANDLE_TR: r.topRight(),
            self.HANDLE_R: QPointF(r.right(), r.center().y()),
            self.HANDLE_BR: r.bottomRight(),
            self.HANDLE_B: QPointF(r.center().x(), r.bottom()),
            self.HANDLE_BL: r.bottomLeft(),
            self.HANDLE_L: QPointF(r.left(), r.center().y()),
        }

    def _hit_test(self, pos: QPointF) -> int:
        """Determine what part of the crop overlay is under the given point."""
        r = self._crop_rect.normalized()
        radius_sq = self.HANDLE_HIT_RADIUS * self.HANDLE_HIT_RADIUS

        for handle_id, pt in self._get_handles(r).items():
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= radius_sq:
                return handle_id

        if r.contains(pos):
            return self.MOVE

        return self.CREATE

    def _cursor_for_action(self, action: int) -> Qt.CursorShape:
        if action in (self.HANDLE_TL, self.HANDLE_BR):
            return Qt.CursorShape.SizeFDiagCursor
        elif action in (self.HANDLE_TR, self.HANDLE_BL):
            return Qt.CursorShape.SizeBDiagCursor
        elif action in (self.HANDLE_T, self.HANDLE_B):
            return Qt.CursorShape.SizeVerCursor
        elif action in (self.HANDLE_L, self.HANDLE_R):
            return Qt.CursorShape.SizeHorCursor
        elif action == self.MOVE:
            return Qt.CursorShape.SizeAllCursor
        return Qt.CursorShape.CrossCursor

    def hoverMoveEvent(self, event) -> None:
        action = self._hit_test(event.pos())
        self.setCursor(QCursor(self._cursor_for_action(action)))
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_start_rect = self._crop_rect.normalized()
            self._active_action = self._hit_test(event.pos())

            if self._active_action == self.CREATE:
                self._crop_rect = QRectF(event.pos(), event.pos())
                self.update()

            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._active_action == self.NONE:
            super().mouseMoveEvent(event)
            return

        cur_pos = event.pos()
        delta = cur_pos - self._drag_start_pos
        init = self._drag_start_rect

        if self._active_action == self.CREATE:
            # Dragging out a new rectangle
            x1 = min(self._drag_start_pos.x(), cur_pos.x())
            y1 = min(self._drag_start_pos.y(), cur_pos.y())
            w = abs(cur_pos.x() - self._drag_start_pos.x())
            h = abs(cur_pos.y() - self._drag_start_pos.y())
            if self._aspect_ratio:
                h = w / self._aspect_ratio
            new_r = QRectF(x1, y1, w, h)
            self._crop_rect = self._clamp_rect(new_r)

        elif self._active_action == self.MOVE:
            new_x = init.x() + delta.x()
            new_y = init.y() + delta.y()
            new_x = max(0.0, min(new_x, self._image_rect.width() - init.width()))
            new_y = max(0.0, min(new_y, self._image_rect.height() - init.height()))
            self._crop_rect = QRectF(new_x, new_y, init.width(), init.height())

        else:
            # Resizing via handle
            left = init.left()
            top = init.top()
            right = init.right()
            bottom = init.bottom()

            act = self._active_action
            if act in (self.HANDLE_TL, self.HANDLE_L, self.HANDLE_BL):
                left = min(init.left() + delta.x(), right - 20)
            if act in (self.HANDLE_TR, self.HANDLE_R, self.HANDLE_BR):
                right = max(init.right() + delta.x(), left + 20)
            if act in (self.HANDLE_TL, self.HANDLE_T, self.HANDLE_TR):
                top = min(init.top() + delta.y(), bottom - 20)
            if act in (self.HANDLE_BL, self.HANDLE_B, self.HANDLE_BR):
                bottom = max(init.bottom() + delta.y(), top + 20)

            # Apply aspect ratio if active
            if self._aspect_ratio:
                w = right - left
                h = bottom - top
                if act in (self.HANDLE_L, self.HANDLE_R):
                    h = w / self._aspect_ratio
                    top = init.center().y() - h / 2.0
                    bottom = top + h
                elif act in (self.HANDLE_T, self.HANDLE_B):
                    w = h * self._aspect_ratio
                    left = init.center().x() - w / 2.0
                    right = left + w
                elif act in (self.HANDLE_TL, self.HANDLE_TR, self.HANDLE_BL, self.HANDLE_BR):
                    target_h = w / self._aspect_ratio
                    if act in (self.HANDLE_TL, self.HANDLE_TR):
                        top = bottom - target_h
                    else:
                        bottom = top + target_h

            new_r = QRectF(left, top, right - left, bottom - top)
            self._crop_rect = self._clamp_rect(new_r)

        self.prepareGeometryChange()
        self.update()
        self.rect_changed.emit(self.crop_rect)
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._active_action = self.NONE
            # Ensure minimum size
            r = self._crop_rect.normalized()
            if r.width() < 10 or r.height() < 10:
                # Revert to a safe small centered box
                w = max(50.0, r.width())
                h = max(50.0, r.height())
                self._crop_rect = self._clamp_rect(QRectF(r.x(), r.y(), w, h))
                self.update()
                self.rect_changed.emit(self.crop_rect)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _clamp_rect(self, r: QRectF) -> QRectF:
        """Clamp rectangle to keep it strictly within image bounds."""
        norm = r.normalized()
        x1 = max(0.0, min(norm.left(), self._image_rect.width() - 10))
        y1 = max(0.0, min(norm.top(), self._image_rect.height() - 10))
        x2 = min(self._image_rect.width(), max(norm.right(), x1 + 10))
        y2 = min(self._image_rect.height(), max(norm.bottom(), y1 + 10))
        return QRectF(x1, y1, x2 - x1, y2 - y1)


class CropHUD(QWidget):
    """Floating control bar displayed at the top of ImageViewer during crop mode."""

    apply_clicked = Signal()
    save_clicked = Signal()
    cancel_clicked = Signal()
    ratio_changed = Signal(object)  # float or None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cropHUD")
        self.setStyleSheet(
            """
            QWidget#cropHUD {
                background-color: rgba(24, 24, 37, 0.94);
                border: 1px solid #45475a;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                color: #cdd6f4;
                font-size: 13px;
            }
            QLabel#cropSizeLabel {
                font-weight: bold;
                color: #89b4fa;
                padding: 0 4px;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 3px 8px;
                min-width: 90px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
                border: 1px solid #45475a;
            }
            QPushButton {
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: bold;
                min-height: 24px;
            }
            QPushButton#applyBtn {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
            }
            QPushButton#applyBtn:hover {
                background-color: #b4befe;
            }
            QPushButton#saveBtn {
                background-color: #a6e3a1;
                color: #11111b;
                border: none;
            }
            QPushButton#saveBtn:hover {
                background-color: #94e2d5;
            }
            QPushButton#cancelBtn {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
            }
            QPushButton#cancelBtn:hover {
                background-color: #45475a;
                color: #f38ba8;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("✂ Kırpma:")
        title_label.setStyleSheet("font-weight: bold; color: #fab387;")
        layout.addWidget(title_label)

        # Dimension display
        self._size_label = QLabel("0 × 0 px")
        self._size_label.setObjectName("cropSizeLabel")
        layout.addWidget(self._size_label)

        # Aspect ratio selector
        self._ratio_combo = QComboBox()
        self._ratio_combo.addItem("Serbest", None)
        self._ratio_combo.addItem("1:1 (Kare)", 1.0)
        self._ratio_combo.addItem("16:9 (Geniş)", 16.0 / 9.0)
        self._ratio_combo.addItem("4:3 (Standart)", 4.0 / 3.0)
        self._ratio_combo.addItem("3:2 (Fotoğraf)", 3.0 / 2.0)
        self._ratio_combo.currentIndexChanged.connect(self._on_ratio_changed)
        layout.addWidget(self._ratio_combo)

        # Apply button
        apply_btn = QPushButton("✔ Kırp (Enter)")
        apply_btn.setObjectName("applyBtn")
        apply_btn.setToolTip("Kırpılmış görüntüyü görüntüleyiciye uygular")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self.apply_clicked)
        layout.addWidget(apply_btn)

        # Save button
        save_btn = QPushButton("💾 Farklı Kaydet")
        save_btn.setObjectName("saveBtn")
        save_btn.setToolTip("Kırpılan alanı yeni bir dosya olarak kaydeder")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_clicked)
        layout.addWidget(save_btn)

        # Cancel button
        cancel_btn = QPushButton("✕ İptal (Esc)")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setToolTip("Kırpma modunu kapatır")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.cancel_clicked)
        layout.addWidget(cancel_btn)

    def set_crop_dimensions(self, width: int, height: int) -> None:
        """Update the pixel size label."""
        self._size_label.setText(f"{width} × {height} px")

    def _on_ratio_changed(self, index: int) -> None:
        ratio = self._ratio_combo.currentData()
        self.ratio_changed.emit(ratio)

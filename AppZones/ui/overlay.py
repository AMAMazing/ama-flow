from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

class FullscreenPreviewOverlay(QWidget):
    """
    1:1 Fullscreen live preview overlay mirroring the FancyZones Ctrl+drag look,
    enhanced to clearly display each zone's live resolution.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.zones = []

    def set_zones(self, zones, screen_geo=None):
        self.zones = zones
        if screen_geo:
            self.setGeometry(screen_geo)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Subtle dark dimming across the entire screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 115))

        palette = [
            (QColor(0, 120, 212, 55), QColor(0, 120, 212, 220), "#0078d4"),
            (QColor(16, 185, 129, 55), QColor(16, 185, 129, 220), "#10b981"),
            (QColor(139, 92, 246, 55), QColor(139, 92, 246, 220), "#8b5cf6"),
            (QColor(245, 158, 11, 55), QColor(245, 158, 11, 220), "#f59e0b"),
            (QColor(236, 72, 153, 55), QColor(236, 72, 153, 220), "#ec4899")
        ]

        for i, z in enumerate(self.zones):
            rect = z.get("rect")
            if not rect:
                continue

            rx = int(rect.get("x", 0))
            ry = int(rect.get("y", 0))
            rw = int(rect.get("width", 0))
            rh = int(rect.get("height", 0))
            if rw <= 0 or rh <= 0:
                continue

            zr = QRect(rx, ry, rw, rh)
            zr.adjust(6, 6, -6, -6)

            fill_c, border_c, accent_hex = palette[i % len(palette)]

            # Draw zone backdrop and border
            painter.setBrush(fill_c)
            painter.setPen(QPen(border_c, 2.5))
            painter.drawRoundedRect(zr, 10, 10)

            # Zone number badge in top-left
            badge_rect = QRect(zr.x() + 14, zr.y() + 14, 32, 32)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.drawRoundedRect(badge_rect, 6, 6)

            painter.setPen(QPen(border_c, 1.5))
            painter.drawRoundedRect(badge_rect, 6, 6)

            painter.setPen(QColor(255, 255, 255, 255))
            font_badge = QFont("Segoe UI", 12, QFont.Weight.Bold)
            painter.setFont(font_badge)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            # Header info next to badge
            title = z.get("window_title", "").strip() or f"Zone {i + 1}"
            pos = z.get("pos", "").strip()
            header_text = f"{title}"
            if pos:
                header_text += f"  ({pos})"

            painter.setPen(QColor(240, 240, 245, 230))
            font_title = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
            painter.setFont(font_title)
            title_rect = QRect(zr.x() + 54, zr.y() + 14, max(50, zr.width() - 70), 32)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, header_text)

            # Prominent live Resolution Display in center
            res_text = f"{rw} × {rh} px"

            center_box = QRect(zr.x() + 10, zr.y() + (zr.height() // 2) - 40, zr.width() - 20, 80)

            painter.setPen(QColor(255, 255, 255, 255))
            font_res = QFont("Segoe UI", 26, QFont.Weight.Bold)
            painter.setFont(font_res)
            painter.drawText(center_box, Qt.AlignmentFlag.AlignCenter, res_text)
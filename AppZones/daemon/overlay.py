from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen

try:
    from ..core.config import CONFIG_PATH, load_config
except (ImportError, ValueError):
    from core.config import CONFIG_PATH, load_config

class OverlayWidget(QWidget):
    """
    Transparent snapping overlay showing active zones and highlighting the target
    zone during a window drag operation.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.zones = []
        self.hovered_zone_idx = -1

    def load_zones(self):
        config = load_config(CONFIG_PATH)

        if "presets" in config and "active_preset" in config:
            active = config["active_preset"]
            preset_data = config["presets"].get(active, [])
            if isinstance(preset_data, dict):
                self.zones = preset_data.get("zones", [])
            else:
                self.zones = preset_data
        else:
            self.zones = config.get("zones", [])

        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            self.setGeometry(primary_screen.geometry())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dim background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # Draw non-hovered zones first, then hovered zone last so its highlight is never covered
        draw_order = [i for i in range(len(self.zones)) if i != self.hovered_zone_idx]
        if 0 <= self.hovered_zone_idx < len(self.zones):
            draw_order.append(self.hovered_zone_idx)

        for i in draw_order:
            z = self.zones[i]
            rect = z.get("rect")
            if not rect:
                continue
            zr = QRect(int(rect["x"]), int(rect["y"]), int(rect["width"]), int(rect["height"]))

            # Draw Zone
            if i == self.hovered_zone_idx:
                painter.setBrush(QColor(0, 120, 212, 140))
                painter.setPen(QPen(QColor(0, 120, 212, 255), 3))
            else:
                painter.setBrush(QColor(255, 255, 255, 30))
                painter.setPen(QPen(QColor(255, 255, 255, 150), 2))

            zr.adjust(6, 6, -6, -6)
            painter.drawRoundedRect(zr, 8, 8)

            # Draw zone number
            painter.setPen(QColor(255, 255, 255, 255))
            font = painter.font()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(zr, Qt.AlignmentFlag.AlignCenter, str(i + 1))
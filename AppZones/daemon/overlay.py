from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen

try:
    from ..core.config import CONFIG_PATH, load_config
    from ..core.win_utils import get_open_windows, get_screen_resolution
    from ..core.layout_engine import calculate_smart_layout, calculate_fullscreen_corner_rects
except (ImportError, ValueError):
    from core.config import CONFIG_PATH, load_config
    from core.win_utils import get_open_windows, get_screen_resolution
    from core.layout_engine import calculate_smart_layout, calculate_fullscreen_corner_rects

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

    def load_zones(self, zones=None):
        if zones is not None:
            self.zones = zones
        else:
            config = load_config(CONFIG_PATH)
            primary_screen = QApplication.primaryScreen()
            if primary_screen:
                screen_geo = primary_screen.geometry()
                screen_w, screen_h = screen_geo.width(), screen_geo.height()
            else:
                screen_w, screen_h = get_screen_resolution()

            mode = config.get("mode", "3_window")
            if mode == "fullscreen_corner":
                corner_settings = config.get("corner_settings", {})
                media_profiles = config.get("layout_settings", {}).get("media_profiles", {})
                self.zones = calculate_fullscreen_corner_rects(corner_settings, media_profiles, screen_w, screen_h)
            else:
                open_wins = get_open_windows()
                self.zones = calculate_smart_layout(config, screen_w, screen_h, open_windows=open_wins)

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
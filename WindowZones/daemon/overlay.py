from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen

try:
    from ..core.config import CONFIG_PATH, load_config
    from ..core.win_utils import (
        get_open_windows,
        get_primary_monitor_info,
        get_screen_resolution,
        get_screen_work_area,
    )
    from ..core.layout_engine import calculate_smart_layout, calculate_fullscreen_corner_rects
except (ImportError, ValueError):
    from core.config import CONFIG_PATH, load_config
    from core.win_utils import (
        get_open_windows,
        get_primary_monitor_info,
        get_screen_resolution,
        get_screen_work_area,
    )
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
        self.monitor_rect_phys = (0, 0, 1920, 1080)

    def _find_qscreen_for_device(self, device_name):
        if device_name:
            for scr in QApplication.screens():
                if scr.name() == device_name:
                    return scr
        return QApplication.primaryScreen()

    def load_zones(self, zones=None, monitor_info=None):
        if monitor_info is None:
            monitor_info = get_primary_monitor_info()

        origin_x, origin_y, screen_w, screen_h = monitor_info["work"]
        self.monitor_rect_phys = monitor_info["monitor"]
        target_screen = self._find_qscreen_for_device(monitor_info.get("device"))

        if zones is not None:
            self.zones = zones
        else:
            config = load_config(CONFIG_PATH)
            mode = config.get("mode", "3_window")
            if mode == "fullscreen_corner":
                corner_settings = config.get("corner_settings", {})
                media_profiles = config.get("layout_settings", {}).get("media_profiles", {})
                self.zones = calculate_fullscreen_corner_rects(
                    corner_settings, media_profiles, screen_w, screen_h,
                    origin_x=origin_x, origin_y=origin_y
                )
            else:
                open_wins = get_open_windows()
                self.zones = calculate_smart_layout(
                    config, screen_w, screen_h, open_windows=open_wins,
                    origin_x=origin_x, origin_y=origin_y
                )

        if target_screen:
            self.setGeometry(target_screen.geometry())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dim background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        mx, my, mw, mh = self.monitor_rect_phys
        sx = (self.width() / float(mw)) if mw > 0 else 1.0
        sy = (self.height() / float(mh)) if mh > 0 else 1.0

        # Draw non-hovered zones first, then hovered zone last so its highlight is never covered
        draw_order = [i for i in range(len(self.zones)) if i != self.hovered_zone_idx]
        if 0 <= self.hovered_zone_idx < len(self.zones):
            draw_order.append(self.hovered_zone_idx)

        for i in draw_order:
            z = self.zones[i]
            rect = z.get("rect")
            if not rect:
                continue

            lx = int(round((rect["x"] - mx) * sx))
            ly = int(round((rect["y"] - my) * sy))
            lw = int(round(rect["width"] * sx))
            lh = int(round(rect["height"] * sy))
            if lw <= 0 or lh <= 0:
                continue

            zr = QRect(lx, ly, lw, lh)

            # Draw Zone
            if i == self.hovered_zone_idx:
                painter.setBrush(QColor(0, 120, 212, 140))
                painter.setPen(QPen(QColor(0, 120, 212, 255), 3))
            else:
                painter.setBrush(QColor(255, 255, 255, 30))
                painter.setPen(QPen(QColor(255, 255, 255, 150), 2))

            pad = min(6, max(0, min(lw, lh) // 4))
            zr.adjust(pad, pad, -pad, -pad)
            painter.drawRoundedRect(zr, 8, 8)

            # Draw zone number
            painter.setPen(QColor(255, 255, 255, 255))
            font = painter.font()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(zr, Qt.AlignmentFlag.AlignCenter, str(i + 1))
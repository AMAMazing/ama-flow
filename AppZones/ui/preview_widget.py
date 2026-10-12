from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

ZONE_PALETTE = [
    {"bg": QColor(10, 132, 255, 60), "border": QColor(10, 132, 255, 230), "accent": "#0a84ff", "text": "#ffffff"},
    {"bg": QColor(48, 209, 88, 60),  "border": QColor(48, 209, 88, 230),  "accent": "#30d158", "text": "#ffffff"},
    {"bg": QColor(255, 159, 10, 60), "border": QColor(255, 159, 10, 230), "accent": "#ff9f0a", "text": "#ffffff"},
    {"bg": QColor(191, 90, 242, 60), "border": QColor(191, 90, 242, 230), "accent": "#bf5af2", "text": "#ffffff"},
    {"bg": QColor(100, 210, 255, 60), "border": QColor(100, 210, 255, 230), "accent": "#64d2ff", "text": "#ffffff"}
]

class LiveLayoutPreview(QWidget):
    """
    Embedded live canvas rendering a scaled mini-map of the workspace layout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.zones = []
        self.screen_w = 1920
        self.screen_h = 1080

    def update_layout(self, zones, screen_w, screen_h):
        self.zones = zones or []
        self.screen_w = max(100, screen_w)
        self.screen_h = max(100, screen_h)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Compute monitor canvas bounds preserving screen aspect ratio
        screen_aspect = self.screen_w / float(self.screen_h)
        pad = 12

        avail_w = w - (pad * 2)
        avail_h = h - (pad * 2)

        if avail_w / float(avail_h) > screen_aspect:
            canvas_h = avail_h
            canvas_w = int(canvas_h * screen_aspect)
        else:
            canvas_w = avail_w
            canvas_h = int(canvas_w / screen_aspect)

        canvas_x = (w - canvas_w) / 2.0
        canvas_y = (h - canvas_h) / 2.0

        canvas_rect = QRectF(canvas_x, canvas_y, canvas_w, canvas_h)

        # Draw monitor background
        painter.setBrush(QColor(18, 18, 22))
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1.5))
        painter.drawRoundedRect(canvas_rect, 10, 10)

        if not self.zones:
            painter.setPen(QColor(142, 142, 147))
            painter.setFont(QFont("-apple-system, Segoe UI", 10))
            painter.drawText(canvas_rect, Qt.AlignmentFlag.AlignCenter, "No Active Layout")
            return

        scale_x = canvas_w / float(self.screen_w)
        scale_y = canvas_h / float(self.screen_h)

        # Draw zones
        for idx, zone in enumerate(self.zones):
            rect = zone.get("rect")
            if not rect:
                continue

            zx = canvas_x + (rect.get("x", 0) * scale_x)
            zy = canvas_y + (rect.get("y", 0) * scale_y)
            zw = rect.get("width", 0) * scale_x
            zh = rect.get("height", 0) * scale_y

            z_rect = QRectF(zx, zy, zw, zh)
            # Add minor padding between zones
            z_rect.adjust(3, 3, -3, -3)

            style = ZONE_PALETTE[idx % len(ZONE_PALETTE)]

            # Background and border
            painter.setBrush(style["bg"])
            painter.setPen(QPen(style["border"], 1.5))
            painter.drawRoundedRect(z_rect, 8, 8)

            # Zone Labeling
            title = zone.get("window_title", f"Zone {idx + 1}")
            pos = zone.get("pos", "")
            role = zone.get("role", "")

            # Display short title
            short_title = title
            if "visual studio code" in title.lower():
                short_title = "VS Code"
            elif "google chrome" in title.lower():
                short_title = "Chrome"
            elif len(short_title) > 22:
                short_title = short_title[:19] + "..."

            painter.setPen(QColor(style["text"]))
            painter.setFont(QFont("-apple-system, Segoe UI", 9, QFont.Weight.Bold))
            title_box = QRectF(z_rect.x() + 6, z_rect.y() + 6, max(10, z_rect.width() - 12), 18)
            painter.drawText(title_box, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, short_title)

            # Center dimension / aspect info
            dim_str = f"{rect.get('width', 0)}x{rect.get('height', 0)}"
            if zone.get("val") and ":" in str(zone.get("val")):
                dim_str += f" ({zone.get('val')})"
            elif pos:
                dim_str += f" ({pos})"

            painter.setPen(QColor(style["accent"]))
            painter.setFont(QFont("-apple-system, Segoe UI", 8))
            dim_box = QRectF(z_rect.x() + 6, z_rect.y() + (z_rect.height() / 2.0) - 10, max(10, z_rect.width() - 12), 20)
            painter.drawText(dim_box, Qt.AlignmentFlag.AlignCenter, dim_str)
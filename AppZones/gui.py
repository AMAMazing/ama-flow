import sys
import json
import os
import subprocess
import win32gui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QLineEdit, QScrollArea, QFrame, QDialog, QListWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
MAIN_SCRIPT = os.path.join(os.path.dirname(__file__), "main.py")

STYLESHEET = """
QMainWindow, QScrollArea, QWidget#scroll_content {
    background-color: #09090b;
}
QFrame#glass {
    background-color: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
QComboBox, QLineEdit {
    background-color: rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 10px;
    color: #f4f4f5;
    font-size: 14px;
}
QComboBox:focus, QLineEdit:focus {
    border: 1px solid #3b82f6;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #18181b;
    color: white;
    selection-background-color: #3b82f6;
    border-radius: 6px;
}
QPushButton {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f4f4f5;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
QPushButton#primary { background-color: #3b82f6; border: none; }
QPushButton#primary:hover { background-color: #2563eb; }
QPushButton#danger { background-color: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; }
QPushButton#danger:hover { background-color: rgba(239, 68, 68, 0.4); }
QLabel { color: #f4f4f5; font-size: 14px; }
QLabel#title { font-size: 28px; font-weight: 800; color: #ffffff; }
QLabel#subtitle { font-size: 14px; color: #a1a1aa; }
QDialog { background-color: #09090b; }
QListWidget {
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    padding: 8px;
    color: #e0e0e0;
    font-size: 14px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
QListWidget::item { padding: 12px; border-radius: 6px; }
QListWidget::item:hover { background-color: rgba(255, 255, 255, 0.05); }
QListWidget::item:selected { background-color: #3b82f6; color: white; }
"""

class NoWheelComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()

def get_open_windows():
    windows = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title: windows.append(title)
        return True
    try: win32gui.EnumWindows(callback, None)
    except: pass
    junk = ["Program Manager", "Settings", "Microsoft Text Input Application"]
    return sorted([w for w in set(windows) if w not in junk])

class AppSelectDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Select Open Application")
        self.setMinimumSize(400, 500)
        layout = QVBoxLayout(self)
        
        self.list = QListWidget()
        for w in get_open_windows():
            self.list.addItem(w)
        layout.addWidget(self.list)
        
        btn = QPushButton("Select")
        btn.setObjectName("primary")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        
    def get_selected(self):
        if self.list.currentItem():
            return self.list.currentItem().text()
        return ""

class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.zones = []
        self.screen_rect = (1920, 1080)

    def update_zones(self, zones, screen_rect):
        self.zones = zones
        self.screen_rect = (screen_rect.width(), screen_rect.height())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        sw, sh = self.screen_rect
        if sw == 0 or sh == 0: return

        scale = min(w / sw, h / sh) * 0.9
        pw = int(sw * scale)
        ph = int(sh * scale)
        px = (w - pw) // 2
        py = (h - ph) // 2

        painter.setBrush(QColor("#000000"))
        painter.setPen(QPen(QColor("#3f3f46"), 4))
        painter.drawRoundedRect(px - 4, py - 4, pw + 8, ph + 8, 8, 8)
        
        painter.setBrush(QColor("#18181b"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(px, py, pw, ph)

        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
        
        for i, z in enumerate(self.zones):
            rect = z.get('rect')
            if not rect: continue
            
            zx = px + int(rect['x'] * scale)
            zy = py + int(rect['y'] * scale)
            zw = int(rect['width'] * scale)
            zh = int(rect['height'] * scale)

            c = QColor(colors[i % len(colors)])
            c.setAlpha(80)
            painter.setBrush(c)
            c.setAlpha(255)
            painter.setPen(QPen(c, 2))
            painter.drawRect(zx, zy, zw, zh)
            
            painter.setPen(QColor("#ffffff"))
            title = z.get('window_title', '')
            painter.drawText(zx, zy, zw, zh, Qt.AlignmentFlag.AlignCenter, title)

class ZoneRow(QFrame):
    def __init__(self, parent, delete_callback, change_callback, initial_data=None):
        super().__init__(parent)
        self.setObjectName("glass")
        self.delete_callback = delete_callback
        self.change_callback = change_callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        row1 = QHBoxLayout()
        self.btn_select = QPushButton("Pick Open App")
        self.btn_select.clicked.connect(self.select_app)
        self.app_match = QLineEdit()
        self.app_match.setPlaceholderText("Window Title Substring (e.g. 'Netflix' or 'Code')")
        btn_del = QPushButton("X")
        btn_del.setObjectName("danger")
        btn_del.setFixedWidth(40)
        btn_del.clicked.connect(lambda: self.delete_callback(self))
        
        row1.addWidget(self.btn_select)
        row1.addWidget(self.app_match, 1)
        row1.addWidget(btn_del)
        
        row2 = QHBoxLayout()
        self.pos_combo = NoWheelComboBox()
        self.pos_combo.addItems(["Left", "Right", "Top", "Bottom", "Top-Left", "Bottom-Left", "Top-Right", "Bottom-Right", "Fill Space"])
        self.pos_combo.setMinimumWidth(150)
        
        self.rule_combo = NoWheelComboBox()
        self.rule_combo.addItems(["Fill (Any)", "Aspect Ratio", "Width (px)", "Height (px)", "Width (%)", "Height (%)"])
        self.rule_combo.setMinimumWidth(150)
        self.rule_combo.currentTextChanged.connect(self.on_rule_changed)
        
        self.val_input = QLineEdit()
        self.val_input.setPlaceholderText("Value (e.g. 16:9 or 40)")
        self.val_input.setMinimumWidth(150)
        
        row2.addWidget(QLabel("Location:"))
        row2.addWidget(self.pos_combo)
        row2.addWidget(QLabel(" Rule:"))
        row2.addWidget(self.rule_combo)
        row2.addWidget(self.val_input)
        row2.addStretch()
        
        layout.addLayout(row1)
        layout.addLayout(row2)
        
        if initial_data:
            self.app_match.setText(initial_data.get("window_title", ""))
            self.pos_combo.setCurrentText(initial_data.get("pos", "Left"))
            self.rule_combo.setCurrentText(initial_data.get("stat", "Fill (Any)"))
            self.val_input.setText(initial_data.get("val", ""))
            
        self.val_input.setVisible(self.rule_combo.currentText() != "Fill (Any)")
        self._initialized = True

        self.app_match.textChanged.connect(lambda _: self.trigger_change())
        self.pos_combo.currentTextChanged.connect(lambda _: self.trigger_change())
        self.val_input.textChanged.connect(lambda _: self.trigger_change())

    def trigger_change(self):
        if hasattr(self, '_initialized') and self._initialized:
            self.change_callback()

    def select_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                # Grab the main application name instead of specific tab
                title = selected.split(" - ")[-1]
                self.app_match.setText(title)
                self.trigger_change()

    def on_rule_changed(self, text):
        self.val_input.setVisible(text != "Fill (Any)")
        self.trigger_change()

    def get_data(self):
        return {
            "window_title": self.app_match.text().strip(),
            "pos": self.pos_combo.currentText(),
            "stat": self.rule_combo.currentText(),
            "val": self.val_input.text().strip()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppZones - Minimalist Auto-Layout")
        self.resize(800, 800)
        self.setStyleSheet(STYLESHEET)
        self.rows = []
        
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        header = QVBoxLayout()
        title = QLabel("AppZones"); title.setObjectName("title")
        sub = QLabel("1 Rule Per App. The solver calculates the exact pixel placements for you."); sub.setObjectName("subtitle")
        header.addWidget(title)
        header.addWidget(sub)
        main_layout.addLayout(header)
        
        self.preview = PreviewWidget()
        main_layout.addWidget(self.preview)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.rows_layout = QVBoxLayout(self.scroll_content)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rows_layout.setSpacing(15)
        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll)
        
        footer = QHBoxLayout()
        btn_add = QPushButton("+ Add App")
        btn_add.clicked.connect(lambda: self.add_row())
        
        btn_apply = QPushButton("Calculate & Snap Layout")
        btn_apply.setObjectName("primary")
        btn_apply.setMinimumHeight(45)
        btn_apply.clicked.connect(self.apply_layout)
        
        footer.addWidget(btn_add)
        footer.addStretch()
        footer.addWidget(btn_apply)
        main_layout.addLayout(footer)

    def add_row(self, data=None):
        row = ZoneRow(self.scroll_content, self.delete_row, self.update_preview, data)
        self.rows.append(row)
        self.rows_layout.addWidget(row)
        self.update_preview()

    def delete_row(self, row):
        self.rows.remove(row)
        row.deleteLater()
        self.update_preview()

    def load_config(self):
        loaded = False
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                    for z in config.get("zones", []):
                        self.add_row(z)
                        loaded = True
            except: pass
            
        if not loaded:
            self.add_row({"window_title": "Code", "pos": "Right", "stat": "Width (%)", "val": "40"})
            self.add_row({"window_title": "Netflix", "pos": "Bottom-Left", "stat": "Aspect Ratio", "val": "16:9"})
            self.add_row({"window_title": "Chrome", "pos": "Fill Space", "stat": "Fill (Any)", "val": ""})
            
        self.update_preview()

    def update_preview(self):
        zones_data = []
        for row in self.rows:
            data = row.get_data()
            if not data["window_title"]:
                data["window_title"] = "Empty"
            zones_data.append(data)
            
        screen = self.screen().geometry()
        zones_data = self.calculate_rects(zones_data, screen.width(), screen.height())
        self.preview.update_zones(zones_data, screen)

    def calculate_rects(self, zones, screen_w, screen_h):
        rem_x, rem_y, rem_w, rem_h = 0, 0, screen_w, screen_h

        def get_val(z, max_val, is_width=True):
            stat = z.get('stat', '')
            val = z.get('val', '0')
            try:
                if stat == "Width (px)" and is_width: return int(val)
                if stat == "Height (px)" and not is_width: return int(val)
                if stat == "Width (%)" and is_width: return int(max_val * float(val) / 100.0)
                if stat == "Height (%)" and not is_width: return int(max_val * float(val) / 100.0)
            except: pass
            return 0

        # Pass 1: Sides
        for z in zones:
            pos = z.get('pos', '')
            stat = z.get('stat', '')
            if pos == "Fill Space" or stat == "Fill (Any)": continue
            
            if pos == "Right" or pos == "Left":
                if stat == "Aspect Ratio":
                    try:
                        val = z.get('val', '').replace(':', '/')
                        num, den = map(float, val.split('/'))
                        w = int(rem_h * num / den)
                    except:
                        w = int(rem_h * 16 / 9)
                else:
                    w = get_val(z, rem_w, True) or (rem_w // 2)
                
                if pos == "Right":
                    z['rect'] = {"x": rem_x + rem_w - w, "y": rem_y, "width": w, "height": rem_h}
                    rem_w = max(0, rem_w - w)
                else:
                    z['rect'] = {"x": rem_x, "y": rem_y, "width": w, "height": rem_h}
                    rem_x += w
                    rem_w = max(0, rem_w - w)
                    
            elif pos == "Top" or pos == "Bottom":
                if stat == "Aspect Ratio":
                    try:
                        val = z.get('val', '').replace(':', '/')
                        num, den = map(float, val.split('/'))
                        h = int(rem_w * den / num)
                    except:
                        h = int(rem_w * 9 / 16)
                else:
                    h = get_val(z, rem_h, False) or (rem_h // 2)
                    
                if pos == "Top":
                    z['rect'] = {"x": rem_x, "y": rem_y, "width": rem_w, "height": h}
                    rem_y += h
                    rem_h = max(0, rem_h - h)
                else:
                    z['rect'] = {"x": rem_x, "y": rem_y + rem_h - h, "width": rem_w, "height": h}
                    rem_h = max(0, rem_h - h)

        # Pass 2: Corners
        for z in zones:
            pos = z.get('pos', '')
            stat = z.get('stat', '')
            if pos == "Fill Space" or stat == "Fill (Any)": continue
            
            if pos in ["Top-Left", "Bottom-Left", "Top-Right", "Bottom-Right"]:
                w = rem_w
                h = 0
                val = z.get('val', '')
                if stat == "Aspect Ratio":
                    try:
                        val = val.replace(':', '/')
                        num, den = map(float, val.split('/'))
                        h = int(w * den / num)
                    except:
                        h = int(w * 9 / 16)
                else:
                    h = get_val(z, rem_h, False) or (rem_h // 2)

                if pos == "Bottom-Left":
                    z['rect'] = {"x": rem_x, "y": rem_y + rem_h - h, "width": w, "height": h}
                    rem_h = max(0, rem_h - h)
                elif pos == "Bottom-Right":
                    z['rect'] = {"x": rem_x + rem_w - w, "y": rem_y + rem_h - h, "width": w, "height": h}
                    rem_h = max(0, rem_h - h)
                elif pos == "Top-Left":
                    z['rect'] = {"x": rem_x, "y": rem_y, "width": w, "height": h}
                    rem_y += h
                    rem_h = max(0, rem_h - h)
                elif pos == "Top-Right":
                    z['rect'] = {"x": rem_x + rem_w - w, "y": rem_y, "width": w, "height": h}
                    rem_y += h
                    rem_h = max(0, rem_h - h)

        # Pass 3: Fill
        for z in zones:
            if z.get('pos') == "Fill Space" or z.get('stat') == "Fill (Any)" or 'rect' not in z:
                z['rect'] = {"x": rem_x, "y": rem_y, "width": rem_w, "height": rem_h}

        return zones

    def apply_layout(self):
        zones_data = []
        for row in self.rows:
            data = row.get_data()
            if data["window_title"]:
                zones_data.append(data)
            
        screen = self.screen().geometry()
        zones_data = self.calculate_rects(zones_data, screen.width(), screen.height())
        
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"zones": zones_data}, f, indent=2)
            
        try:
            subprocess.Popen([sys.executable, MAIN_SCRIPT], shell=False)
        except Exception as e:
            print(f"Failed to launch: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
import sys
import json
import os
import math
import re
import subprocess
import ctypes
from ctypes import wintypes
import win32gui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QLineEdit, QScrollArea, QFrame, QDialog, QListWidget,
                             QInputDialog, QMessageBox, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
MAIN_SCRIPT = os.path.join(os.path.dirname(__file__), "main.py")

STYLESHEET = """
QMainWindow {
    background-color: #202020;
}
QWidget#central {
    background-color: #202020;
}
QScrollArea, QWidget#scroll_content {
    background-color: transparent;
    border: none;
}

/* PowerToys Cards */
QFrame#card {
    background-color: #2b2b2b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
}
QFrame#card:hover {
    border: 1px solid rgba(255, 255, 255, 0.14);
}

QFrame#monitor_card {
    background-color: #2b2b2b;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 8px;
    padding: 6px 14px;
}

/* Typography */
QLabel {
    color: #ffffff;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel#section_title {
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
    padding-bottom: 2px;
}
QLabel#header_title {
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
}
QLabel#subtitle {
    font-size: 12px;
    color: #9d9d9d;
}
QLabel#field_label {
    font-size: 12px;
    color: #a0a0a0;
    font-weight: 500;
}
QLabel#zone_num {
    background-color: rgba(255, 255, 255, 0.08);
    color: #ffffff;
    font-weight: 600;
    font-size: 12px;
    border-radius: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    qproperty-alignment: AlignCenter;
}

/* Inputs & Dropdowns */
QComboBox, QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 13px;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
}
QComboBox:hover, QLineEdit:hover {
    background-color: #242424;
    border: 1px solid rgba(255, 255, 255, 0.20);
}
QComboBox:focus, QLineEdit:focus {
    background-color: #1e1e1e;
    border: 1px solid #0078d4;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #a0a0a0;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    color: #ffffff;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* Buttons */
QPushButton {
    background-color: #323232;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 500;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
}
QPushButton:hover {
    background-color: #3c3c3c;
    border: 1px solid rgba(255, 255, 255, 0.16);
}
QPushButton:pressed {
    background-color: #292929;
}

QPushButton#primary {
    background-color: #0078d4;
    border: 1px solid #1084d9;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primary:hover {
    background-color: #1084d9;
    border: 1px solid #2993e3;
}
QPushButton#primary:pressed {
    background-color: #006cbe;
}

QPushButton#danger {
    background-color: transparent;
    color: #a0a0a0;
    border: 1px solid transparent;
    border-radius: 6px;
    font-size: 13px;
    padding: 4px 8px;
}
QPushButton#danger:hover {
    background-color: rgba(232, 17, 35, 0.15);
    color: #f87171;
    border: 1px solid rgba(232, 17, 35, 0.3);
}

QPushButton#secondary_action {
    background-color: transparent;
    border: 1px solid rgba(255, 255, 255, 0.12);
}
QPushButton#secondary_action:hover {
    background-color: rgba(255, 255, 255, 0.06);
}

/* Dialog */
QDialog {
    background-color: #202020;
}
QListWidget {
    background-color: #1e1e1e;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px;
    color: #ffffff;
    font-size: 13px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 4px;
}
QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.06);
}
QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.2);
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.35);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
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
            if title:
                windows.append((title, hwnd))
        return True
    try:
        win32gui.EnumWindows(callback, None)
    except:
        pass
    junk = ["Program Manager", "Settings", "Microsoft Text Input Application"]
    seen = set()
    cleaned = []
    for title, hwnd in windows:
        if title not in junk and title not in seen:
            seen.add(title)
            cleaned.append((title, hwnd))
    return sorted(cleaned, key=lambda x: x[0].lower())

def get_window_dimensions(hwnd):
    try:
        class RECT(ctypes.Structure):
            _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]
        fr = RECT()
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(fr), ctypes.sizeof(fr)) == 0:
            w = fr.right - fr.left
            h = fr.bottom - fr.top
        else:
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
        return max(0, w), max(0, h)
    except Exception:
        try:
            rect = win32gui.GetWindowRect(hwnd)
            return max(0, rect[2] - rect[0]), max(0, rect[3] - rect[1])
        except Exception:
            return 0, 0

def calculate_window_aspect_ratio(hwnd):
    try:
        w, h = get_window_dimensions(hwnd)
        if w <= 0 or h <= 0:
            return None, 0, 0
        common_ratios = [
            (16, 9), (4, 3), (21, 9), (16, 10), (3, 2),
            (1, 1), (9, 16), (3, 4), (18, 9), (32, 9)
        ]
        target_ratio = w / h
        best_match = None
        best_diff = float("inf")
        for num, den in common_ratios:
            diff = abs((num / den) - target_ratio)
            if diff < best_diff and diff < 0.05:
                best_diff = diff
                best_match = f"{num}:{den}"
        if best_match:
            return best_match, w, h
        divisor = math.gcd(w, h)
        if divisor > 10:
            sim_w = w // divisor
            sim_h = h // divisor
            if sim_w < 100 and sim_h < 100:
                return f"{sim_w}:{sim_h}", w, h
        return f"{round(target_ratio, 2)}:1", w, h
    except:
        return None, 0, 0

class AppSelectDialog(QDialog):
    def __init__(self, parent, return_hwnd=False):
        super().__init__(parent)
        self.return_hwnd = return_hwnd
        self.selected_hwnd = None
        self.setWindowTitle("Select Open Application")
        self.setMinimumSize(460, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel("Choose a running window:")
        lbl.setObjectName("subtitle")
        layout.addWidget(lbl)

        self.list = QListWidget()
        self.window_items = get_open_windows()
        for title, hwnd in self.window_items:
            self.list.addItem(title)
        layout.addWidget(self.list)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_select = QPushButton("Select")
        btn_select.setObjectName("primary")
        btn_select.clicked.connect(self.on_select)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_select)
        layout.addLayout(btn_box)

    def on_select(self):
        idx = self.list.currentRow()
        if idx >= 0 and idx < len(self.window_items):
            self.selected_hwnd = self.window_items[idx][1]
            self.accept()
        else:
            self.reject()

    def get_selected(self):
        if self.list.currentItem():
            return self.list.currentItem().text()
        return ""

class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(240)
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
        if sw == 0 or sh == 0:
            return

        scale = min((w - 40) / sw, (h - 30) / sh)
        pw = int(sw * scale)
        ph = int(sh * scale)
        px = (w - pw) // 2
        py = (h - ph) // 2

        # Monitor Bezel
        painter.setBrush(QColor("#181818"))
        painter.setPen(QPen(QColor("#383838"), 1))
        painter.drawRoundedRect(px - 6, py - 6, pw + 12, ph + 12, 8, 8)

        # Monitor Screen Canvas
        painter.setBrush(QColor("#242424"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(px, py, pw, ph, 4, 4)

        palette = [
            (QColor("#1e3a5f"), QColor("#3b82f6")),
            (QColor("#2d3748"), QColor("#818cf8")),
            (QColor("#1e3f3b"), QColor("#10b981")),
            (QColor("#452e2e"), QColor("#f87171")),
            (QColor("#3f2d4f"), QColor("#c084fc")),
            (QColor("#423821"), QColor("#fbbf24")),
        ]

        for i, z in enumerate(self.zones):
            rect = z.get("rect")
            if not rect:
                continue

            zx = px + int(rect["x"] * scale)
            zy = py + int(rect["y"] * scale)
            zw = int(rect["width"] * scale)
            zh = int(rect["height"] * scale)

            fill_c, border_c = palette[i % len(palette)]

            # If overlapping, use slight transparency so underlying window is recognizable
            fill_c = QColor(fill_c.red(), fill_c.green(), fill_c.blue(), 210)

            gap = 2
            rx = zx + gap
            ry = zy + gap
            rw = max(1, zw - gap * 2)
            rh = max(1, zh - gap * 2)

            painter.setBrush(fill_c)
            painter.setPen(QPen(border_c, 1.5))
            painter.drawRoundedRect(rx, ry, rw, rh, 4, 4)

            # Badge
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 160))
            painter.drawRoundedRect(rx + 6, ry + 6, 20, 18, 3, 3)
            painter.setPen(QColor("#ffffff"))
            font_small = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font_small)
            painter.drawText(rx + 6, ry + 6, 20, 18, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            # Title and dimension text
            title = z.get("window_title", "")
            real_w, real_h = int(rect["width"]), int(rect["height"])
            display_text = f"{title}\n{real_w} × {real_h} px"

            font_body = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
            painter.setFont(font_body)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(rx + 10, ry + 10, rw - 20, rh - 20, Qt.AlignmentFlag.AlignCenter, display_text)

class ZoneRow(QFrame):
    def __init__(self, parent, delete_callback, change_callback, index=1, initial_data=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.delete_callback = delete_callback
        self.change_callback = change_callback
        self.index = index
        self.role = (initial_data or {}).get("role", "")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.num_badge = QLabel(str(self.index))
        self.num_badge.setObjectName("zone_num")
        top_row.addWidget(self.num_badge)

        self.app_match = QLineEdit()
        self.app_match.setPlaceholderText("Window Title Substring (e.g. Visual Studio Code, Chrome, MYAEW)")
        top_row.addWidget(self.app_match, 1)

        self.btn_select = QPushButton("Pick App...")
        self.btn_select.setObjectName("secondary_action")
        self.btn_select.clicked.connect(self.select_app)
        top_row.addWidget(self.btn_select)

        btn_del = QPushButton("✕")
        btn_del.setObjectName("danger")
        btn_del.setToolTip("Delete this zone")
        btn_del.setFixedWidth(32)
        btn_del.clicked.connect(lambda: self.delete_callback(self))
        top_row.addWidget(btn_del)

        layout.addLayout(top_row)

        bot_row = QHBoxLayout()
        bot_row.setSpacing(10)

        lbl_loc = QLabel("Location:")
        lbl_loc.setObjectName("field_label")
        bot_row.addWidget(lbl_loc)

        self.pos_combo = NoWheelComboBox()
        self.pos_combo.addItems(["Left", "Right", "Top", "Bottom", "Top-Left", "Bottom-Left", "Top-Right", "Bottom-Right", "Fill Space"])
        self.pos_combo.setMinimumWidth(130)
        self.pos_combo.currentTextChanged.connect(self.on_pos_changed)
        bot_row.addWidget(self.pos_combo)

        lbl_rule = QLabel("Rule:")
        lbl_rule.setObjectName("field_label")
        bot_row.addWidget(lbl_rule)

        self.rule_combo = NoWheelComboBox()
        self.rule_combo.addItems([
            "Fill (Any)",
            "Aspect Ratio",
            "Aspect Ratio (Maximize)",
            "Aspect Ratio (Equal)",
            "Min Height (px)",
            "Height (px)",
            "Width (px)",
            "Height (%)",
            "Width (%)"
        ])
        self.rule_combo.setMinimumWidth(160)
        self.rule_combo.currentTextChanged.connect(self.on_rule_changed)
        bot_row.addWidget(self.rule_combo)

        self.val_input = QLineEdit()
        self.val_input.setPlaceholderText("Value (e.g. 16:9 or 432)")
        self.val_input.setMinimumWidth(140)
        bot_row.addWidget(self.val_input)

        bot_row.addStretch()
        layout.addLayout(bot_row)

        if initial_data:
            self.app_match.setText(initial_data.get("window_title", ""))
            self.pos_combo.setCurrentText(initial_data.get("pos", "Left"))
            self.rule_combo.setCurrentText(initial_data.get("stat", "Fill (Any)"))
            self.val_input.setText(str(initial_data.get("val", "")))

        self.update_visibility()
        self._initialized = True

        self.app_match.textChanged.connect(lambda _: self.trigger_change())
        self.pos_combo.currentTextChanged.connect(lambda _: self.trigger_change())
        self.rule_combo.currentTextChanged.connect(lambda _: self.trigger_change())
        self.val_input.textChanged.connect(lambda _: self.trigger_change())

    def set_index(self, idx):
        self.index = idx
        self.num_badge.setText(str(idx))

    def update_visibility(self):
        is_fill = (self.pos_combo.currentText() == "Fill Space" or self.rule_combo.currentText() == "Fill (Any)")
        self.val_input.setVisible(not is_fill)

    def trigger_change(self):
        if hasattr(self, "_initialized") and self._initialized:
            self.change_callback()

    def select_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.app_match.setText(title)
                self.trigger_change()

    def on_pos_changed(self, text):
        self.update_visibility()
        self.trigger_change()

    def on_rule_changed(self, text):
        self.update_visibility()
        self.trigger_change()

    def get_data(self):
        return {
            "window_title": self.app_match.text().strip(),
            "role": self.role,
            "pos": self.pos_combo.currentText(),
            "stat": self.rule_combo.currentText(),
            "val": self.val_input.text().strip()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppZones - FancyZones Auto-Layout")
        self.resize(960, 780)
        self.setStyleSheet(STYLESHEET)

        self.active_mode = "3_window"
        self.rows = []
        self.chrome_sizes = {
            "Equal Size": "equal",
            "432px": "432"
        }
        self.media_profiles = {
            "16:9 (PiP)": "16:9",
            "4:3 (Classic)": "4:3",
            "21:9 (Ultrawide)": "21:9",
            "1:1 (Square)": "1:1",
            "MYAEW": "16:9"
        }
        self.layout_settings = {
            "vscode_side": "Right",
            "chrome_sizing": "Equal Size",
            "active_media_profile": "16:9 (PiP)"
        }
        self.corner_settings = {
            "fullscreen_app": "",
            "media_app": "Netflix",
            "corner": "Bottom-Right",
            "max_width": 720,
            "max_height": 450,
            "active_media_profile": "16:9 (PiP)"
        }
        self._updating_controls = False

        self.init_ui()
        self.load_config()

    def init_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Area
        header = QHBoxLayout()
        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)
        title = QLabel("AppZones")
        title.setObjectName("header_title")
        sub = QLabel("Automated PowerToys window placement solver")
        sub.setObjectName("subtitle")
        titles_box.addWidget(title)
        titles_box.addWidget(sub)
        header.addLayout(titles_box)
        header.addStretch()

        self.monitor_card = QFrame()
        self.monitor_card.setObjectName("monitor_card")
        mon_layout = QVBoxLayout(self.monitor_card)
        mon_layout.setContentsMargins(12, 6, 12, 6)
        mon_layout.setSpacing(2)

        self.mon_num_label = QLabel("Display 1")
        self.mon_num_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.mon_num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        screen = self.screen().geometry()
        self.mon_res_label = QLabel(f"{screen.width()} × {screen.height()}")
        self.mon_res_label.setObjectName("subtitle")
        self.mon_res_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mon_layout.addWidget(self.mon_num_label)
        mon_layout.addWidget(self.mon_res_label)
        header.addWidget(self.monitor_card)
        main_layout.addLayout(header)

        # Mode Selection Bar Card
        mode_card = QFrame()
        mode_card.setObjectName("card")
        mode_layout = QHBoxLayout(mode_card)
        mode_layout.setContentsMargins(16, 10, 16, 10)
        mode_layout.setSpacing(12)

        lbl_mode = QLabel("Layout Mode:")
        lbl_mode.setObjectName("field_label")
        mode_layout.addWidget(lbl_mode)

        self.mode_combo = NoWheelComboBox()
        self.mode_combo.addItem("3-Window Layout (Code + Chrome + Media)", "3_window")
        self.mode_combo.addItem("Fullscreen + Corner Media", "fullscreen_corner")
        self.mode_combo.setMinimumWidth(320)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()

        main_layout.addWidget(mode_card)

        # Dynamic Controls Stack (Switches depending on layout mode)
        self.controls_stack = QStackedWidget()

        # Page 0: 3-Window Layout Control Card
        ctrl_card_3win = QFrame()
        ctrl_card_3win.setObjectName("card")
        ctrl_layout_3win = QVBoxLayout(ctrl_card_3win)
        ctrl_layout_3win.setContentsMargins(16, 14, 16, 14)
        ctrl_layout_3win.setSpacing(12)

        # Row 1: VS Code Side & Chrome Sizing
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        lbl_side = QLabel("VS Code Side:")
        lbl_side.setObjectName("field_label")
        row1.addWidget(lbl_side)

        self.vscode_side_combo = NoWheelComboBox()
        self.vscode_side_combo.addItems(["Right", "Left"])
        self.vscode_side_combo.setToolTip("Set VS Code to Left or Right side. Chrome and Media will adapt on the opposite side.")
        self.vscode_side_combo.currentTextChanged.connect(self.on_vscode_side_changed)
        row1.addWidget(self.vscode_side_combo)

        lbl_chrome = QLabel("Google Chrome Sizing:")
        lbl_chrome.setObjectName("field_label")
        row1.addWidget(lbl_chrome)

        self.chrome_sizing_combo = NoWheelComboBox()
        self.chrome_sizing_combo.setMinimumWidth(130)
        self.chrome_sizing_combo.setToolTip("Equal Size: Chrome and Media split height equally.\nCustom Size: User-defined height in pixels or percentage.")
        self.chrome_sizing_combo.currentTextChanged.connect(self.on_chrome_sizing_changed)
        row1.addWidget(self.chrome_sizing_combo)

        btn_detect_chrome = QPushButton("📷 Save Current Chrome Size...")
        btn_detect_chrome.setObjectName("secondary_action")
        btn_detect_chrome.setToolTip("Inspect a running window and automatically calculate and save its height for Chrome")
        btn_detect_chrome.clicked.connect(self.detect_and_save_chrome_size)
        row1.addWidget(btn_detect_chrome)

        btn_add_chrome = QPushButton("+ Custom Size")
        btn_add_chrome.setObjectName("secondary_action")
        btn_add_chrome.setToolTip("Add a custom height for Google Chrome (e.g. 432px, 500px, 40%)")
        btn_add_chrome.clicked.connect(self.add_custom_chrome_size)
        row1.addWidget(btn_add_chrome)

        btn_del_chrome = QPushButton("Delete Size")
        btn_del_chrome.setObjectName("danger")
        btn_del_chrome.setToolTip("Delete selected custom Chrome size")
        btn_del_chrome.clicked.connect(self.delete_current_chrome_size)
        row1.addWidget(btn_del_chrome)

        row1.addStretch()
        ctrl_layout_3win.addLayout(row1)

        # Row 2: Media Aspect Ratio & Capture (for 3-window mode)
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        lbl_media_ar = QLabel("Media Aspect Ratio:")
        lbl_media_ar.setObjectName("field_label")
        row2.addWidget(lbl_media_ar)

        self.media_ar_combo = NoWheelComboBox()
        self.media_ar_combo.setMinimumWidth(160)
        self.media_ar_combo.currentTextChanged.connect(self.on_media_ar_profile_changed)
        row2.addWidget(self.media_ar_combo)

        btn_detect_ar = QPushButton("📷 Save Current Media AR...")
        btn_detect_ar.setObjectName("secondary_action")
        btn_detect_ar.setToolTip("Inspect a running media window and automatically calculate and save its aspect ratio")
        btn_detect_ar.clicked.connect(self.detect_and_save_media_ar)
        row2.addWidget(btn_detect_ar)

        btn_add_ar = QPushButton("+ Custom AR")
        btn_add_ar.setObjectName("secondary_action")
        btn_add_ar.clicked.connect(self.add_custom_ar)
        row2.addWidget(btn_add_ar)

        btn_del_ar = QPushButton("Delete AR")
        btn_del_ar.setObjectName("danger")
        btn_del_ar.clicked.connect(self.delete_current_ar)
        row2.addWidget(btn_del_ar)

        row2.addStretch()
        ctrl_layout_3win.addLayout(row2)

        self.controls_stack.addWidget(ctrl_card_3win)

        # Page 1: Fullscreen + Corner Media Control Card
        ctrl_card_corner = QFrame()
        ctrl_card_corner.setObjectName("card")
        ctrl_layout_corner = QVBoxLayout(ctrl_card_corner)
        ctrl_layout_corner.setContentsMargins(16, 14, 16, 14)
        ctrl_layout_corner.setSpacing(12)

        # Corner Row 1: Target Windows & Corner Placement
        c_row1 = QHBoxLayout()
        c_row1.setSpacing(10)

        lbl_fs = QLabel("Fullscreen Window:")
        lbl_fs.setObjectName("field_label")
        c_row1.addWidget(lbl_fs)

        self.fs_title_input = QLineEdit()
        self.fs_title_input.setPlaceholderText("Title substring (or blank for any)")
        self.fs_title_input.setMinimumWidth(150)
        self.fs_title_input.textChanged.connect(self.on_corner_setting_changed)
        c_row1.addWidget(self.fs_title_input)

        btn_pick_fs = QPushButton("Pick App...")
        btn_pick_fs.setObjectName("secondary_action")
        btn_pick_fs.clicked.connect(self.pick_fullscreen_app)
        c_row1.addWidget(btn_pick_fs)

        lbl_corner_pos = QLabel("Media Corner:")
        lbl_corner_pos.setObjectName("field_label")
        c_row1.addWidget(lbl_corner_pos)

        self.corner_combo = NoWheelComboBox()
        self.corner_combo.addItems(["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left"])
        self.corner_combo.currentTextChanged.connect(self.on_corner_setting_changed)
        c_row1.addWidget(self.corner_combo)

        lbl_corner_media = QLabel("Media Window:")
        lbl_corner_media.setObjectName("field_label")
        c_row1.addWidget(lbl_corner_media)

        self.corner_media_input = QLineEdit()
        self.corner_media_input.setPlaceholderText("Title substring")
        self.corner_media_input.setMinimumWidth(130)
        self.corner_media_input.textChanged.connect(self.on_corner_setting_changed)
        c_row1.addWidget(self.corner_media_input)

        btn_pick_corner_media = QPushButton("Pick App...")
        btn_pick_corner_media.setObjectName("secondary_action")
        btn_pick_corner_media.clicked.connect(self.pick_corner_media_app)
        c_row1.addWidget(btn_pick_corner_media)

        c_row1.addStretch()
        ctrl_layout_corner.addLayout(c_row1)

        # Corner Row 2: Max Dimensions & Aspect Ratio Fitting
        c_row2 = QHBoxLayout()
        c_row2.setSpacing(10)

        lbl_max_size = QLabel("Max Size:")
        lbl_max_size.setObjectName("field_label")
        c_row2.addWidget(lbl_max_size)

        self.corner_max_w_input = QLineEdit()
        self.corner_max_w_input.setPlaceholderText("Max W (px)")
        self.corner_max_w_input.setFixedWidth(85)
        self.corner_max_w_input.textChanged.connect(self.on_corner_setting_changed)
        c_row2.addWidget(self.corner_max_w_input)

        lbl_x = QLabel("×")
        lbl_x.setObjectName("field_label")
        c_row2.addWidget(lbl_x)

        self.corner_max_h_input = QLineEdit()
        self.corner_max_h_input.setPlaceholderText("Max H (px)")
        self.corner_max_h_input.setFixedWidth(85)
        self.corner_max_h_input.textChanged.connect(self.on_corner_setting_changed)
        c_row2.addWidget(self.corner_max_h_input)

        btn_save_current_corner_size = QPushButton("📷 Save Current Size...")
        btn_save_current_corner_size.setObjectName("secondary_action")
        btn_save_current_corner_size.setToolTip("Inspect running media window to set its current dimensions as the max size")
        btn_save_current_corner_size.clicked.connect(self.detect_and_save_corner_max_size)
        c_row2.addWidget(btn_save_current_corner_size)

        lbl_corner_ar = QLabel("Aspect Ratio:")
        lbl_corner_ar.setObjectName("field_label")
        c_row2.addWidget(lbl_corner_ar)

        self.corner_ar_combo = NoWheelComboBox()
        self.corner_ar_combo.setMinimumWidth(150)
        self.corner_ar_combo.currentTextChanged.connect(self.on_corner_ar_changed)
        c_row2.addWidget(self.corner_ar_combo)

        btn_detect_corner_ar = QPushButton("📷 Save Current AR...")
        btn_detect_corner_ar.setObjectName("secondary_action")
        btn_detect_corner_ar.setToolTip("Inspect running media window and save its aspect ratio")
        btn_detect_corner_ar.clicked.connect(self.detect_and_save_corner_ar)
        c_row2.addWidget(btn_detect_corner_ar)

        btn_add_corner_ar = QPushButton("+ Custom AR")
        btn_add_corner_ar.setObjectName("secondary_action")
        btn_add_corner_ar.clicked.connect(self.add_custom_corner_ar)
        c_row2.addWidget(btn_add_corner_ar)

        c_row2.addStretch()
        ctrl_layout_corner.addLayout(c_row2)

        self.controls_stack.addWidget(ctrl_card_corner)
        main_layout.addWidget(self.controls_stack)

        # Section: Layout Preview
        lbl_preview = QLabel("Layout Preview")
        lbl_preview.setObjectName("section_title")
        main_layout.addWidget(lbl_preview)

        self.preview = PreviewWidget()
        main_layout.addWidget(self.preview, 1)

        # Section: Collapsible Zone Rules
        self.zone_header_widget = QWidget()
        zone_header = QHBoxLayout(self.zone_header_widget)
        zone_header.setContentsMargins(0, 0, 0, 0)
        zone_header.setSpacing(10)

        lbl_zones = QLabel("Zone Rules")
        lbl_zones.setObjectName("section_title")
        zone_header.addWidget(lbl_zones)

        self.btn_toggle_zones = QPushButton("▶ Show Zone Rules")
        self.btn_toggle_zones.setObjectName("secondary_action")
        self.btn_toggle_zones.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_zones.clicked.connect(self.toggle_zone_rules)
        zone_header.addWidget(self.btn_toggle_zones)

        zone_header.addStretch()
        main_layout.addWidget(self.zone_header_widget)

        # Collapsible Zone Container (Hidden by default)
        self.zone_container = QWidget()
        zone_container_layout = QVBoxLayout(self.zone_container)
        zone_container_layout.setContentsMargins(0, 0, 0, 0)
        zone_container_layout.setSpacing(8)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMaximumHeight(260)
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.rows_layout = QVBoxLayout(self.scroll_content)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rows_layout.setSpacing(10)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.scroll_content)
        zone_container_layout.addWidget(self.scroll)

        btn_add = QPushButton("+ Add Zone")
        btn_add.setObjectName("secondary_action")
        btn_add.setMinimumHeight(34)
        btn_add.clicked.connect(lambda: self.add_row())
        zone_container_layout.addWidget(btn_add)

        self.zone_container.setVisible(False)
        main_layout.addWidget(self.zone_container)

        # Footer Bar
        footer = QHBoxLayout()
        footer.setSpacing(12)

        btn_apply = QPushButton("Apply Layout")
        btn_apply.setObjectName("primary")
        btn_apply.setMinimumHeight(38)
        btn_apply.setMinimumWidth(160)
        btn_apply.clicked.connect(self.apply_layout)

        footer.addStretch()
        footer.addWidget(btn_apply)
        main_layout.addLayout(footer)

    def toggle_zone_rules(self):
        is_visible = self.zone_container.isVisible()
        self.zone_container.setVisible(not is_visible)
        if not is_visible:
            self.btn_toggle_zones.setText("▼ Hide Zone Rules")
        else:
            self.btn_toggle_zones.setText("▶ Show Zone Rules")

    def load_config(self):
        loaded_zones = []
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.active_mode = config.get("mode", "3_window")
                    if "layout_settings" in config:
                        self.layout_settings.update(config["layout_settings"])
                        if "media_profiles" in config["layout_settings"]:
                            self.media_profiles = config["layout_settings"]["media_profiles"]
                        if "chrome_sizes" in config["layout_settings"]:
                            self.chrome_sizes.update(config["layout_settings"]["chrome_sizes"])
                    if "corner_settings" in config:
                        self.corner_settings.update(config["corner_settings"])
                    if "zones" in config and isinstance(config["zones"], list):
                        loaded_zones = config["zones"]
            except:
                pass

        if "Equal Size" not in self.chrome_sizes:
            self.chrome_sizes["Equal Size"] = "equal"
        if "432px" not in self.chrome_sizes:
            self.chrome_sizes["432px"] = "432"

        if not loaded_zones:
            loaded_zones = [
                {"window_title": "MYAEW", "role": "media", "pos": "Bottom-Left", "stat": "Aspect Ratio", "val": "16:9"},
                {"window_title": "Google Chrome", "role": "chrome", "pos": "Top-Left", "stat": "Height (px)", "val": "432"},
                {"window_title": "Visual Studio Code", "role": "vscode", "pos": "Right", "stat": "Fill (Any)", "val": ""}
            ]

        self._updating_controls = True

        mode_idx = 0 if self.active_mode == "3_window" else 1
        self.mode_combo.setCurrentIndex(mode_idx)
        self.controls_stack.setCurrentIndex(mode_idx)
        self.zone_header_widget.setVisible(self.active_mode == "3_window")
        if self.active_mode != "3_window":
            self.zone_container.setVisible(False)

        self.vscode_side_combo.setCurrentText(self.layout_settings.get("vscode_side", "Right"))
        self.refresh_chrome_sizing_combo()
        self.refresh_media_profiles_combo()

        # Update corner controls
        self.fs_title_input.setText(self.corner_settings.get("fullscreen_app", ""))
        self.corner_combo.setCurrentText(self.corner_settings.get("corner", "Bottom-Right"))
        self.corner_media_input.setText(self.corner_settings.get("media_app", "Netflix"))
        self.corner_max_w_input.setText(str(self.corner_settings.get("max_width", 720)))
        self.corner_max_h_input.setText(str(self.corner_settings.get("max_height", 450)))
        self.refresh_corner_ar_combo()

        self._updating_controls = False

        for row in self.rows[:]:
            self.rows_layout.removeWidget(row)
            row.deleteLater()
        self.rows.clear()

        # For 3-window mode rows:
        three_win_zones = loaded_zones if self.active_mode == "3_window" else [
            {"window_title": "Home – Netflix", "role": "media", "pos": "Bottom-Left", "stat": "Aspect Ratio", "val": "16:9"},
            {"window_title": "Google Chrome", "role": "chrome", "pos": "Top-Left", "stat": "Height (px)", "val": "432"},
            {"window_title": "Visual Studio Code", "role": "vscode", "pos": "Right", "stat": "Fill (Any)", "val": ""}
        ]
        for z in three_win_zones:
            if self.active_mode == "3_window" or z.get("role") in ["media", "chrome", "vscode"]:
                self.add_row(z)

        self.sync_roles_with_layout_settings(update_ui=False)
        self.update_preview()

    def on_mode_changed(self, idx):
        self.active_mode = self.mode_combo.currentData()
        self.controls_stack.setCurrentIndex(idx)
        self.zone_header_widget.setVisible(self.active_mode == "3_window")
        if self.active_mode != "3_window":
            self.zone_container.setVisible(False)
        self.save_to_disk()
        self.update_preview()

    def refresh_chrome_sizing_combo(self):
        self.chrome_sizing_combo.blockSignals(True)
        self.chrome_sizing_combo.clear()
        keys = ["Equal Size"] + [k for k in self.chrome_sizes.keys() if k != "Equal Size"]
        for name in keys:
            self.chrome_sizing_combo.addItem(name)

        active = self.layout_settings.get("chrome_sizing", "Equal Size")
        if active and active in self.chrome_sizes:
            self.chrome_sizing_combo.setCurrentText(active)
        else:
            self.chrome_sizing_combo.setCurrentText("Equal Size")
            self.layout_settings["chrome_sizing"] = "Equal Size"
        self.chrome_sizing_combo.blockSignals(False)

    def refresh_media_profiles_combo(self):
        self.media_ar_combo.blockSignals(True)
        self.media_ar_combo.clear()
        for name in self.media_profiles.keys():
            self.media_ar_combo.addItem(name)
        active = self.layout_settings.get("active_media_profile")
        if active and active in self.media_profiles:
            self.media_ar_combo.setCurrentText(active)
        elif self.media_profiles:
            first_key = list(self.media_profiles.keys())[0]
            self.media_ar_combo.setCurrentText(first_key)
            self.layout_settings["active_media_profile"] = first_key
        self.media_ar_combo.blockSignals(False)

    def refresh_corner_ar_combo(self):
        self.corner_ar_combo.blockSignals(True)
        self.corner_ar_combo.clear()
        for name in self.media_profiles.keys():
            self.corner_ar_combo.addItem(name)
        active = self.corner_settings.get("active_media_profile")
        if active and active in self.media_profiles:
            self.corner_ar_combo.setCurrentText(active)
        elif self.media_profiles:
            first_key = list(self.media_profiles.keys())[0]
            self.corner_ar_combo.setCurrentText(first_key)
            self.corner_settings["active_media_profile"] = first_key
        self.corner_ar_combo.blockSignals(False)

    def on_vscode_side_changed(self, text):
        if self._updating_controls:
            return
        self.layout_settings["vscode_side"] = text
        self.sync_roles_with_layout_settings(update_ui=True)
        self.save_to_disk()
        self.update_preview()

    def on_chrome_sizing_changed(self, text):
        if self._updating_controls or not text:
            return
        self.layout_settings["chrome_sizing"] = text
        self.sync_roles_with_layout_settings(update_ui=True)
        self.save_to_disk()
        self.update_preview()

    def detect_and_save_chrome_size(self):
        dialog = AppSelectDialog(self, return_hwnd=True)
        if dialog.exec():
            hwnd = dialog.selected_hwnd
            title = dialog.get_selected()
            if not hwnd:
                return
            w, h = get_window_dimensions(hwnd)
            if h <= 0:
                QMessageBox.warning(self, "Could not detect", "Could not calculate size for the selected window.")
                return

            clean_name = title.split(" - ")[-1].strip() or "Chrome"
            suggested_profile = f"{h}px"

            name, ok = QInputDialog.getText(
                self, "Save Chrome Size",
                f"Detected size: {w} × {h} px\nDetected height: {h}px\n\nEnter size profile name:",
                text=suggested_profile
            )
            if ok and name.strip():
                p_name = name.strip()
                val = p_name if any(c.isdigit() for c in p_name) else f"{h}px"
                self.chrome_sizes[p_name] = val
                self.layout_settings["chrome_sizing"] = p_name
                chrome_row = self.find_row_by_role("chrome")
                if chrome_row:
                    if clean_name and clean_name not in chrome_row.app_match.text():
                        chrome_row.app_match.setText(clean_name)
                self.refresh_chrome_sizing_combo()
                self.sync_roles_with_layout_settings(update_ui=True)
                self.save_to_disk()
                self.update_preview()

    def add_custom_chrome_size(self):
        val, ok = QInputDialog.getText(
            self, "Add Custom Chrome Height",
            "Enter height in pixels or percentage (e.g. 432, 500px, 40%):",
            text="432px"
        )
        if ok and val.strip():
            val = val.strip()
            name = val if ("px" in val or "%" in val) else f"{val}px"
            self.chrome_sizes[name] = val
            self.layout_settings["chrome_sizing"] = name
            self.refresh_chrome_sizing_combo()
            self.sync_roles_with_layout_settings(update_ui=True)
            self.save_to_disk()
            self.update_preview()

    def delete_current_chrome_size(self):
        curr = self.chrome_sizing_combo.currentText()
        if curr == "Equal Size":
            QMessageBox.warning(self, "Cannot Delete", "'Equal Size' is default and cannot be deleted.")
            return
        if curr in self.chrome_sizes:
            del self.chrome_sizes[curr]
            self.layout_settings["chrome_sizing"] = "Equal Size"
            self.refresh_chrome_sizing_combo()
            self.sync_roles_with_layout_settings(update_ui=True)
            self.save_to_disk()
            self.update_preview()

    def on_media_ar_profile_changed(self, name):
        if self._updating_controls or not name:
            return
        self.layout_settings["active_media_profile"] = name
        ar_val = self.media_profiles.get(name, "16:9")
        media_row = self.find_row_by_role("media")
        if media_row:
            media_row.val_input.setText(ar_val)
        self.save_to_disk()
        self.update_preview()

    def detect_and_save_media_ar(self):
        dialog = AppSelectDialog(self, return_hwnd=True)
        if dialog.exec():
            hwnd = dialog.selected_hwnd
            title = dialog.get_selected()
            if not hwnd:
                return
            detected_ar, w, h = calculate_window_aspect_ratio(hwnd)
            if not detected_ar:
                QMessageBox.warning(self, "Could not detect", "Could not calculate aspect ratio for the selected window.")
                return

            clean_name = title.split(" - ")[-1].strip() or "Custom Media"
            suggested_profile = f"{clean_name} ({detected_ar})"

            name, ok = QInputDialog.getText(
                self, "Save Media Aspect Ratio",
                f"Detected size: {w} × {h} px\nAspect Ratio: {detected_ar}\n\nEnter profile name:",
                text=suggested_profile
            )
            if ok and name.strip():
                p_name = name.strip()
                self.media_profiles[p_name] = detected_ar
                self.layout_settings["active_media_profile"] = p_name
                media_row = self.find_row_by_role("media")
                if media_row:
                    if clean_name and clean_name not in media_row.app_match.text():
                        media_row.app_match.setText(clean_name)
                    media_row.val_input.setText(detected_ar)
                self.refresh_media_profiles_combo()
                self.refresh_corner_ar_combo()
                self.save_to_disk()
                self.update_preview()

    def add_custom_ar(self):
        ratio, ok = QInputDialog.getText(self, "Add Aspect Ratio", "Enter aspect ratio (e.g. 16:9, 4:3, 2.39:1):", text="16:9")
        if ok and ratio.strip():
            ratio = ratio.strip()
            name, n_ok = QInputDialog.getText(self, "Aspect Ratio Name", "Enter name for this aspect ratio:", text=ratio)
            if n_ok and name.strip():
                p_name = name.strip()
                self.media_profiles[p_name] = ratio
                self.layout_settings["active_media_profile"] = p_name
                self.refresh_media_profiles_combo()
                self.refresh_corner_ar_combo()
                media_row = self.find_row_by_role("media")
                if media_row:
                    media_row.val_input.setText(ratio)
                self.save_to_disk()
                self.update_preview()

    def delete_current_ar(self):
        curr = self.media_ar_combo.currentText()
        if len(self.media_profiles) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "You must have at least one media aspect ratio profile.")
            return
        if curr in self.media_profiles:
            del self.media_profiles[curr]
            self.layout_settings["active_media_profile"] = list(self.media_profiles.keys())[0]
            self.refresh_media_profiles_combo()
            self.refresh_corner_ar_combo()
            self.save_to_disk()
            self.update_preview()

    # Corner Mode Handlers
    def on_corner_setting_changed(self):
        if self._updating_controls:
            return
        self.corner_settings["fullscreen_app"] = self.fs_title_input.text().strip()
        self.corner_settings["corner"] = self.corner_combo.currentText()
        self.corner_settings["media_app"] = self.corner_media_input.text().strip()
        try:
            self.corner_settings["max_width"] = max(100, int(self.corner_max_w_input.text().strip() or "720"))
        except:
            pass
        try:
            self.corner_settings["max_height"] = max(100, int(self.corner_max_h_input.text().strip() or "450"))
        except:
            pass
        self.save_to_disk()
        self.update_preview()

    def on_corner_ar_changed(self, name):
        if self._updating_controls or not name:
            return
        self.corner_settings["active_media_profile"] = name
        self.save_to_disk()
        self.update_preview()

    def pick_fullscreen_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.fs_title_input.setText(title)

    def pick_corner_media_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.corner_media_input.setText(title)

    def detect_and_save_corner_max_size(self):
        dialog = AppSelectDialog(self, return_hwnd=True)
        if dialog.exec():
            hwnd = dialog.selected_hwnd
            title = dialog.get_selected()
            if not hwnd:
                return
            w, h = get_window_dimensions(hwnd)
            if w <= 0 or h <= 0:
                QMessageBox.warning(self, "Could not detect", "Could not calculate size for the selected window.")
                return

            clean_name = title.split(" - ")[-1].strip() or ""
            if clean_name and not self.corner_media_input.text():
                self.corner_media_input.setText(clean_name)

            self.corner_max_w_input.setText(str(w))
            self.corner_max_h_input.setText(str(h))
            self.corner_settings["max_width"] = w
            self.corner_settings["max_height"] = h
            self.save_to_disk()
            self.update_preview()

    def detect_and_save_corner_ar(self):
        dialog = AppSelectDialog(self, return_hwnd=True)
        if dialog.exec():
            hwnd = dialog.selected_hwnd
            title = dialog.get_selected()
            if not hwnd:
                return
            detected_ar, w, h = calculate_window_aspect_ratio(hwnd)
            if not detected_ar:
                QMessageBox.warning(self, "Could not detect", "Could not calculate aspect ratio for the selected window.")
                return

            clean_name = title.split(" - ")[-1].strip() or "Custom Media"
            suggested_profile = f"{clean_name} ({detected_ar})"

            name, ok = QInputDialog.getText(
                self, "Save Media Aspect Ratio",
                f"Detected size: {w} × {h} px\nAspect Ratio: {detected_ar}\n\nEnter profile name:",
                text=suggested_profile
            )
            if ok and name.strip():
                p_name = name.strip()
                self.media_profiles[p_name] = detected_ar
                self.corner_settings["active_media_profile"] = p_name
                self.refresh_media_profiles_combo()
                self.refresh_corner_ar_combo()
                self.save_to_disk()
                self.update_preview()

    def add_custom_corner_ar(self):
        ratio, ok = QInputDialog.getText(self, "Add Aspect Ratio", "Enter aspect ratio (e.g. 16:9, 4:3, 2.39:1):", text="16:9")
        if ok and ratio.strip():
            ratio = ratio.strip()
            name, n_ok = QInputDialog.getText(self, "Aspect Ratio Name", "Enter name for this aspect ratio:", text=ratio)
            if n_ok and name.strip():
                p_name = name.strip()
                self.media_profiles[p_name] = ratio
                self.corner_settings["active_media_profile"] = p_name
                self.refresh_media_profiles_combo()
                self.refresh_corner_ar_combo()
                self.save_to_disk()
                self.update_preview()

    def find_row_by_role(self, role):
        for r in self.rows:
            if getattr(r, "role", "") == role:
                return r
        for r in self.rows:
            title = r.app_match.text().lower()
            if role == "vscode" and ("code" in title or "visual studio" in title):
                r.role = "vscode"
                return r
            if role == "chrome" and "chrome" in title:
                r.role = "chrome"
                return r
            if role == "media" and ("myaew" in title or "netflix" in title or "picture" in title or "pip" in title or "youtube" in title):
                r.role = "media"
                return r
        return None

    def sync_roles_with_layout_settings(self, update_ui=True):
        vscode_side = self.layout_settings.get("vscode_side", "Right")
        other_side = "Left" if vscode_side == "Right" else "Right"
        top_pos = f"Top-{other_side}"
        bot_pos = f"Bottom-{other_side}"

        v_row = self.find_row_by_role("vscode")
        c_row = self.find_row_by_role("chrome")
        m_row = self.find_row_by_role("media")

        if v_row:
            v_row.role = "vscode"
            v_row.pos_combo.blockSignals(True)
            v_row.pos_combo.setCurrentText(vscode_side)
            v_row.pos_combo.blockSignals(False)

        if c_row:
            c_row.role = "chrome"
            c_row.pos_combo.blockSignals(True)
            c_row.pos_combo.setCurrentText(top_pos)
            c_row.pos_combo.blockSignals(False)

            active_sizing = self.layout_settings.get("chrome_sizing", "Equal Size")
            size_val = self.chrome_sizes.get(active_sizing, "equal")
            c_row.rule_combo.blockSignals(True)
            c_row.val_input.blockSignals(True)
            if size_val == "equal" or active_sizing == "Equal Size":
                c_row.rule_combo.setCurrentText("Height (px)")
                c_row.val_input.setText("")
            else:
                raw = str(size_val).strip()
                if "%" in raw:
                    c_row.rule_combo.setCurrentText("Height (%)")
                    match = re.search(r"(\d+(\.\d+)?)", raw)
                    c_row.val_input.setText(match.group(1) if match else raw.replace("%", "").strip())
                else:
                    c_row.rule_combo.setCurrentText("Height (px)")
                    match = re.search(r"(\d+)", raw)
                    c_row.val_input.setText(match.group(1) if match else raw.replace("px", "").strip())
            c_row.rule_combo.blockSignals(False)
            c_row.val_input.blockSignals(False)

        if m_row:
            m_row.role = "media"
            m_row.pos_combo.blockSignals(True)
            m_row.pos_combo.setCurrentText(bot_pos)
            m_row.pos_combo.blockSignals(False)
            curr_prof = self.layout_settings.get("active_media_profile")
            if curr_prof and curr_prof in self.media_profiles:
                m_row.val_input.setText(self.media_profiles[curr_prof])

        if update_ui:
            for r in self.rows:
                r.update_visibility()

    def add_row(self, data=None):
        idx = len(self.rows) + 1
        row = ZoneRow(self.scroll_content, self.delete_row, self.update_preview, index=idx, initial_data=data)
        self.rows.append(row)
        self.rows_layout.addWidget(row)
        self.update_preview()

    def delete_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            row.deleteLater()
            for i, r in enumerate(self.rows):
                r.set_index(i + 1)
            self.update_preview()

    def _get_current_zones_with_rects(self):
        screen = self.screen().geometry()
        screen_w = screen.width()
        screen_h = screen.height()

        if self.active_mode == "fullscreen_corner":
            return self.calculate_fullscreen_corner_rects(screen_w, screen_h)

        zones_data = []
        for row in self.rows:
            data = row.get_data()
            if not data["window_title"]:
                data["window_title"] = "Empty"
            zones_data.append(data)

        active_chrome = self.layout_settings.get("chrome_sizing", "Equal Size")
        chrome_val = self.chrome_sizes.get(active_chrome, "equal")
        return self.calculate_rects(zones_data, screen_w, screen_h, chrome_val=chrome_val)

    def calculate_fullscreen_corner_rects(self, screen_w, screen_h):
        fs_title = self.corner_settings.get("fullscreen_app", "").strip() or "Main Fullscreen"
        media_title = self.corner_settings.get("media_app", "").strip() or "Media (Corner)"
        corner = self.corner_settings.get("corner", "Bottom-Right")
        max_w = int(self.corner_settings.get("max_width", 720))
        max_h = int(self.corner_settings.get("max_height", 450))

        active_ar_name = self.corner_settings.get("active_media_profile")
        ar_str = self.media_profiles.get(active_ar_name, "16:9")

        def parse_ar(val):
            try:
                v = val.replace(":", "/")
                num, den = map(float, v.split("/"))
                return num / den
            except:
                return 16.0 / 9.0

        ar = parse_ar(ar_str)

        # Fit aspect ratio inside (max_w, max_h)
        # If max_w / max_h > ar, height is constrained by max_h
        if max_w / max_h > ar:
            mw = int(max_h * ar)
            mh = max_h
        else:
            mw = max_w
            mh = int(max_w / ar)

        mw = max(100, min(mw, screen_w))
        mh = max(100, min(mh, screen_h))

        # Position corner
        if corner == "Bottom-Right":
            mx = screen_w - mw
            my = screen_h - mh
        elif corner == "Bottom-Left":
            mx = 0
            my = screen_h - mh
        elif corner == "Top-Right":
            mx = screen_w - mw
            my = 0
        else: # Top-Left
            mx = 0
            my = 0

        # Zone 1: Fullscreen window
        # Zone 2: Corner media window (ordered second so SetWindowPos puts it on top)
        return [
            {
                "window_title": fs_title,
                "role": "fullscreen",
                "pos": "Fullscreen",
                "stat": "Fullscreen",
                "val": "",
                "rect": {
                    "x": 0,
                    "y": 0,
                    "width": screen_w,
                    "height": screen_h
                }
            },
            {
                "window_title": media_title,
                "role": "media",
                "pos": corner,
                "stat": f"Aspect Ratio ({ar_str})",
                "val": ar_str,
                "rect": {
                    "x": mx,
                    "y": my,
                    "width": mw,
                    "height": mh
                }
            }
        ]

    def update_preview(self):
        zones_data = self._get_current_zones_with_rects()
        screen = self.screen().geometry()
        self.preview.update_zones(zones_data, screen)

    def calculate_rects(self, zones, screen_w, screen_h, chrome_val="equal"):
        rem_x, rem_y, rem_w, rem_h = 0, 0, screen_w, screen_h

        def get_val(z, max_val, is_width=True):
            stat = z.get("stat", "")
            val = z.get("val", "0")
            try:
                if stat == "Width (px)" and is_width:
                    return int(val)
                if stat in ["Height (px)", "Min Height (px)"] and not is_width:
                    return int(val)
                if stat == "Width (%)" and is_width:
                    return int(max_val * float(val) / 100.0)
                if stat in ["Height (%)", "Min Height (%)"] and not is_width:
                    return int(max_val * float(val) / 100.0)
            except:
                pass
            return 0

        def parse_ar(val):
            try:
                v = val.replace(":", "/")
                num, den = map(float, v.split("/"))
                return num / den
            except:
                return 16.0 / 9.0

        def is_fill(z):
            return z.get("pos") == "Fill Space" or z.get("stat") == "Fill (Any)"

        # Pass 1: Explicit Side Snaps (Left, Right, Top, Bottom)
        for z in zones:
            pos = z.get("pos", "")
            if is_fill(z) or pos in ["Top-Left", "Bottom-Left", "Top-Right", "Bottom-Right"]:
                continue

            stat = z.get("stat", "")
            if pos in ["Right", "Left"]:
                if "Aspect Ratio" in stat:
                    w = int(rem_h * parse_ar(z.get("val", "")))
                else:
                    w = get_val(z, rem_w, True) or (rem_w // 2)

                w = max(0, min(w, rem_w))
                if pos == "Right":
                    z["rect"] = {"x": rem_x + rem_w - w, "y": rem_y, "width": w, "height": rem_h}
                    rem_w -= w
                else:
                    z["rect"] = {"x": rem_x, "y": rem_y, "width": w, "height": rem_h}
                    rem_x += w
                    rem_w -= w

            elif pos in ["Top", "Bottom"]:
                if "Aspect Ratio" in stat:
                    h = int(rem_w / parse_ar(z.get("val", "")))
                else:
                    h = get_val(z, rem_h, False) or (rem_h // 2)

                h = max(0, min(h, rem_h))
                if pos == "Top":
                    z["rect"] = {"x": rem_x, "y": rem_y, "width": rem_w, "height": h}
                    rem_y += h
                    rem_h -= h
                else:
                    z["rect"] = {"x": rem_x, "y": rem_y + rem_h - h, "width": rem_w, "height": h}
                    rem_h -= h

        # Pass 2: Corner Columns (Left and Right Columns)
        def solve_column(top_zone, bot_zone, col_x, total_h, total_w):
            if not top_zone and not bot_zone:
                return 0

            top_h, bot_h, col_w = 0, 0, 0

            if top_zone and bot_zone:
                top_stat = top_zone.get("stat", "")
                bot_stat = bot_zone.get("stat", "")

                if "Height" in top_stat and "Aspect Ratio" in bot_stat:
                    ar = parse_ar(bot_zone.get("val", ""))
                    if chrome_val == "equal":
                        top_h = total_h // 2
                        bot_h = total_h - top_h
                    else:
                        raw = str(chrome_val).strip()
                        if "%" in raw:
                            match = re.search(r"(\d+(\.\d+)?)", raw)
                            pct = float(match.group(1)) if match else 50.0
                            top_h = int(total_h * pct / 100.0)
                        else:
                            match = re.search(r"(\d+)", raw)
                            top_h = int(match.group(1)) if match else (get_val(top_zone, total_h, False) or (total_h // 2))
                        bot_h = total_h - top_h
                    col_w = int(bot_h * ar)
                elif "Height" in bot_stat and "Aspect Ratio" in top_stat:
                    ar = parse_ar(top_zone.get("val", ""))
                    if chrome_val == "equal":
                        bot_h = total_h // 2
                        top_h = total_h - bot_h
                    else:
                        raw = str(chrome_val).strip()
                        if "%" in raw:
                            match = re.search(r"(\d+(\.\d+)?)", raw)
                            pct = float(match.group(1)) if match else 50.0
                            bot_h = int(total_h * pct / 100.0)
                        else:
                            match = re.search(r"(\d+)", raw)
                            bot_h = int(match.group(1)) if match else (get_val(bot_zone, total_h, False) or (total_h // 2))
                        top_h = total_h - bot_h
                    col_w = int(top_h * ar)
                elif "Height" in top_stat and "Height" in bot_stat:
                    top_h = get_val(top_zone, total_h, False)
                    bot_h = get_val(bot_zone, total_h, False)
                    col_w = max(get_val(top_zone, total_w, True), get_val(bot_zone, total_w, True)) or (total_w // 2)
                elif "Aspect Ratio" in top_stat and "Aspect Ratio" in bot_stat:
                    top_h = total_h // 2
                    bot_h = total_h - top_h
                    ar_top = parse_ar(top_zone.get("val", ""))
                    ar_bot = parse_ar(bot_zone.get("val", ""))
                    col_w = max(int(top_h * ar_top), int(bot_h * ar_bot))
                else:
                    top_h = get_val(top_zone, total_h, False) or (total_h // 2)
                    bot_h = total_h - top_h
                    col_w = max(get_val(top_zone, total_w, True), get_val(bot_zone, total_w, True)) or (total_w // 2)
            elif top_zone:
                top_stat = top_zone.get("stat", "")
                if "Aspect Ratio" in top_stat:
                    top_h = total_h
                    col_w = int(top_h * parse_ar(top_zone.get("val", "")))
                else:
                    top_h = get_val(top_zone, total_h, False) or total_h
                    col_w = get_val(top_zone, total_w, True) or (total_w // 2)
            elif bot_zone:
                bot_stat = bot_zone.get("stat", "")
                if "Aspect Ratio" in bot_stat:
                    bot_h = total_h
                    col_w = int(bot_h * parse_ar(bot_zone.get("val", "")))
                else:
                    bot_h = get_val(bot_zone, total_h, False) or total_h
                    col_w = get_val(bot_zone, total_w, True) or (total_w // 2)

            col_w = max(0, min(col_w, total_w))

            if top_zone:
                top_zone["rect"] = {"x": col_x, "y": rem_y, "width": col_w, "height": top_h}
            if bot_zone:
                bot_y = rem_y + (top_h if top_zone else (total_h - bot_h))
                bot_zone["rect"] = {"x": col_x, "y": bot_y, "width": col_w, "height": bot_h}

            return col_w

        # Solve Left Column
        tl_zone = next((z for z in zones if z.get("pos") == "Top-Left"), None)
        bl_zone = next((z for z in zones if z.get("pos") == "Bottom-Left"), None)
        left_w = solve_column(tl_zone, bl_zone, rem_x, rem_h, rem_w)
        rem_x += left_w
        rem_w -= left_w

        # Solve Right Column
        tr_zone = next((z for z in zones if z.get("pos") == "Top-Right"), None)
        br_zone = next((z for z in zones if z.get("pos") == "Bottom-Right"), None)
        right_x = rem_x + rem_w
        right_w = solve_column(tr_zone, br_zone, right_x - min(rem_w, rem_w // 2), rem_h, rem_w)
        if right_w > 0:
            if tr_zone:
                tr_zone["rect"]["x"] = rem_x + rem_w - right_w
            if br_zone:
                br_zone["rect"]["x"] = rem_x + rem_w - right_w
            rem_w -= right_w

        # Pass 3: Fill Remaining Space
        fill_zones = [z for z in zones if "rect" not in z or is_fill(z)]
        if fill_zones:
            n = len(fill_zones)
            fill_w = rem_w // n
            for i, z in enumerate(fill_zones):
                fw = fill_w if i < n - 1 else (rem_w - i * fill_w)
                z["rect"] = {"x": rem_x + i * fill_w, "y": rem_y, "width": max(0, fw), "height": rem_h}

        return zones

    def save_to_disk(self):
        zones_with_rects = self._get_current_zones_with_rects()
        self.layout_settings["media_profiles"] = self.media_profiles
        self.layout_settings["chrome_sizes"] = self.chrome_sizes
        output_data = {
            "mode": self.active_mode,
            "layout_settings": self.layout_settings,
            "corner_settings": self.corner_settings,
            "zones": zones_with_rects
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

    def apply_layout(self):
        self.save_to_disk()
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
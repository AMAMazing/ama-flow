import sys
import json
import os
import math
import re
import subprocess
import ctypes
from ctypes import wintypes
import win32gui
import win32con
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QLineEdit, QFrame, QDialog, QListWidget,
                             QInputDialog, QMessageBox, QStackedWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QRect, QEvent
from PyQt6.QtGui import QFont, QPainter, QColor, QPen

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
MAIN_SCRIPT = os.path.join(os.path.dirname(__file__), "main.py")

STYLESHEET = """
QMainWindow {
    background-color: #121214;
}
QWidget#central {
    background-color: #121214;
}

/* PowerToys Cards */
QFrame#card {
    background-color: #1c1c20;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
}
QFrame#card:hover {
    border: 1px solid rgba(255, 255, 255, 0.12);
}

QFrame#monitor_card {
    background-color: #1c1c20;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 14px;
}

/* Typography */
QLabel {
    color: #f1f1f3;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
}
QLabel#header_title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.3px;
}
QLabel#subtitle {
    font-size: 12px;
    color: #8c8c9a;
}
QLabel#field_label {
    font-size: 12px;
    color: #9d9da8;
    font-weight: 600;
}

/* Inputs & Dropdowns */
QComboBox, QLineEdit {
    background-color: #141416;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 7px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 13px;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
}
QComboBox:hover, QLineEdit:hover {
    background-color: #19191c;
    border: 1px solid rgba(255, 255, 255, 0.18);
}
QComboBox:focus, QLineEdit:focus {
    background-color: #141416;
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
    border-top: 5px solid #8e8e99;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1c1c20;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    color: #ffffff;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* Buttons */
QPushButton {
    background-color: #242428;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 500;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
}
QPushButton:hover {
    background-color: #2c2c32;
    border: 1px solid rgba(255, 255, 255, 0.16);
}
QPushButton:pressed {
    background-color: #1d1d21;
}

QPushButton#primary {
    background-color: #0078d4;
    border: 1px solid #1084d9;
    color: #ffffff;
    font-weight: 600;
    border-radius: 8px;
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
    color: #8c8c9a;
    border: 1px solid transparent;
    border-radius: 6px;
    font-size: 12px;
    padding: 4px 8px;
}
QPushButton#danger:hover {
    background-color: rgba(232, 17, 35, 0.15);
    color: #f87171;
    border: 1px solid rgba(232, 17, 35, 0.25);
}

QPushButton#secondary_action {
    background-color: #1d1d22;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 7px;
}
QPushButton#secondary_action:hover {
    background-color: #26262c;
    border: 1px solid rgba(255, 255, 255, 0.18);
}

/* Dialog */
QDialog {
    background-color: #161619;
}
QListWidget {
    background-color: #121214;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 6px;
    color: #ffffff;
    font-size: 13px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 5px;
}
QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.06);
}
QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
"""

class NoWheelComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()

def is_alt_tab_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    title = win32gui.GetWindowText(hwnd).strip()
    if not title:
        return False

    if "appzones" in title.lower():
        return False

    try:
        current_pid = os.getpid()
        class DWORD(ctypes.c_ulong):
            pass
        pid = DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == current_pid:
            return False
    except Exception:
        pass

    cloaked = ctypes.c_int(0)
    try:
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0:
            if cloaked.value != 0:
                return False
    except Exception:
        pass

    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if (ex_style & win32con.WS_EX_TOOLWINDOW) and not (ex_style & win32con.WS_EX_APPWINDOW):
            return False

        owner = win32gui.GetWindow(hwnd, win32con.GW_OWNER)
        if owner and not (ex_style & win32con.WS_EX_APPWINDOW):
            return False

        rect = win32gui.GetWindowRect(hwnd)
        if (rect[2] - rect[0] <= 0) or (rect[3] - rect[1] <= 0):
            return False
    except Exception:
        return False

    return True

def get_open_windows():
    windows = []
    def callback(hwnd, _):
        if is_alt_tab_window(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            windows.append((title, hwnd))
        return True
    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass
    junk = {"Program Manager", "Settings", "Microsoft Text Input Application", "Windows Input Experience"}
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
    except Exception:
        return None, 0, 0

class AppSelectDialog(QDialog):
    def __init__(self, parent, return_hwnd=False):
        super().__init__(parent)
        self.return_hwnd = return_hwnd
        self.selected_hwnd = None
        self.setWindowTitle("Select Open Application")
        self.setMinimumSize(440, 420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        lbl = QLabel("Choose a running application:")
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

class MainWindow(QMainWindow):
    def __init__(self):
        self.overlay_preview = None
        super().__init__()
        self.setWindowTitle("AppZones")
        self.resize(840, 370)
        self.setStyleSheet(STYLESHEET)

        # Make sure the GUI stays visible on top of the 1:1 fullscreen preview overlay
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.active_mode = "3_window"
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
        self.app_titles_3win = {
            "vscode": "Visual Studio Code",
            "chrome": "Google Chrome",
            "media": "Netflix"
        }
        self._updating_controls = False

        # Initialize the 1:1 fullscreen live preview overlay
        self.overlay_preview = FullscreenPreviewOverlay()

        self.init_ui()
        self.load_config()

    def init_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Header Area
        header = QHBoxLayout()
        titles_box = QVBoxLayout()
        titles_box.setSpacing(1)
        title = QLabel("AppZones ⚡")
        title.setObjectName("header_title")
        sub = QLabel("Automated PowerToys window placement solver")
        sub.setObjectName("subtitle")
        titles_box.addWidget(title)
        titles_box.addWidget(sub)
        header.addLayout(titles_box)
        header.addStretch()

        # Display badge
        self.monitor_card = QFrame()
        self.monitor_card.setObjectName("monitor_card")
        mon_layout = QHBoxLayout(self.monitor_card)
        mon_layout.setContentsMargins(10, 4, 10, 4)
        mon_layout.setSpacing(6)

        screen = self.screen().geometry()
        self.mon_res_label = QLabel(f"🖥️ Display 1  •  {screen.width()} × {screen.height()}")
        self.mon_res_label.setObjectName("subtitle")
        self.mon_res_label.setStyleSheet("color: #d1d1db; font-weight: 600; font-size: 12px;")
        mon_layout.addWidget(self.mon_res_label)
        header.addWidget(self.monitor_card)
        main_layout.addLayout(header)

        # Mode Selection Bar
        mode_card = QFrame()
        mode_card.setObjectName("card")
        mode_layout = QHBoxLayout(mode_card)
        mode_layout.setContentsMargins(14, 8, 14, 8)
        mode_layout.setSpacing(10)

        lbl_mode = QLabel("Layout Mode:")
        lbl_mode.setObjectName("field_label")
        mode_layout.addWidget(lbl_mode)

        self.mode_combo = NoWheelComboBox()
        self.mode_combo.addItem("🪟 3-Window Setup (Code + Chrome + Media)", "3_window")
        self.mode_combo.addItem("🎯 Fullscreen + Corner Media (Weekly Activity)", "fullscreen_corner")
        self.mode_combo.setMinimumWidth(340)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addWidget(mode_card)

        # Dynamic Controls Stack
        self.controls_stack = QStackedWidget()

        # Page 0: 3-Window Setup Controls
        ctrl_card_3win = QFrame()
        ctrl_card_3win.setObjectName("card")
        ctrl_layout_3win = QVBoxLayout(ctrl_card_3win)
        ctrl_layout_3win.setContentsMargins(14, 12, 14, 12)
        ctrl_layout_3win.setSpacing(10)

        # Row 1: VS Code Placement & Match
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_side = QLabel("Code Side:")
        lbl_side.setObjectName("field_label")
        row1.addWidget(lbl_side)

        self.vscode_side_combo = NoWheelComboBox()
        self.vscode_side_combo.addItems(["Right", "Left"])
        self.vscode_side_combo.setFixedWidth(85)
        self.vscode_side_combo.currentTextChanged.connect(self.on_vscode_side_changed)
        row1.addWidget(self.vscode_side_combo)

        lbl_code_title = QLabel("App:")
        lbl_code_title.setObjectName("field_label")
        row1.addWidget(lbl_code_title)

        self.code_title_input = QLineEdit()
        self.code_title_input.setPlaceholderText("Code Window Title")
        self.code_title_input.textChanged.connect(self.on_3win_titles_changed)
        row1.addWidget(self.code_title_input, 1)

        btn_pick_code = QPushButton("Pick...")
        btn_pick_code.setObjectName("secondary_action")
        btn_pick_code.clicked.connect(self.pick_code_app)
        row1.addWidget(btn_pick_code)

        ctrl_layout_3win.addLayout(row1)

        # Row 2: Chrome Sizing & Match
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_chrome = QLabel("Chrome Size:")
        lbl_chrome.setObjectName("field_label")
        row2.addWidget(lbl_chrome)

        self.chrome_sizing_combo = NoWheelComboBox()
        self.chrome_sizing_combo.setMinimumWidth(120)
        self.chrome_sizing_combo.currentTextChanged.connect(self.on_chrome_sizing_changed)
        row2.addWidget(self.chrome_sizing_combo)

        self.chrome_title_input = QLineEdit()
        self.chrome_title_input.setPlaceholderText("Chrome Window Title")
        self.chrome_title_input.textChanged.connect(self.on_3win_titles_changed)
        row2.addWidget(self.chrome_title_input, 1)

        btn_pick_chrome = QPushButton("Pick...")
        btn_pick_chrome.setObjectName("secondary_action")
        btn_pick_chrome.clicked.connect(self.pick_chrome_app)
        row2.addWidget(btn_pick_chrome)

        btn_detect_chrome = QPushButton("� Save Size")
        btn_detect_chrome.setObjectName("secondary_action")
        btn_detect_chrome.setToolTip("Inspect window to detect and save height")
        btn_detect_chrome.clicked.connect(self.detect_and_save_chrome_size)
        row2.addWidget(btn_detect_chrome)

        btn_add_chrome = QPushButton("+ Size")
        btn_add_chrome.setObjectName("secondary_action")
        btn_add_chrome.clicked.connect(self.add_custom_chrome_size)
        row2.addWidget(btn_add_chrome)

        btn_del_chrome = QPushButton("✕")
        btn_del_chrome.setObjectName("danger")
        btn_del_chrome.setToolTip("Delete selected size profile")
        btn_del_chrome.clicked.connect(self.delete_current_chrome_size)
        row2.addWidget(btn_del_chrome)

        ctrl_layout_3win.addLayout(row2)

        # Row 3: Media Aspect Ratio & Match
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        lbl_media_ar = QLabel("Media Ratio:")
        lbl_media_ar.setObjectName("field_label")
        row3.addWidget(lbl_media_ar)

        self.media_ar_combo = NoWheelComboBox()
        self.media_ar_combo.setMinimumWidth(130)
        self.media_ar_combo.currentTextChanged.connect(self.on_media_ar_profile_changed)
        row3.addWidget(self.media_ar_combo)

        self.media_title_input = QLineEdit()
        self.media_title_input.setPlaceholderText("Media Window Title")
        self.media_title_input.textChanged.connect(self.on_3win_titles_changed)
        row3.addWidget(self.media_title_input, 1)

        btn_pick_media = QPushButton("Pick...")
        btn_pick_media.setObjectName("secondary_action")
        btn_pick_media.clicked.connect(self.pick_media_app)
        row3.addWidget(btn_pick_media)

        btn_detect_ar = QPushButton("� Save AR")
        btn_detect_ar.setObjectName("secondary_action")
        btn_detect_ar.setToolTip("Inspect window to detect and save aspect ratio")
        btn_detect_ar.clicked.connect(self.detect_and_save_media_ar)
        row3.addWidget(btn_detect_ar)

        btn_add_ar = QPushButton("+ AR")
        btn_add_ar.setObjectName("secondary_action")
        btn_add_ar.clicked.connect(self.add_custom_ar)
        row3.addWidget(btn_add_ar)

        btn_del_ar = QPushButton("✕")
        btn_del_ar.setObjectName("danger")
        btn_del_ar.setToolTip("Delete selected AR profile")
        btn_del_ar.clicked.connect(self.delete_current_ar)
        row3.addWidget(btn_del_ar)

        ctrl_layout_3win.addLayout(row3)
        self.controls_stack.addWidget(ctrl_card_3win)

        # Page 1: Fullscreen + Corner Media Controls
        ctrl_card_corner = QFrame()
        ctrl_card_corner.setObjectName("card")
        ctrl_layout_corner = QVBoxLayout(ctrl_card_corner)
        ctrl_layout_corner.setContentsMargins(14, 12, 14, 12)
        ctrl_layout_corner.setSpacing(10)

        # Corner Row 1: Target Windows & Corner Placement
        c_row1 = QHBoxLayout()
        c_row1.setSpacing(8)

        lbl_fs = QLabel("Fullscreen App:")
        lbl_fs.setObjectName("field_label")
        c_row1.addWidget(lbl_fs)

        self.fs_title_input = QLineEdit()
        self.fs_title_input.setPlaceholderText("Fullscreen Window Title")
        self.fs_title_input.textChanged.connect(self.on_corner_setting_changed)
        c_row1.addWidget(self.fs_title_input, 1)

        btn_pick_fs = QPushButton("Pick...")
        btn_pick_fs.setObjectName("secondary_action")
        btn_pick_fs.clicked.connect(self.pick_fullscreen_app)
        c_row1.addWidget(btn_pick_fs)

        lbl_corner_pos = QLabel("Corner:")
        lbl_corner_pos.setObjectName("field_label")
        c_row1.addWidget(lbl_corner_pos)

        self.corner_combo = NoWheelComboBox()
        self.corner_combo.addItems(["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left"])
        self.corner_combo.currentTextChanged.connect(self.on_corner_setting_changed)
        c_row1.addWidget(self.corner_combo)

        lbl_corner_media = QLabel("Media App:")
        lbl_corner_media.setObjectName("field_label")
        c_row1.addWidget(lbl_corner_media)

        self.corner_media_input = QLineEdit()
        self.corner_media_input.setPlaceholderText("Corner Media Title")
        self.corner_media_input.textChanged.connect(self.on_corner_setting_changed)
        c_row1.addWidget(self.corner_media_input, 1)

        btn_pick_corner_media = QPushButton("Pick...")
        btn_pick_corner_media.setObjectName("secondary_action")
        btn_pick_corner_media.clicked.connect(self.pick_corner_media_app)
        c_row1.addWidget(btn_pick_corner_media)

        ctrl_layout_corner.addLayout(c_row1)

        # Corner Row 2: Max Dimensions & Aspect Ratio Fitting
        c_row2 = QHBoxLayout()
        c_row2.setSpacing(8)

        lbl_max_size = QLabel("Max Size:")
        lbl_max_size.setObjectName("field_label")
        c_row2.addWidget(lbl_max_size)

        self.corner_max_w_input = QLineEdit()
        self.corner_max_w_input.setPlaceholderText("Max W")
        self.corner_max_w_input.setFixedWidth(70)
        self.corner_max_w_input.textChanged.connect(self.on_corner_setting_changed)
        c_row2.addWidget(self.corner_max_w_input)

        lbl_x = QLabel("×")
        lbl_x.setObjectName("field_label")
        c_row2.addWidget(lbl_x)

        self.corner_max_h_input = QLineEdit()
        self.corner_max_h_input.setPlaceholderText("Max H")
        self.corner_max_h_input.setFixedWidth(70)
        self.corner_max_h_input.textChanged.connect(self.on_corner_setting_changed)
        c_row2.addWidget(self.corner_max_h_input)

        btn_save_current_corner_size = QPushButton("� Save Current Size")
        btn_save_current_corner_size.setObjectName("secondary_action")
        btn_save_current_corner_size.setToolTip("Inspect window to save its width and height as max size")
        btn_save_current_corner_size.clicked.connect(self.detect_and_save_corner_max_size)
        c_row2.addWidget(btn_save_current_corner_size)

        lbl_corner_ar = QLabel("Aspect Ratio:")
        lbl_corner_ar.setObjectName("field_label")
        c_row2.addWidget(lbl_corner_ar)

        self.corner_ar_combo = NoWheelComboBox()
        self.corner_ar_combo.setMinimumWidth(130)
        self.corner_ar_combo.currentTextChanged.connect(self.on_corner_ar_changed)
        c_row2.addWidget(self.corner_ar_combo)

        btn_detect_corner_ar = QPushButton("� Save AR")
        btn_detect_corner_ar.setObjectName("secondary_action")
        btn_detect_corner_ar.setToolTip("Inspect window to detect and save aspect ratio")
        btn_detect_corner_ar.clicked.connect(self.detect_and_save_corner_ar)
        c_row2.addWidget(btn_detect_corner_ar)

        btn_add_corner_ar = QPushButton("+ AR")
        btn_add_corner_ar.setObjectName("secondary_action")
        btn_add_corner_ar.clicked.connect(self.add_custom_corner_ar)
        c_row2.addWidget(btn_add_corner_ar)

        c_row2.addStretch()
        ctrl_layout_corner.addLayout(c_row2)
        self.controls_stack.addWidget(ctrl_card_corner)

        main_layout.addWidget(self.controls_stack)

        # Footer Bar
        footer = QHBoxLayout()
        footer.setSpacing(10)

        tip_lbl = QLabel("💡 Tip: Hold Ctrl while dragging any window to snap it into position.")
        tip_lbl.setObjectName("subtitle")
        footer.addWidget(tip_lbl)
        footer.addStretch()

        btn_apply = QPushButton("🚀 Apply Layout")
        btn_apply.setObjectName("primary")
        btn_apply.setMinimumHeight(38)
        btn_apply.setMinimumWidth(160)
        btn_apply.clicked.connect(self.apply_layout)
        footer.addWidget(btn_apply)

        main_layout.addLayout(footer)

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "overlay_preview", None):
            self.show_overlay()

    def show_overlay(self):
        zones_data = self._get_current_zones_with_rects()
        screen_geo = self.screen().geometry()
        if getattr(self, "overlay_preview", None):
            self.overlay_preview.set_zones(zones_data, screen_geo)
            self.overlay_preview.show()
        if self.isVisible():
            self.raise_()
            self.activateWindow()

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
            except Exception:
                pass

        if "Equal Size" not in self.chrome_sizes:
            self.chrome_sizes["Equal Size"] = "equal"
        if "432px" not in self.chrome_sizes:
            self.chrome_sizes["432px"] = "432"

        # Read 3-window app titles from config if present
        for z in loaded_zones:
            role = z.get("role")
            title = z.get("window_title")
            if role in self.app_titles_3win and title:
                self.app_titles_3win[role] = title

        self._updating_controls = True

        mode_idx = 0 if self.active_mode == "3_window" else 1
        self.mode_combo.setCurrentIndex(mode_idx)
        self.controls_stack.setCurrentIndex(mode_idx)

        self.vscode_side_combo.setCurrentText(self.layout_settings.get("vscode_side", "Right"))
        self.code_title_input.setText(self.app_titles_3win.get("vscode", "Visual Studio Code"))
        self.chrome_title_input.setText(self.app_titles_3win.get("chrome", "Google Chrome"))
        self.media_title_input.setText(self.app_titles_3win.get("media", "Netflix"))

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
        self.update_dimensions_display()

    def on_mode_changed(self, idx):
        self.active_mode = self.mode_combo.currentData()
        self.controls_stack.setCurrentIndex(idx)
        self.save_to_disk()
        self.update_dimensions_display()

    def on_3win_titles_changed(self):
        if self._updating_controls:
            return
        self.app_titles_3win["vscode"] = self.code_title_input.text().strip() or "Visual Studio Code"
        self.app_titles_3win["chrome"] = self.chrome_title_input.text().strip() or "Google Chrome"
        self.app_titles_3win["media"] = self.media_title_input.text().strip() or "Netflix"
        self.save_to_disk()
        self.update_dimensions_display()

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
        self.save_to_disk()
        self.update_dimensions_display()

    def on_chrome_sizing_changed(self, text):
        if self._updating_controls or not text:
            return
        self.layout_settings["chrome_sizing"] = text
        self.save_to_disk()
        self.update_dimensions_display()

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
                if clean_name:
                    self.chrome_title_input.setText(clean_name)
                    self.app_titles_3win["chrome"] = clean_name
                self.refresh_chrome_sizing_combo()
                self.save_to_disk()
                self.update_dimensions_display()

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
            self.save_to_disk()
            self.update_dimensions_display()

    def delete_current_chrome_size(self):
        curr = self.chrome_sizing_combo.currentText()
        if curr == "Equal Size":
            QMessageBox.warning(self, "Cannot Delete", "'Equal Size' is default and cannot be deleted.")
            return
        if curr in self.chrome_sizes:
            del self.chrome_sizes[curr]
            self.layout_settings["chrome_sizing"] = "Equal Size"
            self.refresh_chrome_sizing_combo()
            self.save_to_disk()
            self.update_dimensions_display()

    def on_media_ar_profile_changed(self, name):
        if self._updating_controls or not name:
            return
        self.layout_settings["active_media_profile"] = name
        self.save_to_disk()
        self.update_dimensions_display()

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
                if clean_name:
                    self.media_title_input.setText(clean_name)
                    self.app_titles_3win["media"] = clean_name
                self.refresh_media_profiles_combo()
                self.refresh_corner_ar_combo()
                self.save_to_disk()
                self.update_dimensions_display()

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
                self.save_to_disk()
                self.update_dimensions_display()

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
            self.update_dimensions_display()

    # Corner Mode Handlers
    def on_corner_setting_changed(self):
        if self._updating_controls:
            return
        self.corner_settings["fullscreen_app"] = self.fs_title_input.text().strip()
        self.corner_settings["corner"] = self.corner_combo.currentText()
        self.corner_settings["media_app"] = self.corner_media_input.text().strip()
        try:
            self.corner_settings["max_width"] = max(100, int(self.corner_max_w_input.text().strip() or "720"))
        except Exception:
            pass
        try:
            self.corner_settings["max_height"] = max(100, int(self.corner_max_h_input.text().strip() or "450"))
        except Exception:
            pass
        self.save_to_disk()
        self.update_dimensions_display()

    def on_corner_ar_changed(self, name):
        if self._updating_controls or not name:
            return
        self.corner_settings["active_media_profile"] = name
        self.save_to_disk()
        self.update_dimensions_display()

    def pick_code_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.code_title_input.setText(title)

    def pick_chrome_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.chrome_title_input.setText(title)

    def pick_media_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.media_title_input.setText(title)

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
            self.update_dimensions_display()

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
                self.update_dimensions_display()

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
                self.update_dimensions_display()

    def _get_current_zones_with_rects(self):
        screen = self.screen().geometry()
        screen_w = screen.width()
        screen_h = screen.height()

        if self.active_mode == "fullscreen_corner":
            return self.calculate_fullscreen_corner_rects(screen_w, screen_h)

        # 3-window zones
        vscode_side = self.layout_settings.get("vscode_side", "Right")
        other_side = "Left" if vscode_side == "Right" else "Right"
        top_pos = f"Top-{other_side}"
        bot_pos = f"Bottom-{other_side}"

        curr_ar = self.media_profiles.get(self.layout_settings.get("active_media_profile", "16:9 (PiP)"), "16:9")
        active_chrome = self.layout_settings.get("chrome_sizing", "Equal Size")
        chrome_val = self.chrome_sizes.get(active_chrome, "equal")

        zones = [
            {
                "window_title": self.app_titles_3win.get("media", "Netflix"),
                "role": "media",
                "pos": bot_pos,
                "stat": "Aspect Ratio",
                "val": curr_ar
            },
            {
                "window_title": self.app_titles_3win.get("chrome", "Google Chrome"),
                "role": "chrome",
                "pos": top_pos,
                "stat": "Height (px)" if chrome_val == "equal" else ("Height (%)" if "%" in str(chrome_val) else "Height (px)"),
                "val": "" if chrome_val == "equal" else str(chrome_val)
            },
            {
                "window_title": self.app_titles_3win.get("vscode", "Visual Studio Code"),
                "role": "vscode",
                "pos": vscode_side,
                "stat": "Fill (Any)",
                "val": ""
            }
        ]

        return self.calculate_rects(zones, screen_w, screen_h, chrome_val=chrome_val)

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
            except Exception:
                return 16.0 / 9.0

        ar = parse_ar(ar_str)

        if max_w / max_h > ar:
            mw = int(max_h * ar)
            mh = max_h
        else:
            mw = max_w
            mh = int(max_w / ar)

        mw = max(100, min(mw, screen_w))
        mh = max(100, min(mh, screen_h))

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

    def update_dimensions_display(self):
        zones_data = self._get_current_zones_with_rects()
        screen_geo = self.screen().geometry()
        if getattr(self, "overlay_preview", None):
            self.overlay_preview.set_zones(zones_data, screen_geo)
        if hasattr(self, "mon_res_label"):
            self.mon_res_label.setText(f"🖥️ Display 1  •  {screen_geo.width()} × {screen_geo.height()}")
        # Ensure MainWindow is raised above the preview overlay only if it's already visible
        if self.isVisible():
            self.raise_()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if getattr(self, "overlay_preview", None):
                if self.isMinimized():
                    self.overlay_preview.hide()
                else:
                    self.overlay_preview.show()
                    self.raise_()

    def closeEvent(self, event):
        if getattr(self, "overlay_preview", None):
            self.overlay_preview.close()
        super().closeEvent(event)

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
            except Exception:
                pass
            return 0

        def parse_ar(val):
            try:
                v = val.replace(":", "/")
                num, den = map(float, v.split("/"))
                return num / den
            except Exception:
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
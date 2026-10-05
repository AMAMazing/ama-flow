import sys
import json
import os
import subprocess
import win32gui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QLineEdit, QScrollArea, QFrame, QDialog, QListWidget,
                             QInputDialog, QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

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
    font-size: 16px;
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
        self.setMinimumSize(420, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel("Choose a running window to assign to this zone:")
        lbl.setObjectName("subtitle")
        layout.addWidget(lbl)

        self.list = QListWidget()
        for w in get_open_windows():
            self.list.addItem(w)
        layout.addWidget(self.list)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_select = QPushButton("Select Application")
        btn_select.setObjectName("primary")
        btn_select.clicked.connect(self.accept)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_select)
        layout.addLayout(btn_box)

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

        # Monitor Bezel (FancyZones style)
        painter.setBrush(QColor("#181818"))
        painter.setPen(QPen(QColor("#383838"), 1))
        painter.drawRoundedRect(px - 6, py - 6, pw + 12, ph + 12, 8, 8)

        # Monitor Screen Canvas
        painter.setBrush(QColor("#242424"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(px, py, pw, ph, 4, 4)

        # Palette: refined muted PowerToys-like tones
        palette = [
            (QColor("#1e3a5f"), QColor("#3b82f6")),  # Blue
            (QColor("#2d3748"), QColor("#818cf8")),  # Indigo/Slate
            (QColor("#1e3f3b"), QColor("#10b981")),  # Teal
            (QColor("#452e2e"), QColor("#f87171")),  # Rose
            (QColor("#3f2d4f"), QColor("#c084fc")),  # Purple
            (QColor("#423821"), QColor("#fbbf24")),  # Amber
        ]

        # Draw Zones
        for i, z in enumerate(self.zones):
            rect = z.get('rect')
            if not rect:
                continue

            zx = px + int(rect['x'] * scale)
            zy = py + int(rect['y'] * scale)
            zw = int(rect['width'] * scale)
            zh = int(rect['height'] * scale)

            fill_c, border_c = palette[i % len(palette)]

            # Inset slightly for zone separation like FancyZones
            gap = 2
            rx = zx + gap
            ry = zy + gap
            rw = max(1, zw - gap * 2)
            rh = max(1, zh - gap * 2)

            painter.setBrush(fill_c)
            painter.setPen(QPen(border_c, 1.5))
            painter.drawRoundedRect(rx, ry, rw, rh, 4, 4)

            # Zone number badge top-left
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 140))
            painter.drawRoundedRect(rx + 6, ry + 6, 20, 18, 3, 3)
            painter.setPen(QColor("#ffffff"))
            font_small = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font_small)
            painter.drawText(rx + 6, ry + 6, 20, 18, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            # Title and dimension text
            title = z.get('window_title', '')
            real_w, real_h = int(rect['width']), int(rect['height'])
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header Row: Zone Number Badge, App Name/Input, Pick App Button, Delete Button
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.num_badge = QLabel(str(self.index))
        self.num_badge.setObjectName("zone_num")
        top_row.addWidget(self.num_badge)

        self.app_match = QLineEdit()
        self.app_match.setPlaceholderText("Window Title Substring (e.g. Chrome, Visual Studio Code)")
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

        # Rules / Placement Controls Row
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
            self.val_input.setText(initial_data.get("val", ""))

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
        if hasattr(self, '_initialized') and self._initialized:
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
            "pos": self.pos_combo.currentText(),
            "stat": self.rule_combo.currentText(),
            "val": self.val_input.text().strip()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppZones - FancyZones Auto-Layout")
        self.resize(880, 840)
        self.setStyleSheet(STYLESHEET)

        self.rows = []
        self.presets = {}
        self.preset_modes = {}
        self.active_preset = "Default"

        self.init_ui()
        self.load_config()

    def init_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Area with PowerToys-style Monitor Display Card
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

        # Monitor Card (FancyZones style)
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

        # Presets Bar Card
        preset_card = QFrame()
        preset_card.setObjectName("card")
        preset_layout = QHBoxLayout(preset_card)
        preset_layout.setContentsMargins(14, 10, 14, 10)
        preset_layout.setSpacing(12)

        lbl_preset = QLabel("Preset:")
        lbl_preset.setObjectName("field_label")
        preset_layout.addWidget(lbl_preset)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(160)
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo, 1)

        lbl_split = QLabel("Corner Sizing:")
        lbl_split.setObjectName("field_label")
        preset_layout.addWidget(lbl_split)

        self.split_combo = NoWheelComboBox()
        self.split_combo.addItems(["Maximize Size", "Equal Sizes"])
        self.split_combo.setToolTip("Maximize Size: Aspect Ratio app gets max possible space.\nEqual Sizes: Both apps split column height equally.")
        self.split_combo.currentTextChanged.connect(lambda _: self.on_split_mode_changed())
        preset_layout.addWidget(self.split_combo)

        btn_save = QPushButton("Save As...")
        btn_save.setObjectName("secondary_action")
        btn_save.clicked.connect(self.save_preset_as)
        preset_layout.addWidget(btn_save)

        btn_delete = QPushButton("Delete")
        btn_delete.setObjectName("danger")
        btn_delete.clicked.connect(self.delete_preset)
        preset_layout.addWidget(btn_delete)

        main_layout.addWidget(preset_card)

        # Section: Layout Preview
        lbl_preview = QLabel("Layout Preview")
        lbl_preview.setObjectName("section_title")
        main_layout.addWidget(lbl_preview)

        self.preview = PreviewWidget()
        main_layout.addWidget(self.preview)

        # Section: Zones Configuration
        lbl_zones = QLabel("Zone Rules")
        lbl_zones.setObjectName("section_title")
        main_layout.addWidget(lbl_zones)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.rows_layout = QVBoxLayout(self.scroll_content)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rows_layout.setSpacing(10)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, 1)

        # Bottom Bar
        footer = QHBoxLayout()
        footer.setSpacing(12)

        btn_add = QPushButton("+ Add Zone")
        btn_add.setObjectName("secondary_action")
        btn_add.setMinimumHeight(38)
        btn_add.clicked.connect(lambda: self.add_row())

        btn_apply = QPushButton("Apply Layout")
        btn_apply.setObjectName("primary")
        btn_apply.setMinimumHeight(38)
        btn_apply.setMinimumWidth(160)
        btn_apply.clicked.connect(self.apply_layout)

        footer.addWidget(btn_add)
        footer.addStretch()
        footer.addWidget(btn_apply)
        main_layout.addLayout(footer)

    def load_config(self):
        loaded = False
        self.presets = {"Default": []}
        self.preset_modes = {}
        self.active_preset = "Default"

        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if "presets" in config:
                        self.presets = config["presets"]
                        self.active_preset = config.get("active_preset", "Default")
                        self.preset_modes = config.get("preset_modes", {})
                        loaded = True
                    elif "zones" in config:
                        self.presets["Default"] = config["zones"]
                        loaded = True
            except: pass

        if not loaded or not self.presets.get(self.active_preset):
            self.presets["Default"] = [
                {"window_title": "Code", "pos": "Fill Space", "stat": "Fill (Any)", "val": ""},
                {"window_title": "Netflix", "pos": "Bottom-Left", "stat": "Aspect Ratio", "val": "16:9"},
                {"window_title": "Chrome", "pos": "Top-Left", "stat": "Height (px)", "val": "432"}
            ]
            self.active_preset = "Default"
            self.preset_modes["Default"] = "Equal Sizes"

        self.populate_presets()

    def populate_presets(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItems(list(self.presets.keys()))
        if self.active_preset in self.presets:
            self.preset_combo.setCurrentText(self.active_preset)
        self.preset_combo.blockSignals(False)
        self.load_preset(self.active_preset)

    def load_preset(self, name):
        for row in self.rows[:]:
            self.rows_layout.removeWidget(row)
            row.deleteLater()
        self.rows.clear()

        zones = self.presets.get(name, [])
        mode = self.preset_modes.get(name)
        if not mode and zones and isinstance(zones, list) and len(zones) > 0:
            mode = zones[0].get("split_mode")
        if not mode:
            mode = "Maximize Size" if "PiP" in name else "Equal Sizes"

        self.split_combo.blockSignals(True)
        self.split_combo.setCurrentText(mode)
        self.split_combo.blockSignals(False)

        for z in zones:
            self.add_row(z)

        self.update_preview()

    def on_preset_changed(self, name):
        if name and name in self.presets:
            self.active_preset = name
            self.load_preset(name)

    def on_split_mode_changed(self):
        mode = self.split_combo.currentText()
        self.preset_modes[self.active_preset] = mode
        self.presets[self.active_preset] = self._get_current_zones_with_rects()
        self.save_to_disk()
        self.update_preview()

    def _get_current_zones_with_rects(self):
        zones_data = []
        mode = self.split_combo.currentText()
        for row in self.rows:
            data = row.get_data()
            if data["window_title"]:
                data["split_mode"] = mode
                zones_data.append(data)

        screen = self.screen().geometry()
        return self.calculate_rects(zones_data, screen.width(), screen.height(), split_mode=mode)

    def save_preset_as(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset Name:", text=self.active_preset)
        if ok and name.strip():
            name = name.strip()
            self.active_preset = name
            self.preset_modes[name] = self.split_combo.currentText()
            self.presets[name] = self._get_current_zones_with_rects()

            if self.preset_combo.findText(name) == -1:
                self.preset_combo.blockSignals(True)
                self.preset_combo.addItem(name)
                self.preset_combo.blockSignals(False)

            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText(name)
            self.preset_combo.blockSignals(False)

            self.save_to_disk()

    def delete_preset(self):
        if len(self.presets) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "You must have at least one preset.")
            return

        reply = QMessageBox.question(self, "Delete Preset", f"Are you sure you want to delete '{self.active_preset}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            del self.presets[self.active_preset]
            if self.active_preset in self.preset_modes:
                del self.preset_modes[self.active_preset]
            self.active_preset = list(self.presets.keys())[0]
            self.populate_presets()
            self.save_to_disk()

    def save_to_disk(self):
        self.preset_modes[self.active_preset] = self.split_combo.currentText()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "active_preset": self.active_preset,
                "presets": self.presets,
                "preset_modes": self.preset_modes
            }, f, indent=2)

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

    def update_preview(self):
        zones_data = []
        mode = self.split_combo.currentText()
        for row in self.rows:
            data = row.get_data()
            if not data["window_title"]:
                data["window_title"] = "Empty"
            data["split_mode"] = mode
            zones_data.append(data)

        screen = self.screen().geometry()
        zones_data = self.calculate_rects(zones_data, screen.width(), screen.height(), split_mode=mode)
        self.preview.update_zones(zones_data, screen)

    def calculate_rects(self, zones, screen_w, screen_h, split_mode="Maximize Size"):
        rem_x, rem_y, rem_w, rem_h = 0, 0, screen_w, screen_h

        def get_val(z, max_val, is_width=True):
            stat = z.get('stat', '')
            val = z.get('val', '0')
            try:
                if stat == "Width (px)" and is_width: return int(val)
                if stat in ["Height (px)", "Min Height (px)"] and not is_width: return int(val)
                if stat == "Width (%)" and is_width: return int(max_val * float(val) / 100.0)
                if stat in ["Height (%)", "Min Height (%)"] and not is_width: return int(max_val * float(val) / 100.0)
            except: pass
            return 0

        def parse_ar(val):
            try:
                v = val.replace(':', '/')
                num, den = map(float, v.split('/'))
                return num / den
            except:
                return 16.0 / 9.0

        def is_fill(z):
            return z.get('pos') == "Fill Space" or z.get('stat') == "Fill (Any)"

        # Pass 1: Explicit Side Snaps (Left, Right, Top, Bottom)
        for z in zones:
            pos = z.get('pos', '')
            if is_fill(z) or pos in ["Top-Left", "Bottom-Left", "Top-Right", "Bottom-Right"]:
                continue

            stat = z.get('stat', '')
            if pos in ["Right", "Left"]:
                if "Aspect Ratio" in stat:
                    w = int(rem_h * parse_ar(z.get('val', '')))
                else:
                    w = get_val(z, rem_w, True) or (rem_w // 2)

                w = max(0, min(w, rem_w))
                if pos == "Right":
                    z['rect'] = {"x": rem_x + rem_w - w, "y": rem_y, "width": w, "height": rem_h}
                    rem_w -= w
                else:
                    z['rect'] = {"x": rem_x, "y": rem_y, "width": w, "height": rem_h}
                    rem_x += w
                    rem_w -= w

            elif pos in ["Top", "Bottom"]:
                if "Aspect Ratio" in stat:
                    h = int(rem_w / parse_ar(z.get('val', '')))
                else:
                    h = get_val(z, rem_h, False) or (rem_h // 2)

                h = max(0, min(h, rem_h))
                if pos == "Top":
                    z['rect'] = {"x": rem_x, "y": rem_y, "width": rem_w, "height": h}
                    rem_y += h
                    rem_h -= h
                else:
                    z['rect'] = {"x": rem_x, "y": rem_y + rem_h - h, "width": rem_w, "height": h}
                    rem_h -= h

        # Pass 2: Smart Corner Columns (Left and Right Columns)
        def solve_column(top_zone, bot_zone, col_x, total_h, total_w):
            if not top_zone and not bot_zone:
                return 0

            top_h, bot_h, col_w = 0, 0, 0

            if top_zone and bot_zone:
                top_stat = top_zone.get('stat', '')
                bot_stat = bot_zone.get('stat', '')

                def get_mode(ar_zone):
                    stat = ar_zone.get('stat', '')
                    if "Equal" in stat: return "Equal Sizes"
                    if "Max" in stat: return "Maximize Size"
                    return ar_zone.get('split_mode', split_mode)

                if "Height" in top_stat and "Aspect Ratio" in bot_stat:
                    min_top_h = get_val(top_zone, total_h, False)
                    min_top_h = max(0, min(min_top_h, total_h))
                    ar = parse_ar(bot_zone.get('val', ''))
                    mode = get_mode(bot_zone)
                    if mode == "Equal Sizes":
                        target_h = total_h // 2
                        top_h = max(min_top_h, target_h)
                        bot_h = total_h - top_h
                    else:
                        top_h = min_top_h
                        bot_h = total_h - top_h
                    col_w = int(bot_h * ar)
                elif "Height" in bot_stat and "Aspect Ratio" in top_stat:
                    min_bot_h = get_val(bot_zone, total_h, False)
                    min_bot_h = max(0, min(min_bot_h, total_h))
                    ar = parse_ar(top_zone.get('val', ''))
                    mode = get_mode(top_zone)
                    if mode == "Equal Sizes":
                        target_h = total_h // 2
                        bot_h = max(min_bot_h, target_h)
                        top_h = total_h - bot_h
                    else:
                        bot_h = min_bot_h
                        top_h = total_h - bot_h
                    col_w = int(top_h * ar)
                elif "Height" in top_stat and "Height" in bot_stat:
                    top_h = get_val(top_zone, total_h, False)
                    bot_h = get_val(bot_zone, total_h, False)
                    col_w = max(get_val(top_zone, total_w, True), get_val(bot_zone, total_w, True)) or (total_w // 2)
                elif "Aspect Ratio" in top_stat and "Aspect Ratio" in bot_stat:
                    top_h = total_h // 2
                    bot_h = total_h - top_h
                    ar_top = parse_ar(top_zone.get('val', ''))
                    ar_bot = parse_ar(bot_zone.get('val', ''))
                    col_w = max(int(top_h * ar_top), int(bot_h * ar_bot))
                else:
                    top_h = get_val(top_zone, total_h, False) or (total_h // 2)
                    bot_h = total_h - top_h
                    col_w = max(get_val(top_zone, total_w, True), get_val(bot_zone, total_w, True)) or (total_w // 2)
            elif top_zone:
                top_stat = top_zone.get('stat', '')
                if "Aspect Ratio" in top_stat:
                    top_h = total_h
                    col_w = int(top_h * parse_ar(top_zone.get('val', '')))
                else:
                    top_h = get_val(top_zone, total_h, False) or total_h
                    col_w = get_val(top_zone, total_w, True) or (total_w // 2)
            elif bot_zone:
                bot_stat = bot_zone.get('stat', '')
                if "Aspect Ratio" in bot_stat:
                    bot_h = total_h
                    col_w = int(bot_h * parse_ar(bot_zone.get('val', '')))
                else:
                    bot_h = get_val(bot_zone, total_h, False) or total_h
                    col_w = get_val(bot_zone, total_w, True) or (total_w // 2)

            col_w = max(0, min(col_w, total_w))

            if top_zone:
                top_zone['rect'] = {"x": col_x, "y": rem_y, "width": col_w, "height": top_h}
            if bot_zone:
                bot_y = rem_y + (top_h if top_zone else (total_h - bot_h))
                bot_zone['rect'] = {"x": col_x, "y": bot_y, "width": col_w, "height": bot_h}

            return col_w

        # Solve Left Column
        tl_zone = next((z for z in zones if z.get('pos') == "Top-Left"), None)
        bl_zone = next((z for z in zones if z.get('pos') == "Bottom-Left"), None)
        left_w = solve_column(tl_zone, bl_zone, rem_x, rem_h, rem_w)
        rem_x += left_w
        rem_w -= left_w

        # Solve Right Column
        tr_zone = next((z for z in zones if z.get('pos') == "Top-Right"), None)
        br_zone = next((z for z in zones if z.get('pos') == "Bottom-Right"), None)
        right_x = rem_x + rem_w
        right_w = solve_column(tr_zone, br_zone, right_x - min(rem_w, rem_w // 2), rem_h, rem_w)
        if right_w > 0:
            if tr_zone: tr_zone['rect']['x'] = rem_x + rem_w - right_w
            if br_zone: br_zone['rect']['x'] = rem_x + rem_w - right_w
            rem_w -= right_w

        # Pass 3: Fill Remaining Space
        fill_zones = [z for z in zones if 'rect' not in z or is_fill(z)]
        if fill_zones:
            n = len(fill_zones)
            fill_w = rem_w // n
            for i, z in enumerate(fill_zones):
                fw = fill_w if i < n - 1 else (rem_w - i * fill_w)
                z['rect'] = {"x": rem_x + i * fill_w, "y": rem_y, "width": max(0, fw), "height": rem_h}

        return zones

    def apply_layout(self):
        self.presets[self.active_preset] = self._get_current_zones_with_rects()
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
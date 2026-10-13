from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QLineEdit, QComboBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

try:
    from core.win_utils import get_open_windows
    from core.config import (
        CONFIG_PATH,
        DEFAULT_KEYBINDINGS,
        load_config,
        save_config,
        parse_hotkey,
        format_hotkey_display
    )
except (ImportError, ValueError):
    from ..core.win_utils import get_open_windows
    from ..core.config import (
        CONFIG_PATH,
        DEFAULT_KEYBINDINGS,
        load_config,
        save_config,
        parse_hotkey,
        format_hotkey_display
    )

class AppSelectDialog(QDialog):
    """
    Modal dialog allowing users to pick an active window from all running Alt-Tab windows.
    """
    def __init__(self, parent=None, return_hwnd=False):
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
        if 0 <= idx < len(self.window_items):
            self.selected_hwnd = self.window_items[idx][1]
            self.accept()
        else:
            self.reject()

    def get_selected(self):
        if self.list.currentItem():
            return self.list.currentItem().text()
        return ""


class SettingsDialog(QDialog):
    """
    Modal dialog allowing users to configure their 3 global keybindings:
    1. Open Editor / GUI (Default: Ctrl+Win+Z)
    2. Snapping Drag Modifier (Default: Ctrl)
    3. Apply Current Layout (Default: Win+Shift+Z)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WindowZones Settings")
        self.setMinimumWidth(480)

        self.config_data = load_config(CONFIG_PATH)
        self.keybindings = dict(self.config_data.get("keybindings", DEFAULT_KEYBINDINGS))

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        # Header
        lbl_title = QLabel("Keyboard Shortcuts & Hotkeys")
        lbl_title.setObjectName("header_title")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel("Customize your 3 primary shortcuts. Changes will be saved to config.json.")
        lbl_desc.setObjectName("subtitle")
        lbl_desc.setStyleSheet("color: #8c8c9a; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(lbl_desc)

        # Settings Card Frame
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(14)

        # Shortcut 1: Open GUI
        box_gui = QVBoxLayout()
        box_gui.setSpacing(4)
        lbl_gui = QLabel("1. Open Editor Shortcut:")
        lbl_gui.setObjectName("field_label")
        self.edit_gui = QLineEdit()
        self.edit_gui.setPlaceholderText("e.g. Ctrl+Win+Z")
        self.edit_gui.setText(self.keybindings.get("open_gui", DEFAULT_KEYBINDINGS["open_gui"]))
        box_gui.addWidget(lbl_gui)
        box_gui.addWidget(self.edit_gui)
        card_layout.addLayout(box_gui)

        # Shortcut 2: Snap Drag Modifier
        box_snap = QVBoxLayout()
        box_snap.setSpacing(4)
        lbl_snap = QLabel("2. Window Drag Snapping Modifier:")
        lbl_snap.setObjectName("field_label")
        self.combo_snap = QComboBox()
        self.combo_snap.addItems(["Ctrl", "Shift", "Alt", "Win"])
        current_mod = self.keybindings.get("snap_modifier", DEFAULT_KEYBINDINGS["snap_modifier"])
        mod_idx = self.combo_snap.findText(current_mod, Qt.MatchFlag.MatchFixedString)
        if mod_idx >= 0:
            self.combo_snap.setCurrentIndex(mod_idx)
        box_snap.addWidget(lbl_snap)
        box_snap.addWidget(self.combo_snap)
        card_layout.addLayout(box_snap)

        # Shortcut 3: Apply Layout
        box_apply = QVBoxLayout()
        box_apply.setSpacing(4)
        lbl_apply = QLabel("3. Apply Current Layout Shortcut:")
        lbl_apply.setObjectName("field_label")
        self.edit_apply = QLineEdit()
        self.edit_apply.setPlaceholderText("e.g. Win+Shift+Z")
        self.edit_apply.setText(self.keybindings.get("apply_layout", DEFAULT_KEYBINDINGS["apply_layout"]))
        box_apply.addWidget(lbl_apply)
        box_apply.addWidget(self.edit_apply)
        card_layout.addLayout(box_apply)

        layout.addWidget(card)

        # Buttons footer
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_reset = QPushButton("Reset Defaults")
        btn_reset.setObjectName("secondary_action")
        btn_reset.clicked.connect(self.reset_defaults)
        btn_box.addWidget(btn_reset)

        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self.save_settings)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def reset_defaults(self):
        self.edit_gui.setText(DEFAULT_KEYBINDINGS["open_gui"])
        idx = self.combo_snap.findText(DEFAULT_KEYBINDINGS["snap_modifier"])
        if idx >= 0:
            self.combo_snap.setCurrentIndex(idx)
        self.edit_apply.setText(DEFAULT_KEYBINDINGS["apply_layout"])

    def save_settings(self):
        open_gui_val = self.edit_gui.text().strip()
        snap_mod_val = self.combo_snap.currentText().strip()
        apply_layout_val = self.edit_apply.text().strip()

        # Validate Open GUI hotkey
        mod1, vk1 = parse_hotkey(open_gui_val)
        if mod1 is None or vk1 is None:
            QMessageBox.warning(
                self,
                "Invalid Shortcut",
                f"The Open Editor shortcut '{open_gui_val}' is invalid.\nPlease use a combination like 'Ctrl+Win+Z' or 'Win+Shift+A'."
            )
            return

        # Validate Apply Layout hotkey
        mod2, vk2 = parse_hotkey(apply_layout_val)
        if mod2 is None or vk2 is None:
            QMessageBox.warning(
                self,
                "Invalid Shortcut",
                f"The Apply Layout shortcut '{apply_layout_val}' is invalid.\nPlease use a combination like 'Win+Shift+Z' or 'Ctrl+Alt+S'."
            )
            return

        self.keybindings = {
            "open_gui": open_gui_val,
            "snap_modifier": snap_mod_val,
            "apply_layout": apply_layout_val
        }

        self.config_data["keybindings"] = self.keybindings
        save_config(self.config_data, CONFIG_PATH)
        self.accept()

    def get_keybindings(self):
        return self.keybindings
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QInputDialog
)
from PyQt6.QtCore import pyqtSignal

try:
    from ui.widgets import NoWheelComboBox
    from ui.dialogs import AppSelectDialog
    from core.win_utils import get_window_dimensions, calculate_window_aspect_ratio
except (ImportError, ValueError):
    from .widgets import NoWheelComboBox
    from .dialogs import AppSelectDialog
    from ..core.win_utils import get_window_dimensions, calculate_window_aspect_ratio

class ThreeWindowPanel(QFrame):
    """
    Panel controlling the 3-Window Setup (Code + Chrome + Media).
    """
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._updating = False

        self.layout_settings = {}
        self.chrome_sizes = {}
        self.media_profiles = {}
        self.app_titles = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Row 1: VS Code Placement & Match
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_side = QLabel("Code Side:")
        lbl_side.setObjectName("field_label")
        row1.addWidget(lbl_side)

        self.vscode_side_combo = NoWheelComboBox()
        self.vscode_side_combo.addItems(["Right", "Left"])
        self.vscode_side_combo.setFixedWidth(85)
        self.vscode_side_combo.currentTextChanged.connect(self._on_vscode_side_changed)
        row1.addWidget(self.vscode_side_combo)

        lbl_code_title = QLabel("App:")
        lbl_code_title.setObjectName("field_label")
        row1.addWidget(lbl_code_title)

        self.code_title_input = QLineEdit()
        self.code_title_input.setPlaceholderText("Code Window Title")
        self.code_title_input.textChanged.connect(self._on_titles_changed)
        row1.addWidget(self.code_title_input, 1)

        btn_pick_code = QPushButton("Pick...")
        btn_pick_code.setObjectName("secondary_action")
        btn_pick_code.clicked.connect(self._pick_code_app)
        row1.addWidget(btn_pick_code)

        layout.addLayout(row1)

        # Row 2: Chrome Sizing & Match
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_chrome = QLabel("Chrome Size:")
        lbl_chrome.setObjectName("field_label")
        row2.addWidget(lbl_chrome)

        self.chrome_sizing_combo = NoWheelComboBox()
        self.chrome_sizing_combo.setMinimumWidth(120)
        self.chrome_sizing_combo.currentTextChanged.connect(self._on_chrome_sizing_changed)
        row2.addWidget(self.chrome_sizing_combo)

        self.chrome_title_input = QLineEdit()
        self.chrome_title_input.setPlaceholderText("Chrome Window Title")
        self.chrome_title_input.textChanged.connect(self._on_titles_changed)
        row2.addWidget(self.chrome_title_input, 1)

        btn_pick_chrome = QPushButton("Pick...")
        btn_pick_chrome.setObjectName("secondary_action")
        btn_pick_chrome.clicked.connect(self._pick_chrome_app)
        row2.addWidget(btn_pick_chrome)

        btn_detect_chrome = QPushButton("🎯 Save Size")
        btn_detect_chrome.setObjectName("secondary_action")
        btn_detect_chrome.setToolTip("Inspect window to detect and save height")
        btn_detect_chrome.clicked.connect(self._detect_and_save_chrome_size)
        row2.addWidget(btn_detect_chrome)

        btn_add_chrome = QPushButton("+ Size")
        btn_add_chrome.setObjectName("secondary_action")
        btn_add_chrome.clicked.connect(self._add_custom_chrome_size)
        row2.addWidget(btn_add_chrome)

        btn_del_chrome = QPushButton("✕")
        btn_del_chrome.setObjectName("danger")
        btn_del_chrome.setToolTip("Delete selected size profile")
        btn_del_chrome.clicked.connect(self._delete_current_chrome_size)
        row2.addWidget(btn_del_chrome)

        layout.addLayout(row2)

        # Row 3: Media Aspect Ratio & Match
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        lbl_media_ar = QLabel("Media Ratio:")
        lbl_media_ar.setObjectName("field_label")
        row3.addWidget(lbl_media_ar)

        self.media_ar_combo = NoWheelComboBox()
        self.media_ar_combo.setMinimumWidth(130)
        self.media_ar_combo.currentTextChanged.connect(self._on_media_ar_changed)
        row3.addWidget(self.media_ar_combo)

        self.media_title_input = QLineEdit()
        self.media_title_input.setPlaceholderText("Media Window Title")
        self.media_title_input.textChanged.connect(self._on_titles_changed)
        row3.addWidget(self.media_title_input, 1)

        btn_pick_media = QPushButton("Pick...")
        btn_pick_media.setObjectName("secondary_action")
        btn_pick_media.clicked.connect(self._pick_media_app)
        row3.addWidget(btn_pick_media)

        btn_detect_ar = QPushButton("🎯 Save AR")
        btn_detect_ar.setObjectName("secondary_action")
        btn_detect_ar.setToolTip("Inspect window to detect and save aspect ratio")
        btn_detect_ar.clicked.connect(self._detect_and_save_media_ar)
        row3.addWidget(btn_detect_ar)

        btn_add_ar = QPushButton("+ AR")
        btn_add_ar.setObjectName("secondary_action")
        btn_add_ar.clicked.connect(self._add_custom_ar)
        row3.addWidget(btn_add_ar)

        btn_del_ar = QPushButton("✕")
        btn_del_ar.setObjectName("danger")
        btn_del_ar.setToolTip("Delete selected AR profile")
        btn_del_ar.clicked.connect(self._delete_current_ar)
        row3.addWidget(btn_del_ar)

        layout.addLayout(row3)

    def load_settings(self, layout_settings, chrome_sizes, media_profiles, app_titles):
        self._updating = True
        self.layout_settings = layout_settings
        self.chrome_sizes = chrome_sizes
        self.media_profiles = media_profiles
        self.app_titles = app_titles

        self.vscode_side_combo.setCurrentText(self.layout_settings.get("vscode_side", "Right"))
        self.code_title_input.setText(self.app_titles.get("vscode", "Visual Studio Code"))
        self.chrome_title_input.setText(self.app_titles.get("chrome", "Google Chrome"))
        self.media_title_input.setText(self.app_titles.get("media", "Netflix"))

        self.refresh_chrome_sizing_combo()
        self.refresh_media_profiles_combo()
        self._updating = False

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

    def _on_vscode_side_changed(self, text):
        if self._updating:
            return
        self.layout_settings["vscode_side"] = text
        self.settings_changed.emit()

    def _on_chrome_sizing_changed(self, text):
        if self._updating or not text:
            return
        self.layout_settings["chrome_sizing"] = text
        self.settings_changed.emit()

    def _on_media_ar_changed(self, name):
        if self._updating or not name:
            return
        self.layout_settings["active_media_profile"] = name
        self.settings_changed.emit()

    def _on_titles_changed(self):
        if self._updating:
            return
        self.app_titles["vscode"] = self.code_title_input.text().strip() or "Visual Studio Code"
        self.app_titles["chrome"] = self.chrome_title_input.text().strip() or "Google Chrome"
        self.app_titles["media"] = self.media_title_input.text().strip() or "Netflix"
        self.settings_changed.emit()

    def _pick_code_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.code_title_input.setText(title)

    def _pick_chrome_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.chrome_title_input.setText(title)

    def _pick_media_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.media_title_input.setText(title)

    def _detect_and_save_chrome_size(self):
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
                    self.app_titles["chrome"] = clean_name
                self.refresh_chrome_sizing_combo()
                self.settings_changed.emit()

    def _add_custom_chrome_size(self):
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
            self.settings_changed.emit()

    def _delete_current_chrome_size(self):
        curr = self.chrome_sizing_combo.currentText()
        if curr == "Equal Size":
            QMessageBox.warning(self, "Cannot Delete", "'Equal Size' is default and cannot be deleted.")
            return
        if curr in self.chrome_sizes:
            del self.chrome_sizes[curr]
            self.layout_settings["chrome_sizing"] = "Equal Size"
            self.refresh_chrome_sizing_combo()
            self.settings_changed.emit()

    def _detect_and_save_media_ar(self):
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
                    self.app_titles["media"] = clean_name
                self.refresh_media_profiles_combo()
                self.settings_changed.emit()

    def _add_custom_ar(self):
        ratio, ok = QInputDialog.getText(self, "Add Aspect Ratio", "Enter aspect ratio (e.g. 16:9, 4:3, 2.39:1):", text="16:9")
        if ok and ratio.strip():
            ratio = ratio.strip()
            name, n_ok = QInputDialog.getText(self, "Aspect Ratio Name", "Enter name for this aspect ratio:", text=ratio)
            if n_ok and name.strip():
                p_name = name.strip()
                self.media_profiles[p_name] = ratio
                self.layout_settings["active_media_profile"] = p_name
                self.refresh_media_profiles_combo()
                self.settings_changed.emit()

    def _delete_current_ar(self):
        curr = self.media_ar_combo.currentText()
        if len(self.media_profiles) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "You must have at least one media aspect ratio profile.")
            return
        if curr in self.media_profiles:
            del self.media_profiles[curr]
            self.layout_settings["active_media_profile"] = list(self.media_profiles.keys())[0]
            self.refresh_media_profiles_combo()
            self.settings_changed.emit()
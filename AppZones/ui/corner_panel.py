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

class CornerPanel(QFrame):
    """
    Panel controlling Fullscreen + Corner Media layout.
    """
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._updating = False

        self.corner_settings = {}
        self.media_profiles = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Corner Row 1: Target Windows & Corner Placement
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_fs = QLabel("Fullscreen App:")
        lbl_fs.setObjectName("field_label")
        row1.addWidget(lbl_fs)

        self.fs_title_input = QLineEdit()
        self.fs_title_input.setPlaceholderText("Fullscreen Window Title")
        self.fs_title_input.textChanged.connect(self._on_corner_setting_changed)
        row1.addWidget(self.fs_title_input, 1)

        btn_pick_fs = QPushButton("Pick...")
        btn_pick_fs.setObjectName("secondary_action")
        btn_pick_fs.clicked.connect(self._pick_fullscreen_app)
        row1.addWidget(btn_pick_fs)

        lbl_corner_pos = QLabel("Corner:")
        lbl_corner_pos.setObjectName("field_label")
        row1.addWidget(lbl_corner_pos)

        self.corner_combo = NoWheelComboBox()
        self.corner_combo.addItems(["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left"])
        self.corner_combo.currentTextChanged.connect(self._on_corner_setting_changed)
        row1.addWidget(self.corner_combo)

        lbl_corner_media = QLabel("Media App:")
        lbl_corner_media.setObjectName("field_label")
        row1.addWidget(lbl_corner_media)

        self.corner_media_input = QLineEdit()
        self.corner_media_input.setPlaceholderText("Corner Media Title")
        self.corner_media_input.textChanged.connect(self._on_corner_setting_changed)
        row1.addWidget(self.corner_media_input, 1)

        btn_pick_corner_media = QPushButton("Pick...")
        btn_pick_corner_media.setObjectName("secondary_action")
        btn_pick_corner_media.clicked.connect(self._pick_corner_media_app)
        row1.addWidget(btn_pick_corner_media)

        layout.addLayout(row1)

        # Corner Row 2: Max Dimensions & Aspect Ratio Fitting
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_max_size = QLabel("Max Size:")
        lbl_max_size.setObjectName("field_label")
        row2.addWidget(lbl_max_size)

        self.corner_max_w_input = QLineEdit()
        self.corner_max_w_input.setPlaceholderText("Max W")
        self.corner_max_w_input.setFixedWidth(70)
        self.corner_max_w_input.textChanged.connect(self._on_corner_setting_changed)
        row2.addWidget(self.corner_max_w_input)

        lbl_x = QLabel("×")
        lbl_x.setObjectName("field_label")
        row2.addWidget(lbl_x)

        self.corner_max_h_input = QLineEdit()
        self.corner_max_h_input.setPlaceholderText("Max H")
        self.corner_max_h_input.setFixedWidth(70)
        self.corner_max_h_input.textChanged.connect(self._on_corner_setting_changed)
        row2.addWidget(self.corner_max_h_input)

        btn_save_current_corner_size = QPushButton("🎯 Save Current Size")
        btn_save_current_corner_size.setObjectName("secondary_action")
        btn_save_current_corner_size.setToolTip("Inspect window to save its width and height as max size")
        btn_save_current_corner_size.clicked.connect(self._detect_and_save_corner_max_size)
        row2.addWidget(btn_save_current_corner_size)

        lbl_corner_ar = QLabel("Aspect Ratio:")
        lbl_corner_ar.setObjectName("field_label")
        row2.addWidget(lbl_corner_ar)

        self.corner_ar_combo = NoWheelComboBox()
        self.corner_ar_combo.setMinimumWidth(130)
        self.corner_ar_combo.currentTextChanged.connect(self._on_corner_ar_changed)
        row2.addWidget(self.corner_ar_combo)

        btn_detect_corner_ar = QPushButton("🎯 Save AR")
        btn_detect_corner_ar.setObjectName("secondary_action")
        btn_detect_corner_ar.setToolTip("Inspect window to detect and save aspect ratio")
        btn_detect_corner_ar.clicked.connect(self._detect_and_save_corner_ar)
        row2.addWidget(btn_detect_corner_ar)

        btn_add_corner_ar = QPushButton("+ AR")
        btn_add_corner_ar.setObjectName("secondary_action")
        btn_add_corner_ar.clicked.connect(self._add_custom_corner_ar)
        row2.addWidget(btn_add_corner_ar)

        row2.addStretch()
        layout.addLayout(row2)

    def load_settings(self, corner_settings, media_profiles):
        self._updating = True
        self.corner_settings = corner_settings
        self.media_profiles = media_profiles

        self.fs_title_input.setText(self.corner_settings.get("fullscreen_app", ""))
        self.corner_combo.setCurrentText(self.corner_settings.get("corner", "Bottom-Right"))
        self.corner_media_input.setText(self.corner_settings.get("media_app", "Netflix"))
        self.corner_max_w_input.setText(str(self.corner_settings.get("max_width", 720)))
        self.corner_max_h_input.setText(str(self.corner_settings.get("max_height", 450)))
        self.refresh_corner_ar_combo()
        self._updating = False

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

    def _on_corner_setting_changed(self):
        if self._updating:
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
        self.settings_changed.emit()

    def _on_corner_ar_changed(self, name):
        if self._updating or not name:
            return
        self.corner_settings["active_media_profile"] = name
        self.settings_changed.emit()

    def _pick_fullscreen_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.fs_title_input.setText(title)

    def _pick_corner_media_app(self):
        dialog = AppSelectDialog(self)
        if dialog.exec():
            selected = dialog.get_selected()
            if selected:
                title = selected.split(" - ")[-1]
                self.corner_media_input.setText(title)

    def _detect_and_save_corner_max_size(self):
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
            self.settings_changed.emit()

    def _detect_and_save_corner_ar(self):
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
                self.refresh_corner_ar_combo()
                self.settings_changed.emit()

    def _add_custom_corner_ar(self):
        ratio, ok = QInputDialog.getText(self, "Add Aspect Ratio", "Enter aspect ratio (e.g. 16:9, 4:3, 2.39:1):", text="16:9")
        if ok and ratio.strip():
            ratio = ratio.strip()
            name, n_ok = QInputDialog.getText(self, "Aspect Ratio Name", "Enter name for this aspect ratio:", text=ratio)
            if n_ok and name.strip():
                p_name = name.strip()
                self.media_profiles[p_name] = ratio
                self.corner_settings["active_media_profile"] = p_name
                self.refresh_corner_ar_combo()
                self.settings_changed.emit()
import sys
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QEvent

try:
    from ui.styles import STYLESHEET
    from ui.preview_widget import LiveLayoutPreview
    from ui.aspect_ratio_manager import AspectRatioRow, AddAspectRatioDialog
    from ui.dialogs import SettingsDialog
    from core.config import (
        CONFIG_PATH,
        MAIN_SCRIPT,
        DEFAULT_CHROME_SIZES,
        DEFAULT_MEDIA_PROFILES,
        DEFAULT_LAYOUT_SETTINGS,
        DEFAULT_CORNER_SETTINGS,
        DEFAULT_APP_TITLES_3WIN,
        DEFAULT_KEYBINDINGS,
        load_config,
        save_config,
    )
    from core.layout_engine import (
        calculate_smart_layout,
        calculate_fullscreen_corner_rects
    )
    from core.detector import detector
    from core.win_utils import get_open_windows
except (ImportError, ValueError):
    from .styles import STYLESHEET
    from .preview_widget import LiveLayoutPreview
    from .aspect_ratio_manager import AspectRatioRow, AddAspectRatioDialog
    from .dialogs import SettingsDialog
    from ..core.config import (
        CONFIG_PATH,
        MAIN_SCRIPT,
        DEFAULT_CHROME_SIZES,
        DEFAULT_MEDIA_PROFILES,
        DEFAULT_LAYOUT_SETTINGS,
        DEFAULT_CORNER_SETTINGS,
        DEFAULT_APP_TITLES_3WIN,
        DEFAULT_KEYBINDINGS,
        load_config,
        save_config,
    )
    from ..core.layout_engine import (
        calculate_smart_layout,
        calculate_fullscreen_corner_rects
    )
    from ..core.detector import detector
    from ..core.win_utils import get_open_windows


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppZones")
        self.resize(780, 720)
        self.setMinimumSize(700, 600)
        self.setStyleSheet(STYLESHEET)

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.active_mode = "3_window"
        self.chrome_sizes = dict(DEFAULT_CHROME_SIZES)
        self.media_profiles = dict(DEFAULT_MEDIA_PROFILES)
        self.layout_settings = dict(DEFAULT_LAYOUT_SETTINGS)
        self.corner_settings = dict(DEFAULT_CORNER_SETTINGS)
        self.app_titles_3win = dict(DEFAULT_APP_TITLES_3WIN)
        self.keybindings = dict(DEFAULT_KEYBINDINGS)

        self.init_ui()
        self.load_data()

        # Auto-refresh detection status and live preview every 1.5 seconds
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.on_periodic_refresh)
        self.poll_timer.start(1500)

    def init_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 18, 24, 18)
        main_layout.setSpacing(12)

        # 1. Header Bar
        header = QHBoxLayout()
        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)

        title = QLabel("AppZones")
        title.setObjectName("app_title")
        subtitle = QLabel("Intelligent Workspace Orchestrator")
        subtitle.setObjectName("app_subtitle")

        titles_box.addWidget(title)
        titles_box.addWidget(subtitle)
        header.addLayout(titles_box)
        header.addStretch()

        screen = self.screen().geometry()
        self.display_label = QLabel(f"{screen.width()} × {screen.height()}")
        self.display_label.setStyleSheet("color: #636366; font-size: 11px; font-weight: 600;")
        header.addWidget(self.display_label)

        self.btn_settings = QPushButton("Preferences")
        self.btn_settings.setObjectName("secondary_action")
        self.btn_settings.clicked.connect(self.open_settings)
        header.addWidget(self.btn_settings)

        main_layout.addLayout(header)

        # 2. Live Intelligence Status Card
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        status_layout = QHBoxLayout(self.status_card)
        status_layout.setContentsMargins(14, 10, 14, 10)
        status_layout.setSpacing(12)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #30d158; font-size: 14px;")
        status_layout.addWidget(self.status_dot)

        status_text_box = QVBoxLayout()
        status_text_box.setSpacing(2)
        self.status_headline = QLabel("Detecting workspace state...")
        self.status_headline.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 13px;")
        self.status_detail = QLabel("Active layout recalculates automatically when media opens or closes.")
        self.status_detail.setStyleSheet("color: #8e8e93; font-size: 11px;")
        status_text_box.addWidget(self.status_headline)
        status_text_box.addWidget(self.status_detail)
        status_layout.addLayout(status_text_box)
        status_layout.addStretch()

        main_layout.addWidget(self.status_card)

        # 3. Embedded Live Layout Preview Card (Clean, scaled mini-map)
        preview_card = QFrame()
        preview_card.setObjectName("card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(14, 10, 14, 10)
        preview_layout.setSpacing(6)

        prev_header = QHBoxLayout()
        prev_title = QLabel("LIVE WORKSPACE PREVIEW")
        prev_title.setObjectName("section_heading")
        prev_header.addWidget(prev_title)
        prev_header.addStretch()
        preview_layout.addLayout(prev_header)

        self.live_preview = LiveLayoutPreview(self)
        preview_layout.addWidget(self.live_preview)

        main_layout.addWidget(preview_card)

        # 4. Workspace Preferences Card
        pref_card = QFrame()
        pref_card.setObjectName("card")
        pref_layout = QVBoxLayout(pref_card)
        pref_layout.setContentsMargins(16, 12, 16, 12)
        pref_layout.setSpacing(10)

        sec_title = QLabel("WORKSPACE CONTROLS")
        sec_title.setObjectName("section_heading")
        pref_layout.addWidget(sec_title)

        # Row 1: VS Code Position & Chrome Size
        row1 = QHBoxLayout()
        lbl_vsc = QLabel("VS Code Position:")
        lbl_vsc.setObjectName("card_title")
        row1.addWidget(lbl_vsc)

        self.btn_side_left = QPushButton("Left")
        self.btn_side_left.setProperty("class", "segment_btn")
        self.btn_side_left.setCheckable(True)
        self.btn_side_left.clicked.connect(lambda: self.set_vscode_side("Left"))
        row1.addWidget(self.btn_side_left)

        self.btn_side_right = QPushButton("Right")
        self.btn_side_right.setProperty("class", "segment_btn")
        self.btn_side_right.setCheckable(True)
        self.btn_side_right.clicked.connect(lambda: self.set_vscode_side("Right"))
        row1.addWidget(self.btn_side_right)

        row1.addSpacing(20)

        lbl_chr = QLabel("Chrome Size:")
        lbl_chr.setObjectName("card_title")
        row1.addWidget(lbl_chr)

        self.btn_chr_equal = QPushButton("Equal")
        self.btn_chr_equal.setProperty("class", "segment_btn")
        self.btn_chr_equal.setCheckable(True)
        self.btn_chr_equal.clicked.connect(lambda: self.set_chrome_sizing("Equal Size"))
        row1.addWidget(self.btn_chr_equal)

        self.btn_chr_432 = QPushButton("432 px")
        self.btn_chr_432.setProperty("class", "segment_btn")
        self.btn_chr_432.setCheckable(True)
        self.btn_chr_432.clicked.connect(lambda: self.set_chrome_sizing("432px"))
        row1.addWidget(self.btn_chr_432)

        self.btn_chr_590 = QPushButton("590 px")
        self.btn_chr_590.setProperty("class", "segment_btn")
        self.btn_chr_590.setCheckable(True)
        self.btn_chr_590.clicked.connect(lambda: self.set_chrome_sizing("590px"))
        row1.addWidget(self.btn_chr_590)

        row1.addStretch()
        pref_layout.addLayout(row1)

        # Row 2: Corner Popup Position (when 1 app + media)
        row2 = QHBoxLayout()
        lbl_crn = QLabel("Popup Corner (1 App + Media):")
        lbl_crn.setObjectName("card_title")
        row2.addWidget(lbl_crn)

        self.corner_btns = {}
        for c_name in ["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left"]:
            btn = QPushButton(c_name.replace("-", " "))
            btn.setProperty("class", "segment_btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=c_name: self.set_popup_corner(c))
            self.corner_btns[c_name] = btn
            row2.addWidget(btn)

        row2.addStretch()
        pref_layout.addLayout(row2)

        main_layout.addWidget(pref_card)

        # 5. Aspect Ratio Categories Card
        profiles_card = QFrame()
        profiles_card.setObjectName("card")
        profiles_layout = QVBoxLayout(profiles_card)
        profiles_layout.setContentsMargins(16, 12, 16, 12)
        profiles_layout.setSpacing(8)

        header_row = QHBoxLayout()
        prof_heading = QLabel("ASPECT RATIO CATEGORIES")
        prof_heading.setObjectName("section_heading")
        header_row.addWidget(prof_heading)
        header_row.addStretch()

        # Only one primary "Add Aspect Ratio" button upfront!
        btn_add_aspect_ratio = QPushButton("+ Add Aspect Ratio")
        btn_add_aspect_ratio.setObjectName("secondary_action")
        btn_add_aspect_ratio.clicked.connect(self.add_aspect_ratio_dialog)
        header_row.addWidget(btn_add_aspect_ratio)
        profiles_layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        self.profiles_container = QWidget()
        self.profiles_container.setStyleSheet("background: transparent;")
        self.profiles_list_layout = QVBoxLayout(self.profiles_container)
        self.profiles_list_layout.setContentsMargins(0, 0, 0, 0)
        self.profiles_list_layout.setSpacing(6)
        scroll.setWidget(self.profiles_container)
        profiles_layout.addWidget(scroll)

        main_layout.addWidget(profiles_card, 1)

        # 6. Bottom Actions Footer
        footer = QHBoxLayout()
        snap_key = self.keybindings.get("snap_modifier", "Ctrl")
        self.tip_label = QLabel(f"Hold {snap_key} while dragging any window to snap.")
        self.tip_label.setStyleSheet("color: #636366; font-size: 11px;")
        footer.addWidget(self.tip_label)
        footer.addStretch()

        self.btn_apply = QPushButton("Apply Layout")
        self.btn_apply.setObjectName("primary_action")
        self.btn_apply.clicked.connect(self.apply_layout)
        footer.addWidget(self.btn_apply)

        main_layout.addLayout(footer)

    def set_vscode_side(self, side):
        self.layout_settings["vscode_side"] = side
        self.btn_side_left.setChecked(side == "Left")
        self.btn_side_right.setChecked(side == "Right")
        self.save_to_disk()
        self.update_dimensions_display()

    def set_chrome_sizing(self, sizing):
        self.layout_settings["chrome_sizing"] = sizing
        self.btn_chr_equal.setChecked(sizing == "Equal Size")
        self.btn_chr_432.setChecked(sizing == "432px")
        self.btn_chr_590.setChecked(sizing == "590px")
        self.save_to_disk()
        self.update_dimensions_display()

    def set_popup_corner(self, corner):
        self.corner_settings["corner"] = corner
        for name, btn in self.corner_btns.items():
            btn.setChecked(name == corner)
        self.save_to_disk()
        self.update_dimensions_display()

    def on_periodic_refresh(self):
        self.update_detection_status()
        self.update_dimensions_display()

    def update_detection_status(self):
        detected_app, detected_hwnd, detected_title, ar, prof_name = detector.detect_active_media(self.media_profiles)
        open_wins = get_open_windows()
        is_vsc_open = any("visual studio code" in t.lower() for t, _ in open_wins)
        is_chrome_open = any("google chrome" in t.lower() and not ("picture in picture" in t.lower() or "pip" in t.lower()) for t, h in open_wins if not detected_hwnd or h != detected_hwnd)

        if detected_app:
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("color: #38bdf8; font-size: 14px;")

            if (is_vsc_open and not is_chrome_open) or (is_chrome_open and not is_vsc_open):
                active_app = "VS Code" if is_vsc_open else "Chrome"
                corner_name = self.corner_settings.get("corner", "Bottom-Right")
                self.status_headline.setText(f"Fullscreen {active_app} + {detected_app} Popup ({ar})")
                self.status_detail.setText(f"Media is floating at {corner_name} with {ar} ratio over fullscreen {active_app}.")
            else:
                self.status_headline.setText(f"3-Window Setup: {detected_app} Active ({ar})")
                self.status_detail.setText(f"Matched to {prof_name}. Dynamic 3-window layout applied.")
        else:
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("color: #30d158; font-size: 14px;")
            self.status_headline.setText("No Media Active — 50 / 50 Split")
            self.status_detail.setText("Chrome and VS Code divide your workspace evenly.")

    def render_profiles_list(self):
        # Clear existing rows
        while self.profiles_list_layout.count():
            item = self.profiles_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        keys = list(self.media_profiles.keys())
        for idx, prof_name in enumerate(keys):
            prof_data = self.media_profiles[prof_name]
            can_up = (idx > 0)
            can_down = (idx < len(keys) - 1)

            row = AspectRatioRow(
                prof_name=prof_name,
                prof_data=prof_data,
                on_delete=self.delete_aspect_ratio,
                on_move=self.reorder_aspect_ratio,
                on_drop_app=self.move_app_between_profiles,
                on_remove_app=self.remove_app_from_profile,
                can_move_up=can_up,
                can_move_down=can_down,
                parent=self
            )
            self.profiles_list_layout.addWidget(row)

    def add_aspect_ratio_dialog(self):
        dlg = AddAspectRatioDialog(self)
        if dlg.exec():
            name, ratio, apps = dlg.get_result()
            if name in self.media_profiles:
                QMessageBox.warning(self, "Profile Exists", f"A category named '{name}' already exists.")
                return

            self.media_profiles[name] = {
                "aspect_ratio": ratio,
                "apps": apps
            }
            self.save_to_disk()
            self.render_profiles_list()
            self.update_dimensions_display()
            self.update_detection_status()

    def delete_aspect_ratio(self, prof_name):
        reply = QMessageBox.question(
            self,
            "Delete Aspect Ratio",
            f"Are you sure you want to delete '{prof_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if prof_name in self.media_profiles:
                del self.media_profiles[prof_name]
                self.save_to_disk()
                self.render_profiles_list()
                self.update_dimensions_display()
                self.update_detection_status()

    def reorder_aspect_ratio(self, prof_name, direction):
        keys = list(self.media_profiles.keys())
        if prof_name not in keys:
            return
        idx = keys.index(prof_name)
        new_idx = idx + direction
        if 0 <= new_idx < len(keys):
            keys[idx], keys[new_idx] = keys[new_idx], keys[idx]
            new_profiles = {k: self.media_profiles[k] for k in keys}
            self.media_profiles = new_profiles
            self.save_to_disk()
            self.render_profiles_list()

    def move_app_between_profiles(self, src_profile, target_profile, app_name):
        src_data = self.media_profiles.get(src_profile)
        if isinstance(src_data, dict) and app_name in src_data.get("apps", []):
            src_data["apps"].remove(app_name)

        tgt_data = self.media_profiles.get(target_profile)
        if isinstance(tgt_data, dict):
            if app_name not in tgt_data.get("apps", []):
                tgt_data["apps"].append(app_name)
        else:
            self.media_profiles[target_profile] = {
                "aspect_ratio": str(tgt_data),
                "apps": [app_name]
            }

        self.save_to_disk()
        self.render_profiles_list()
        self.update_dimensions_display()
        self.update_detection_status()

    def remove_app_from_profile(self, prof_name, app_name):
        prof = self.media_profiles.get(prof_name)
        if isinstance(prof, dict) and app_name in prof.get("apps", []):
            prof["apps"].remove(app_name)
            self.save_to_disk()
            self.render_profiles_list()
            self.update_dimensions_display()

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.keybindings = dlg.get_keybindings()
            snap_key = self.keybindings.get("snap_modifier", "Ctrl")
            self.tip_label.setText(f"Hold {snap_key} while dragging any window to snap.")
            self.save_to_disk()

    def load_data(self):
        config = load_config(CONFIG_PATH)
        if config:
            self.active_mode = config.get("mode", "3_window")
            if "keybindings" in config and isinstance(config["keybindings"], dict):
                self.keybindings.update(config["keybindings"])
            if "layout_settings" in config:
                self.layout_settings.update(config["layout_settings"])
                if "media_profiles" in config["layout_settings"]:
                    self.media_profiles = config["layout_settings"]["media_profiles"]
                if "chrome_sizes" in config["layout_settings"]:
                    self.chrome_sizes.update(config["layout_settings"]["chrome_sizes"])
            if "corner_settings" in config:
                self.corner_settings.update(config["corner_settings"])

        vsc_side = self.layout_settings.get("vscode_side", "Right")
        self.btn_side_left.setChecked(vsc_side == "Left")
        self.btn_side_right.setChecked(vsc_side == "Right")

        chr_sz = self.layout_settings.get("chrome_sizing", "432px")
        self.btn_chr_equal.setChecked(chr_sz == "Equal Size")
        self.btn_chr_432.setChecked(chr_sz == "432px")
        self.btn_chr_590.setChecked(chr_sz == "590px")

        crn_pos = self.corner_settings.get("corner", "Bottom-Right")
        for name, btn in self.corner_btns.items():
            btn.setChecked(name == crn_pos)

        snap_key = self.keybindings.get("snap_modifier", "Ctrl")
        self.tip_label.setText(f"Hold {snap_key} while dragging any window to snap.")

        self.render_profiles_list()
        self.update_detection_status()
        self.update_dimensions_display()

    def _get_current_zones_with_rects(self):
        screen = self.screen().geometry()
        screen_w = screen.width()
        screen_h = screen.height()

        config_data = {
            "layout_settings": self.layout_settings,
            "chrome_sizes": self.chrome_sizes,
            "media_profiles": self.media_profiles,
            "corner_settings": self.corner_settings,
            "app_titles": self.app_titles_3win
        }
        open_wins = get_open_windows()
        return calculate_smart_layout(config_data, screen_w, screen_h, open_windows=open_wins)

    def update_dimensions_display(self):
        zones_data = self._get_current_zones_with_rects()
        screen_geo = self.screen().geometry()
        self.live_preview.update_layout(zones_data, screen_geo.width(), screen_geo.height())
        if hasattr(self, "display_label"):
            self.display_label.setText(f"{screen_geo.width()} × {screen_geo.height()}")

    def save_to_disk(self):
        zones_with_rects = self._get_current_zones_with_rects()
        self.layout_settings["media_profiles"] = self.media_profiles
        self.layout_settings["chrome_sizes"] = self.chrome_sizes
        output_data = {
            "mode": self.active_mode,
            "keybindings": self.keybindings,
            "layout_settings": self.layout_settings,
            "corner_settings": self.corner_settings,
            "zones": zones_with_rects
        }
        save_config(output_data, CONFIG_PATH)

    def apply_layout(self):
        self.save_to_disk()
        try:
            subprocess.Popen([sys.executable, MAIN_SCRIPT], shell=False)
        except Exception as e:
            print(f"Failed to launch: {e}")
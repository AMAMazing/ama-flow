import sys
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QEvent

try:
    from ui.styles import STYLESHEET
    from ui.widgets import NoWheelComboBox
    from ui.overlay import FullscreenPreviewOverlay
    from ui.three_window_panel import ThreeWindowPanel
    from ui.corner_panel import CornerPanel
    from core.config import (
        CONFIG_PATH,
        MAIN_SCRIPT,
        DEFAULT_CHROME_SIZES,
        DEFAULT_MEDIA_PROFILES,
        DEFAULT_LAYOUT_SETTINGS,
        DEFAULT_CORNER_SETTINGS,
        DEFAULT_APP_TITLES_3WIN,
        load_config,
        save_config,
    )
    from core.layout_engine import (
        calculate_rects,
        calculate_fullscreen_corner_rects,
    )
except (ImportError, ValueError):
    from .styles import STYLESHEET
    from .widgets import NoWheelComboBox
    from .overlay import FullscreenPreviewOverlay
    from .three_window_panel import ThreeWindowPanel
    from .corner_panel import CornerPanel
    from ..core.config import (
        CONFIG_PATH,
        MAIN_SCRIPT,
        DEFAULT_CHROME_SIZES,
        DEFAULT_MEDIA_PROFILES,
        DEFAULT_LAYOUT_SETTINGS,
        DEFAULT_CORNER_SETTINGS,
        DEFAULT_APP_TITLES_3WIN,
        load_config,
        save_config,
    )
    from ..core.layout_engine import (
        calculate_rects,
        calculate_fullscreen_corner_rects,
    )

class MainWindow(QMainWindow):
    def __init__(self):
        self.overlay_preview = None
        super().__init__()
        self.setWindowTitle("AppZones")
        self.resize(840, 370)
        self.setStyleSheet(STYLESHEET)

        # Keep GUI visible above the 1:1 fullscreen preview overlay
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.active_mode = "3_window"
        self.chrome_sizes = dict(DEFAULT_CHROME_SIZES)
        self.media_profiles = dict(DEFAULT_MEDIA_PROFILES)
        self.layout_settings = dict(DEFAULT_LAYOUT_SETTINGS)
        self.corner_settings = dict(DEFAULT_CORNER_SETTINGS)
        self.app_titles_3win = dict(DEFAULT_APP_TITLES_3WIN)

        # Initialize the 1:1 fullscreen live preview overlay
        self.overlay_preview = FullscreenPreviewOverlay()

        self.init_ui()
        self.load_data()

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

        # Panel 0: 3-Window Setup Controls
        self.panel_3win = ThreeWindowPanel()
        self.panel_3win.settings_changed.connect(self.on_panel_settings_changed)
        self.controls_stack.addWidget(self.panel_3win)

        # Panel 1: Fullscreen + Corner Media Controls
        self.panel_corner = CornerPanel()
        self.panel_corner.settings_changed.connect(self.on_panel_settings_changed)
        self.controls_stack.addWidget(self.panel_corner)

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

    def load_data(self):
        config = load_config(CONFIG_PATH)
        loaded_zones = []

        if config:
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

        mode_idx = 0 if self.active_mode == "3_window" else 1
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(mode_idx)
        self.mode_combo.blockSignals(False)
        self.controls_stack.setCurrentIndex(mode_idx)

        self.panel_3win.load_settings(
            self.layout_settings,
            self.chrome_sizes,
            self.media_profiles,
            self.app_titles_3win
        )

        self.panel_corner.load_settings(
            self.corner_settings,
            self.media_profiles
        )

        self.update_dimensions_display()

    def on_mode_changed(self, idx):
        self.active_mode = self.mode_combo.currentData()
        self.controls_stack.setCurrentIndex(idx)
        self.save_to_disk()
        self.update_dimensions_display()

    def on_panel_settings_changed(self):
        self.save_to_disk()
        self.update_dimensions_display()

    def _get_current_zones_with_rects(self):
        screen = self.screen().geometry()
        screen_w = screen.width()
        screen_h = screen.height()

        if self.active_mode == "fullscreen_corner":
            return calculate_fullscreen_corner_rects(
                self.corner_settings,
                self.media_profiles,
                screen_w,
                screen_h
            )

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

        return calculate_rects(zones, screen_w, screen_h, chrome_val=chrome_val)

    def update_dimensions_display(self):
        zones_data = self._get_current_zones_with_rects()
        screen_geo = self.screen().geometry()
        if getattr(self, "overlay_preview", None):
            self.overlay_preview.set_zones(zones_data, screen_geo)
        if hasattr(self, "mon_res_label"):
            self.mon_res_label.setText(f"🖥️ Display 1  •  {screen_geo.width()} × {screen_geo.height()}")
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
        save_config(output_data, CONFIG_PATH)

    def apply_layout(self):
        self.save_to_disk()
        try:
            subprocess.Popen([sys.executable, MAIN_SCRIPT], shell=False)
        except Exception as e:
            print(f"Failed to launch: {e}")
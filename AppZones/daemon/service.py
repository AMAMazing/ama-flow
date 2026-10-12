import sys
import signal
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QTimer, QRect
from PyQt6.QtGui import QCursor

try:
    from ..core.config import (
        CONFIG_PATH,
        load_config,
        parse_hotkey,
        parse_modifier_vk,
        format_hotkey_display
    )
    from ..core.win_utils import (
        WINEVENTPROC,
        find_window_by_title,
        position_window,
        get_open_windows,
        get_screen_resolution
    )
    from ..core.layout_engine import (
        calculate_smart_layout,
        calculate_fullscreen_corner_rects
    )
except (ImportError, ValueError):
    from core.config import (
        CONFIG_PATH,
        load_config,
        parse_hotkey,
        parse_modifier_vk,
        format_hotkey_display
    )
    from core.win_utils import (
        WINEVENTPROC,
        find_window_by_title,
        position_window,
        get_open_windows,
        get_screen_resolution
    )
    from core.layout_engine import (
        calculate_smart_layout,
        calculate_fullscreen_corner_rects
    )

from .overlay import OverlayWidget
from .hotkey import HotkeyFilter

def get_active_zones_for_current_state(config=None):
    """
    Determines the current active zones based on open windows and layout settings.
    """
    if config is None:
        config = load_config(CONFIG_PATH)

    mode = config.get("mode", "3_window")
    primary_screen = QApplication.primaryScreen()
    if primary_screen:
        screen_geo = primary_screen.geometry()
        screen_w, screen_h = screen_geo.width(), screen_geo.height()
    else:
        screen_w, screen_h = get_screen_resolution()

    if mode == "fullscreen_corner":
        corner_settings = config.get("corner_settings", {})
        media_profiles = config.get("layout_settings", {}).get("media_profiles", {})
        return calculate_fullscreen_corner_rects(corner_settings, media_profiles, screen_w, screen_h)

    # 3-window mode (with smart detection & 50/50 fallback)
    open_wins = get_open_windows()
    zones = calculate_smart_layout(config, screen_w, screen_h, open_windows=open_wins)
    return zones

def apply_layout_statically():
    """
    Reads config.json, detects media/browser/code windows, and positions all matched open windows immediately.
    """
    config = load_config(CONFIG_PATH)
    zones = get_active_zones_for_current_state(config)

    for zone in zones:
        title = zone.get("window_title", "")
        rect = zone.get("rect")
        if not rect or not title:
            continue

        hwnd = find_window_by_title(title)
        if hwnd:
            print(f"Positioning '{title}' to {rect}", flush=True)
            position_window(hwnd, rect)
        else:
            print(f"Skipping '{title}' (window not currently open)", flush=True)

class AppZonesDaemon(QObject):
    """
    Background service listening for window drag/move operations via WinEventHook
    and displaying the snapping overlay when the configured modifier key is pressed.
    """
    def __init__(self):
        super().__init__()

        self.overlay = OverlayWidget()
        self.is_moving = False
        self.moving_hwnd = None
        self.snap_modifier_vk = 0x11

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)

        # WinEventHook for Drags
        self.hook_proc = WINEVENTPROC(self.win_event_callback)
        self.hook = ctypes.windll.user32.SetWinEventHook(
            0x000A, 0x000B, 0, self.hook_proc, 0, 0, 0
        )

    def refresh_modifier_vk(self):
        try:
            config = load_config(CONFIG_PATH)
            snap_mod = config.get("keybindings", {}).get("snap_modifier", "Ctrl")
            self.snap_modifier_vk = parse_modifier_vk(snap_mod)
        except Exception:
            self.snap_modifier_vk = 0x11

    def win_event_callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if idObject != 0:  # OBJID_WINDOW = 0
            return

        if event == 0x000A:  # EVENT_SYSTEM_MOVESIZESTART
            root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)
            self.is_moving = True
            self.moving_hwnd = root_hwnd
            self.refresh_modifier_vk()
            self.timer.start(16)
        elif event == 0x000B:  # EVENT_SYSTEM_MOVESIZEEND
            self.is_moving = False
            self.timer.stop()
            if self.overlay.isVisible():
                self.overlay.hide()
                if self.overlay.hovered_zone_idx != -1:
                    rect = self.overlay.zones[self.overlay.hovered_zone_idx]["rect"]
                    QTimer.singleShot(50, lambda h=self.moving_hwnd, r=rect: position_window(h, r))
                self.overlay.hovered_zone_idx = -1

    def on_tick(self):
        modifier_pressed = ctypes.windll.user32.GetAsyncKeyState(self.snap_modifier_vk) & 0x8000

        if modifier_pressed:
            if not self.overlay.isVisible():
                self.overlay.load_zones()
                self.overlay.show()

            pos = QCursor.pos()
            hovered = -1
            matching = []
            for i, z in enumerate(self.overlay.zones):
                rect = z.get("rect")
                if not rect:
                    continue
                zr = QRect(int(rect["x"]), int(rect["y"]), int(rect["width"]), int(rect["height"]))
                if zr.contains(pos):
                    area = int(rect["width"]) * int(rect["height"])
                    matching.append((area, -i, i))

            if matching:
                matching.sort()
                hovered = matching[0][2]

            if hovered != self.overlay.hovered_zone_idx:
                self.overlay.hovered_zone_idx = hovered
                self.overlay.update()
        else:
            if self.overlay.isVisible():
                self.overlay.hide()
                self.overlay.hovered_zone_idx = -1

def run_daemon():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "AppZonesDaemonMutex")
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        print("Daemon is already running. Applying layout statically and exiting...", flush=True)
        apply_layout_statically()
        sys.exit(0)

    app = QApplication(sys.argv)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    apply_layout_statically()

    config = load_config(CONFIG_PATH)
    keybindings = config.get("keybindings", {})
    open_gui_str = keybindings.get("open_gui", "Ctrl+Win+Z")
    apply_layout_str = keybindings.get("apply_layout", "Win+Shift+Z")
    snap_mod_str = keybindings.get("snap_modifier", "Ctrl")

    app._hotkey_filter = HotkeyFilter(
        on_open_gui=None,
        on_apply_layout=apply_layout_statically
    )
    app.installNativeEventFilter(app._hotkey_filter)

    # Register Hotkey 1: Open GUI (Ctrl + Win + Z default)
    mod1, vk1 = parse_hotkey(open_gui_str)
    if mod1 is not None and vk1 is not None:
        ctypes.windll.user32.RegisterHotKey(0, 1, mod1, vk1)

    # Register Hotkey 2: Apply Layout (Win + Shift + Z default)
    mod2, vk2 = parse_hotkey(apply_layout_str)
    if mod2 is not None and vk2 is not None:
        ctypes.windll.user32.RegisterHotKey(0, 2, mod2, vk2)

    app._daemon = AppZonesDaemon()

    print("\n-------------------------------------------------------------", flush=True)
    print(" AppZones Daemon is ACTIVE and listening in the background! ", flush=True)
    print("-------------------------------------------------------------", flush=True)
    print(f" 1. Press '{format_hotkey_display(open_gui_str)}' at any time to open the AppZones Editor.", flush=True)
    print(f" 2. Press '{format_hotkey_display(apply_layout_str)}' to instantly apply the current layout.", flush=True)
    print(f" 3. Hold '{snap_mod_str}' while dragging any window to reveal your zones and snap it.", flush=True)
    print("-------------------------------------------------------------\n", flush=True)

    sys.exit(app.exec())
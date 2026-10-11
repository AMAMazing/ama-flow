import sys
import signal
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QTimer, QRect
from PyQt6.QtGui import QCursor

try:
    from ..core.config import CONFIG_PATH, load_config
    from ..core.win_utils import (
        WINEVENTPROC,
        find_window_by_title,
        position_window
    )
except (ImportError, ValueError):
    from core.config import CONFIG_PATH, load_config
    from core.win_utils import (
        WINEVENTPROC,
        find_window_by_title,
        position_window
    )

from .overlay import OverlayWidget
from .hotkey import HotkeyFilter

def apply_layout_statically():
    """
    Reads config.json and positions all matched open windows immediately.
    """
    config = load_config(CONFIG_PATH)

    if "presets" in config and "active_preset" in config:
        active = config["active_preset"]
        preset_data = config["presets"].get(active, [])
        if isinstance(preset_data, dict):
            zones = preset_data.get("zones", [])
        else:
            zones = preset_data
    else:
        zones = config.get("zones", [])

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
    and displaying the snapping overlay when Ctrl is pressed.
    """
    def __init__(self):
        super().__init__()

        self.overlay = OverlayWidget()
        self.is_moving = False
        self.moving_hwnd = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)

        # WinEventHook for Drags
        self.hook_proc = WINEVENTPROC(self.win_event_callback)
        self.hook = ctypes.windll.user32.SetWinEventHook(
            0x000A, 0x000B, 0, self.hook_proc, 0, 0, 0
        )

    def win_event_callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if idObject != 0:  # OBJID_WINDOW = 0
            return

        if event == 0x000A:  # EVENT_SYSTEM_MOVESIZESTART
            # Use GA_ROOT (2) to get the main parent window being dragged
            root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)
            self.is_moving = True
            self.moving_hwnd = root_hwnd
            self.timer.start(16)
        elif event == 0x000B:  # EVENT_SYSTEM_MOVESIZEEND
            self.is_moving = False
            self.timer.stop()
            if self.overlay.isVisible():
                self.overlay.hide()
                if self.overlay.hovered_zone_idx != -1:
                    rect = self.overlay.zones[self.overlay.hovered_zone_idx]["rect"]
                    # Apply 50ms after to ensure Windows finishes its drop event calculations
                    QTimer.singleShot(50, lambda h=self.moving_hwnd, r=rect: position_window(h, r))
                self.overlay.hovered_zone_idx = -1

    def on_tick(self):
        # 0x11 is VK_CONTROL, covers both left and right control keys
        ctrl_pressed = ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000

        if ctrl_pressed:
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
    # Use a named mutex to act as a single-instance daemon
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "AppZonesDaemonMutex")
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        print("Daemon is already running. Applying layout statically and exiting...", flush=True)
        apply_layout_statically()
        sys.exit(0)

    app = QApplication(sys.argv)

    # Restore default C-level SIGINT handler so Ctrl+C gracefully kills it in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Apply once on startup for convenience
    apply_layout_statically()

    # Securely bind the native event filter to the app thread so the hotkey never misses
    app._hotkey_filter = HotkeyFilter()
    app.installNativeEventFilter(app._hotkey_filter)

    # Register Hotkey: Win + Shift + Z (0 means associate with thread message queue)
    ctypes.windll.user32.RegisterHotKey(0, 1, 0x0008 | 0x0004, 0x5A)

    # Start daemon to listen for Win+Shift+Z and Ctrl+Drag
    app._daemon = AppZonesDaemon()

    print("\n-------------------------------------------------------------", flush=True)
    print(" AppZones Daemon is ACTIVE and listening in the background! ", flush=True)
    print("-------------------------------------------------------------", flush=True)
    print(" 1. Press 'Win + Shift + Z' at any time to open the AppZones Editor.", flush=True)
    print(" 2. Hold 'Ctrl' while dragging any window to reveal your zones and snap it.", flush=True)
    print("-------------------------------------------------------------\n", flush=True)

    sys.exit(app.exec())
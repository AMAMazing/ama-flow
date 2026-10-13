import sys
import os
import signal
import ctypes
import subprocess
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtCore import QObject, QTimer, QRect
from PyQt6.QtGui import QCursor, QIcon, QAction

try:
    from ..core.config import (
        CONFIG_PATH,
        APP_DIR,
        GUI_SCRIPT,
        MAIN_SCRIPT,
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
    from ..core.detector import detector
except (ImportError, ValueError):
    from core.config import (
        CONFIG_PATH,
        APP_DIR,
        GUI_SCRIPT,
        MAIN_SCRIPT,
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
    from core.detector import detector

from .overlay import OverlayWidget
from .hotkey import HotkeyFilter

def get_pythonw_executable():
    exec_dir = os.path.dirname(sys.executable)
    pyw = os.path.join(exec_dir, "pythonw.exe")
    if os.path.exists(pyw):
        return pyw
    return sys.executable

def launch_gui():
    existing = find_window_by_title("WindowZones")
    if existing:
        user32 = ctypes.windll.user32
        user32.ShowWindow(existing, 9)
        user32.SetForegroundWindow(existing)
        return

    py_exec = get_pythonw_executable()
    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000
    try:
        subprocess.Popen(
            [py_exec, GUI_SCRIPT],
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            close_fds=True
        )
    except Exception as e:
        print(f"Failed to launch GUI: {e}", flush=True)

def get_startup_shortcut_path():
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "WindowZones.lnk")
    return None

def is_startup_enabled():
    path = get_startup_shortcut_path()
    return path is not None and os.path.exists(path)

def set_startup_enabled(enable: bool):
    path = get_startup_shortcut_path()
    if not path:
        return False
    if enable:
        try:
            py_exec = get_pythonw_executable()
            icon_path = os.path.join(APP_DIR, "windowzones_icon.ico")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(APP_DIR, "appzones_icon.ico")
            powershell_cmd = (
                f'$WshShell = New-Object -ComObject WScript.Shell; '
                f'$Shortcut = $WshShell.CreateShortcut("{path}"); '
                f'$Shortcut.TargetPath = "{py_exec}"; '
                f'$Shortcut.Arguments = \'"{MAIN_SCRIPT}"\'; '
                f'$Shortcut.WorkingDirectory = "{APP_DIR}"; '
                f'$Shortcut.IconLocation = "{icon_path}, 0"; '
                f'$Shortcut.Description = "WindowZones Window Manager Background Service"; '
                f'$Shortcut.Save()'
            )
            CREATE_NO_WINDOW = 0x08000000
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", powershell_cmd],
                creationflags=CREATE_NO_WINDOW,
                check=True
            )
            return True
        except Exception as e:
            print(f"Failed to enable startup: {e}", flush=True)
            return False
    else:
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            print(f"Failed to disable startup: {e}", flush=True)
            return False

def get_active_zones_for_current_state(config=None):
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

    # 3-window mode (smart auto-detect media vs 50/50 split)
    open_wins = get_open_windows()
    zones = calculate_smart_layout(config, screen_w, screen_h, open_windows=open_wins)
    return zones

def apply_layout_statically():
    config = load_config(CONFIG_PATH)
    zones = get_active_zones_for_current_state(config)

    # Check if a media window was detected to get its exact HWND
    media_profiles = config.get("layout_settings", {}).get("media_profiles", {})
    detected_app, detected_hwnd, detected_title, ar, prof = detector.detect_active_media(media_profiles)

    for zone in zones:
        role = zone.get("role", "")
        title = zone.get("window_title", "")
        rect = zone.get("rect")
        if not rect:
            continue

        hwnd = None
        if role == "media" and detected_hwnd:
            hwnd = detected_hwnd
        else:
            hwnd = find_window_by_title(title)

        if hwnd:
            print(f"Positioning '{title}' ({role}) to {rect}", flush=True)
            position_window(hwnd, rect)
        else:
            print(f"Skipping '{title}' (window not currently open)", flush=True)

class WindowZonesDaemon(QObject):
    def __init__(self):
        super().__init__()

        self.overlay = OverlayWidget()
        self.is_moving = False
        self.moving_hwnd = None
        self.snap_modifier_vk = 0x11

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)

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
        if idObject != 0:
            return

        if event == 0x000A:
            root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)
            self.is_moving = True
            self.moving_hwnd = root_hwnd
            self.refresh_modifier_vk()
            self.timer.start(16)
        elif event == 0x000B:
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
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "WindowZonesDaemonMutex")
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:
        print("Daemon is already running. Applying layout statically and exiting...", flush=True)
        apply_layout_statically()
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    apply_layout_statically()

    config = load_config(CONFIG_PATH)
    keybindings = config.get("keybindings", {})
    open_gui_str = keybindings.get("open_gui", "Ctrl+Win+Z")
    apply_layout_str = keybindings.get("apply_layout", "Win+Shift+Z")
    snap_mod_str = keybindings.get("snap_modifier", "Ctrl")

    app._hotkey_filter = HotkeyFilter(
        on_open_gui=launch_gui,
        on_apply_layout=apply_layout_statically
    )
    app.installNativeEventFilter(app._hotkey_filter)

    mod1, vk1 = parse_hotkey(open_gui_str)
    if mod1 is not None and vk1 is not None:
        ctypes.windll.user32.RegisterHotKey(0, 1, mod1, vk1)

    mod2, vk2 = parse_hotkey(apply_layout_str)
    if mod2 is not None and vk2 is not None:
        ctypes.windll.user32.RegisterHotKey(0, 2, mod2, vk2)

    app._daemon = WindowZonesDaemon()

    # System Tray Integration
    icon_path = os.path.join(APP_DIR, "windowzones_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(APP_DIR, "appzones_icon.ico")

    tray_icon = QSystemTrayIcon(app)
    if os.path.exists(icon_path):
        tray_icon.setIcon(QIcon(icon_path))
    else:
        tray_icon.setIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon))

    tray_icon.setToolTip("WindowZones - Window Manager (Running in Background)")

    menu = QMenu()

    action_settings = QAction("Open Settings", menu)
    action_settings.triggered.connect(launch_gui)
    menu.addAction(action_settings)

    action_apply = QAction("Apply Layout", menu)
    action_apply.triggered.connect(apply_layout_statically)
    menu.addAction(action_apply)

    menu.addSeparator()

    action_startup = QAction("Start with Windows", menu)
    action_startup.setCheckable(True)
    action_startup.setChecked(is_startup_enabled())
    def on_startup_toggle(checked):
        set_startup_enabled(checked)
        action_startup.setChecked(is_startup_enabled())
    action_startup.toggled.connect(on_startup_toggle)
    menu.addAction(action_startup)

    menu.addSeparator()

    action_quit = QAction("Exit WindowZones", menu)
    action_quit.triggered.connect(app.quit)
    menu.addAction(action_quit)

    tray_icon.setContextMenu(menu)
    tray_icon.activated.connect(
        lambda reason: launch_gui() if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick
        ) else None
    )
    tray_icon.show()

    # Display balloon notification to confirm active background state
    tray_icon.showMessage(
        "WindowZones Active",
        f"Running silently in background.\nPress {format_hotkey_display(open_gui_str)} for settings or {format_hotkey_display(apply_layout_str)} to apply layout.",
        QSystemTrayIcon.MessageIcon.Information,
        2500
    )

    app._tray_icon = tray_icon

    print("\n-------------------------------------------------------------", flush=True)
    print(" WindowZones Daemon is ACTIVE and listening in the background! ", flush=True)
    print("-------------------------------------------------------------", flush=True)
    print(f" 1. Press '{format_hotkey_display(open_gui_str)}' or click the tray icon to open Settings.", flush=True)
    print(f" 2. Press '{format_hotkey_display(apply_layout_str)}' to instantly apply the current layout.", flush=True)
    print(f" 3. Hold '{snap_mod_str}' while dragging any window to reveal your zones and snap it.", flush=True)
    print("-------------------------------------------------------------\n", flush=True)

    sys.exit(app.exec())
import sys
import os
import signal
import ctypes
import subprocess
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtCore import Qt, QObject, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

try:
    from ..core.config import (
        CONFIG_PATH,
        APP_DIR,
        GUI_SCRIPT,
        MAIN_SCRIPT,
        DEFAULT_KEYBINDINGS,
        load_config,
        parse_hotkey,
        parse_modifier_vk,
        format_hotkey_display
    )
    from ..core.win_utils import (
        WINEVENTPROC,
        enable_dpi_awareness,
        find_window_by_title,
        position_window,
        get_open_windows,
        get_open_vscode_windows,
        is_vscode_window_hwnd,
        get_cursor_pos,
        get_primary_monitor_info,
        get_monitor_info_from_point,
        get_monitor_info_from_hwnd,
        get_screen_resolution,
        get_screen_work_area
    )
    from ..core.layout_engine import (
        calculate_smart_layout,
        calculate_fullscreen_corner_rects
    )
    from ..core.detector import detector
    from ..core.vscode_hub_engine import get_hub_engine
    from ..ui.vscode_hub import VSCodeHubWindow
except (ImportError, ValueError):
    from core.config import (
        CONFIG_PATH,
        APP_DIR,
        GUI_SCRIPT,
        MAIN_SCRIPT,
        DEFAULT_KEYBINDINGS,
        load_config,
        parse_hotkey,
        parse_modifier_vk,
        format_hotkey_display
    )
    from core.win_utils import (
        WINEVENTPROC,
        enable_dpi_awareness,
        find_window_by_title,
        position_window,
        get_open_windows,
        get_open_vscode_windows,
        is_vscode_window_hwnd,
        get_cursor_pos,
        get_primary_monitor_info,
        get_monitor_info_from_point,
        get_monitor_info_from_hwnd,
        get_screen_resolution,
        get_screen_work_area
    )
    from core.layout_engine import (
        calculate_smart_layout,
        calculate_fullscreen_corner_rects
    )
    from core.detector import detector
    from core.vscode_hub_engine import get_hub_engine
    from ui.vscode_hub import VSCodeHubWindow

from .overlay import OverlayWidget
from .hotkey import HotkeyFilter
from .vscode_tabs import VSCodeTabsManager, get_tab_bar_physical_height

# Ensure process DPI awareness is active
enable_dpi_awareness()

DAEMON_IPC_NAME = "WindowZonesDaemonIPC"


def send_daemon_command(command: str) -> bool:
    """
    Sends a lightweight IPC command (e.g. OPEN_HUB, RELOAD_CONFIG, APPLY_LAYOUT)
    to the active background WindowZones daemon if running.
    """
    try:
        sock = QLocalSocket()
        sock.connectToServer(DAEMON_IPC_NAME)
        if not sock.waitForConnected(250):
            return False
        sock.write(command.encode("utf-8"))
        sock.flush()
        sock.waitForBytesWritten(250)
        sock.disconnectFromServer()
        return True
    except Exception:
        return False


def get_pythonw_executable():
    exec_dir = os.path.dirname(sys.executable)
    pyw = os.path.join(exec_dir, "pythonw.exe")
    if os.path.exists(pyw):
        return pyw
    return sys.executable


def launch_gui():
    existing = find_window_by_title("WindowZones", exact=True)
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
            cwd=APP_DIR,
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
                f'$Shortcut.Arguments = \'{MAIN_SCRIPT}\'; '
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


def get_active_monitor_info():
    try:
        fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
        if fg_hwnd:
            return get_monitor_info_from_hwnd(fg_hwnd)
    except Exception:
        pass
    return get_primary_monitor_info()


def get_active_zones_for_current_state(config=None, monitor_info=None):
    if config is None:
        config = load_config(CONFIG_PATH)

    mode = config.get("mode", "3_window")
    if monitor_info is None:
        monitor_info = get_active_monitor_info()

    origin_x, origin_y, screen_w, screen_h = monitor_info["work"]

    if mode == "fullscreen_corner":
        corner_settings = config.get("corner_settings", {})
        media_profiles = config.get("layout_settings", {}).get("media_profiles", {})
        return calculate_fullscreen_corner_rects(
            corner_settings, media_profiles, screen_w, screen_h,
            origin_x=origin_x, origin_y=origin_y
        )

    # 3-window mode (smart auto-detect media vs 50/50 split)
    open_wins = get_open_windows()
    zones = calculate_smart_layout(
        config, screen_w, screen_h, open_windows=open_wins,
        origin_x=origin_x, origin_y=origin_y
    )
    return zones


def _adjust_rect_for_vscode_tabs(rect, monitor_info):
    wx, wy, ww, wh = monitor_info["work"]
    bar_h = get_tab_bar_physical_height(monitor_info.get("scale", 1.0))
    needed_top = wy + bar_h
    if rect["y"] < needed_top:
        delta = needed_top - rect["y"]
        return {
            "x": rect["x"],
            "y": needed_top,
            "width": rect["width"],
            "height": max(240, rect["height"] - delta),
        }
    return dict(rect)


def apply_layout_statically():
    config = load_config(CONFIG_PATH)
    monitor_info = get_active_monitor_info()
    zones = get_active_zones_for_current_state(config, monitor_info=monitor_info)

    # Check whether VS Code tabs will be active so top space is reserved cleanly
    tabs_mode = config.get("layout_settings", {}).get("vscode_tabs_mode", "Auto")
    open_vscode = get_open_vscode_windows()
    tabs_active = (
        (tabs_mode == "Enabled" and len(open_vscode) >= 1)
        or (tabs_mode == "Auto" and len(open_vscode) >= 2)
    )

    # Check if a media window was detected to get its exact HWND
    media_profiles = config.get("layout_settings", {}).get("media_profiles", {})
    detected_app, detected_hwnd, detected_title, ar, prof = detector.detect_active_media(media_profiles)

    used_hwnds = set()
    if detected_hwnd:
        used_hwnds.add(detected_hwnd)

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

            # General fallback to prevent HWND collisions (same window assigned to multiple zones)
            if hwnd in used_hwnds:
                hwnd = None

            if not hwnd:
                for w_title, w_hwnd in get_open_windows():
                    if w_hwnd not in used_hwnds and title.lower() in w_title.lower():
                        hwnd = w_hwnd
                        break

        if hwnd:
            used_hwnds.add(hwnd)
            target_rect = rect
            if tabs_active and is_vscode_window_hwnd(hwnd):
                target_rect = _adjust_rect_for_vscode_tabs(rect, monitor_info)
                # Stack all other non-minimized VS Code windows neatly into the same tabbed zone
                for vwin in open_vscode:
                    vhwnd = vwin["hwnd"]
                    if vhwnd != hwnd and vhwnd not in used_hwnds and not vwin["is_minimized"]:
                        used_hwnds.add(vhwnd)
                        position_window(vhwnd, target_rect, no_activate=True)

            print(f"Positioning '{title}' ({role}) to {target_rect}", flush=True)
            position_window(hwnd, target_rect)
        else:
            print(f"Skipping '{title}' (window not currently open)", flush=True)


class WindowZonesDaemon(QObject):
    def __init__(self):
        super().__init__()

        self.overlay = OverlayWidget()
        self.is_moving = False
        self.moving_hwnd = None
        self.snap_modifier_vk = 0x11
        self.active_monitor_device = None

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
            self.active_monitor_device = None
            self.refresh_modifier_vk()
            self.timer.start(16)
        elif event == 0x000B:
            self.is_moving = False
            self.timer.stop()
            self.active_monitor_device = None
            if self.overlay.isVisible():
                self.overlay.hide()
                if self.overlay.hovered_zone_idx != -1:
                    rect = self.overlay.zones[self.overlay.hovered_zone_idx]["rect"]
                    QTimer.singleShot(50, lambda h=self.moving_hwnd, r=rect: position_window(h, r))
                self.overlay.hovered_zone_idx = -1

    def on_tick(self):
        modifier_pressed = ctypes.windll.user32.GetAsyncKeyState(self.snap_modifier_vk) & 0x8000

        if modifier_pressed:
            cx, cy = get_cursor_pos()
            mon_info = get_monitor_info_from_point(cx, cy)
            mon_dev = mon_info.get("device")

            if not self.overlay.isVisible() or mon_dev != self.active_monitor_device:
                self.active_monitor_device = mon_dev
                self.overlay.hovered_zone_idx = -1
                self.overlay.load_zones(monitor_info=mon_info)
                self.overlay.show()

            hovered = -1
            matching = []
            for i, z in enumerate(self.overlay.zones):
                rect = z.get("rect")
                if not rect:
                    continue
                rx = int(rect["x"])
                ry = int(rect["y"])
                rw = int(rect["width"])
                rh = int(rect["height"])
                if rx <= cx < rx + rw and ry <= cy < ry + rh:
                    area = rw * rh
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
                self.active_monitor_device = None


def run_daemon():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "WindowZonesDaemonMutex")
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:
        print("Daemon is already running. Applying layout statically and exiting...", flush=True)
        apply_layout_statically()
        sys.exit(0)

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    apply_layout_statically()

    # Shared VS Code Hub engine powering both the native Hub window and the VS Code Tab Bar '+' dropdown
    hub_engine = get_hub_engine()
    hub_engine.start_scan()
    hub_window = VSCodeHubWindow(engine=hub_engine)

    def open_vscode_hub():
        hub_window.toggle_hub()

    tabs_manager = VSCodeTabsManager(engine=hub_engine, on_open_hub=hub_window.show_hub)
    daemon_obj = WindowZonesDaemon()

    registered_hotkeys = {}

    def register_all_hotkeys(cfg=None):
        cfg = cfg or load_config(CONFIG_PATH)
        kb = cfg.get("keybindings", {})
        targets = {
            1: kb.get("open_gui", DEFAULT_KEYBINDINGS["open_gui"]),
            2: kb.get("apply_layout", DEFAULT_KEYBINDINGS["apply_layout"]),
            3: kb.get("open_vscode_hub", DEFAULT_KEYBINDINGS["open_vscode_hub"]),
        }
        user32 = ctypes.windll.user32
        for hk_id, hk_str in targets.items():
            if registered_hotkeys.get(hk_id) == hk_str:
                continue
            if hk_id in registered_hotkeys:
                try:
                    user32.UnregisterHotKey(0, hk_id)
                except Exception:
                    pass
            mod, vk = parse_hotkey(hk_str)
            if mod is not None and vk is not None:
                user32.RegisterHotKey(0, hk_id, mod, vk)
                registered_hotkeys[hk_id] = hk_str
        return targets

    def unregister_all_hotkeys():
        user32 = ctypes.windll.user32
        for hk_id in list(registered_hotkeys.keys()):
            try:
                user32.UnregisterHotKey(0, hk_id)
            except Exception:
                pass
        registered_hotkeys.clear()

    config = load_config(CONFIG_PATH)
    keybindings = config.get("keybindings", {})
    open_gui_str = keybindings.get("open_gui", DEFAULT_KEYBINDINGS["open_gui"])
    apply_layout_str = keybindings.get("apply_layout", DEFAULT_KEYBINDINGS["apply_layout"])
    open_hub_str = keybindings.get("open_vscode_hub", DEFAULT_KEYBINDINGS["open_vscode_hub"])
    snap_mod_str = keybindings.get("snap_modifier", DEFAULT_KEYBINDINGS["snap_modifier"])

    app._hotkey_filter = HotkeyFilter(
        on_open_gui=launch_gui,
        on_apply_layout=apply_layout_statically,
        on_open_vscode_hub=open_vscode_hub,
    )
    app.installNativeEventFilter(app._hotkey_filter)
    register_all_hotkeys(config)

    # Hot-reload config.json changes (hotkeys & VS Code tabs mode) without requiring daemon restart
    last_cfg_mtime = [os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else 0.0]

    def reload_runtime_config(force=False):
        try:
            cur_mtime = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else 0.0
            if not force and cur_mtime == last_cfg_mtime[0]:
                return
            last_cfg_mtime[0] = cur_mtime
            fresh_cfg = load_config(CONFIG_PATH)
            register_all_hotkeys(fresh_cfg)
            daemon_obj.refresh_modifier_vk()
            tabs_manager.reload_mode_from_config()
            tabs_manager.refresh_now()
        except Exception:
            pass

    cfg_watch_timer = QTimer(app)
    cfg_watch_timer.timeout.connect(reload_runtime_config)
    cfg_watch_timer.start(1000)

    # Local IPC Server so the Control Panel can invoke Hub / Reload directly on the daemon
    ipc_server = QLocalServer(app)
    QLocalServer.removeServer(DAEMON_IPC_NAME)
    ipc_server.listen(DAEMON_IPC_NAME)

    def handle_ipc_connection():
        client = ipc_server.nextPendingConnection()
        if not client:
            return
        if client.waitForReadyRead(400):
            cmd = client.readAll().data().decode("utf-8", errors="ignore").strip().upper()
            if cmd == "OPEN_HUB":
                hub_window.show_hub()
            elif cmd == "TOGGLE_HUB":
                hub_window.toggle_hub()
            elif cmd == "RELOAD_CONFIG":
                reload_runtime_config(force=True)
            elif cmd == "APPLY_LAYOUT":
                apply_layout_statically()
        client.disconnectFromServer()

    ipc_server.newConnection.connect(handle_ipc_connection)

    app._daemon = daemon_obj
    app._hub_engine = hub_engine
    app._hub_window = hub_window
    app._tabs_manager = tabs_manager
    app._cfg_watch_timer = cfg_watch_timer
    app._ipc_server = ipc_server
    app._mutex = mutex

    app.aboutToQuit.connect(unregister_all_hotkeys)
    app.aboutToQuit.connect(ipc_server.close)

    # System Tray Integration
    icon_path = os.path.join(APP_DIR, "windowzones_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(APP_DIR, "appzones_icon.ico")

    tray_icon = QSystemTrayIcon(app)
    if os.path.exists(icon_path):
        tray_icon.setIcon(QIcon(icon_path))
    else:
        tray_icon.setIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon))

    tray_icon.setToolTip("WindowZones - Window Manager & VS Code Hub (Running in Background)")

    menu = QMenu()

    action_settings = QAction("Open Settings", menu)
    action_settings.triggered.connect(launch_gui)
    menu.addAction(action_settings)

    action_hub = QAction("Open VS Code Hub", menu)
    action_hub.triggered.connect(hub_window.show_hub)
    menu.addAction(action_hub)

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
        (
            f"Running silently in background.\n"
            f"Settings: {format_hotkey_display(open_gui_str)} | "
            f"Layout: {format_hotkey_display(apply_layout_str)} | "
            f"VS Code Hub: {format_hotkey_display(open_hub_str)}"
        ),
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
    print(f" 4. Press '{format_hotkey_display(open_hub_str)}' to open the integrated VS Code Hub.", flush=True)
    print("-------------------------------------------------------------\n", flush=True)

    sys.exit(app.exec())
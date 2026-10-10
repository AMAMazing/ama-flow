import sys
import json
import os
import win32gui
import win32con
import ctypes
from ctypes import wintypes
import subprocess
import signal

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QObject, QAbstractNativeEventFilter
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor

class RECT(ctypes.Structure):
    _fields_ = [('left', wintypes.LONG), 
                ('top', wintypes.LONG), 
                ('right', wintypes.LONG), 
                ('bottom', wintypes.LONG)]

WINEVENTPROC = ctypes.WINFUNCTYPE(
    None, 
    wintypes.HANDLE, 
    wintypes.DWORD, 
    wintypes.HWND, 
    wintypes.LONG, 
    wintypes.LONG, 
    wintypes.DWORD, 
    wintypes.DWORD
)

def get_window_margins(hwnd):
    """
    Returns (pad_left, pad_top, pad_right, pad_bottom) by comparing
    GetWindowRect (which includes invisible resize borders) with 
    DwmGetWindowAttribute (which is the actual visual frame).
    """
    try:
        wr = win32gui.GetWindowRect(hwnd)
        fr = RECT()
        # 9 is DWMWA_EXTENDED_FRAME_BOUNDS
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(fr), ctypes.sizeof(fr)) == 0:
            pad_left = fr.left - wr[0]
            pad_top = fr.top - wr[1]
            pad_right = wr[2] - fr.right
            pad_bottom = wr[3] - fr.bottom
            return pad_left, pad_top, pad_right, pad_bottom
    except Exception:
        pass
    return 0, 0, 0, 0

def load_config(path="config.json"):
    if not os.path.exists(path): return {"zones": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_window_by_title(title_substring):
    if not title_substring: return None
    hwnds = []
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            text = win32gui.GetWindowText(hwnd)
            if text and title_substring.lower() in text.lower():
                hwnds.append(hwnd)
        return True
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None

def position_window(hwnd, rect):
    try:
        placement = win32gui.GetWindowPlacement(hwnd)
        if placement[1] == win32con.SW_SHOWMINIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        elif placement[1] == win32con.SW_SHOWMAXIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_NORMAL)
        
        # Calculate the invisible borders
        pad_left, pad_top, pad_right, pad_bottom = get_window_margins(hwnd)
        
        # Adjust the target rect to counteract the invisible borders
        x = int(rect["x"]) - pad_left
        y = int(rect["y"]) - pad_top
        w = int(rect["width"]) + pad_left + pad_right
        h = int(rect["height"]) + pad_top + pad_bottom
        
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOP,
            x, y, w, h,
            0
        )
    except Exception as e:
        print(f"Failed to position window {hwnd}: {e}", flush=True)

def apply_layout_statically():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    config = load_config(config_path)
    
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

class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.zones = []
        self.hovered_zone_idx = -1

    def load_zones(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        config = load_config(config_path)
        
        if "presets" in config and "active_preset" in config:
            active = config["active_preset"]
            preset_data = config["presets"].get(active, [])
            if isinstance(preset_data, dict):
                self.zones = preset_data.get("zones", [])
            else:
                self.zones = preset_data
        else:
            self.zones = config.get("zones", [])
            
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dim background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # Draw non-hovered zones first, then hovered zone last so its highlight is never covered
        draw_order = [i for i in range(len(self.zones)) if i != self.hovered_zone_idx]
        if 0 <= self.hovered_zone_idx < len(self.zones):
            draw_order.append(self.hovered_zone_idx)

        for i in draw_order:
            z = self.zones[i]
            rect = z.get("rect")
            if not rect: continue
            zr = QRect(int(rect["x"]), int(rect["y"]), int(rect["width"]), int(rect["height"]))
            
            # Draw Zone
            if i == self.hovered_zone_idx:
                painter.setBrush(QColor(0, 120, 212, 140))
                painter.setPen(QPen(QColor(0, 120, 212, 255), 3))
            else:
                painter.setBrush(QColor(255, 255, 255, 30))
                painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
                
            zr.adjust(6, 6, -6, -6)
            painter.drawRoundedRect(zr, 8, 8)
            
            # Draw zone number
            painter.setPen(QColor(255, 255, 255, 255))
            font = painter.font()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(zr, Qt.AlignmentFlag.AlignCenter, str(i + 1))

class HotkeyFilter(QAbstractNativeEventFilter):
    def nativeEventFilter(self, eventType, message):
        try:
            msg_obj = ctypes.wintypes.MSG.from_address(int(message))
            if msg_obj.message == win32con.WM_HOTKEY and msg_obj.wParam == 1:
                gui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui.py")
                # Use DETACHED_PROCESS to fully isolate GUI from daemon terminal so ctrl+c won't kill it
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen([sys.executable, gui_path], creationflags=DETACHED_PROCESS, close_fds=True)
                return True, 0
        except Exception:
            pass
        return False, 0

class AppZonesDaemon(QObject):
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
        if idObject != 0: # OBJID_WINDOW = 0
            return
            
        if event == 0x000A: # EVENT_SYSTEM_MOVESIZESTART
            # Use GA_ROOT to get the main parent window being dragged
            root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)
            self.is_moving = True
            self.moving_hwnd = root_hwnd
            self.timer.start(16)
        elif event == 0x000B: # EVENT_SYSTEM_MOVESIZEEND
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
            # In overlapping layouts (such as fullscreen + corner overlay),
            # pick the smallest area zone containing the cursor.
            # If areas are equal, pick the topmost zone (highest index).
            matching = []
            for i, z in enumerate(self.overlay.zones):
                rect = z.get("rect")
                if not rect: continue
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

def main():
    # Use a named mutex to act as a single-instance daemon
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "AppZonesDaemonMutex")
    last_error = ctypes.windll.kernel32.GetLastError()
    
    if last_error == 183: # ERROR_ALREADY_EXISTS
        print("Daemon is already running. Applying layout statically and exiting...", flush=True)
        apply_layout_statically()
        sys.exit(0)
        
    app = QApplication(sys.argv)
    
    # Restore the default C-level SIGINT handler so Ctrl+C gracefully kills it in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Apply once on startup for convenience
    apply_layout_statically()
    
    # Securely bind the native event filter to the app thread so the hotkey never misses
    app._hotkey_filter = HotkeyFilter()
    app.installNativeEventFilter(app._hotkey_filter)
    
    # Register Hotkey: Win + Shift + Z (0 means associate with thread message queue)
    ctypes.windll.user32.RegisterHotKey(0, 1, 0x0008 | 0x0004, 0x5A)
    
    # Start the daemon to listen for Win+Shift+Z and Ctrl+Drag
    # Keep reference to avoid garbage collection wiping out the Windows Hook
    app._daemon = AppZonesDaemon()
    
    print("\n-------------------------------------------------------------", flush=True)
    print(" AppZones Daemon is ACTIVE and listening in the background! ", flush=True)
    print("-------------------------------------------------------------", flush=True)
    print(" 1. Press 'Win + Shift + Z' at any time to open the AppZones Editor.", flush=True)
    print(" 2. Hold 'Ctrl' while dragging any window to reveal your zones and snap it.", flush=True)
    print("-------------------------------------------------------------\n", flush=True)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
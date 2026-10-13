import os
import math
import ctypes
from ctypes import wintypes
import win32gui
import win32con

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', wintypes.LONG),
        ('top', wintypes.LONG),
        ('right', wintypes.LONG),
        ('bottom', wintypes.LONG)
    ]

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

def get_screen_resolution():
    try:
        user32 = ctypes.windll.user32
        # SM_CXSCREEN = 0, SM_CYSCREEN = 1
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    return 1920, 1080

def get_window_margins(hwnd):
    """
    Returns (pad_left, pad_top, pad_right, pad_bottom) by comparing
    GetWindowRect (which includes invisible resize borders) with
    DwmGetWindowAttribute (actual visual frame).
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

def is_alt_tab_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    title = win32gui.GetWindowText(hwnd).strip()
    if not title:
        return False

    if "windowzones" in title.lower() or "appzones" in title.lower():
        return False

    try:
        current_pid = os.getpid()
        class DWORD(ctypes.c_ulong):
            pass
        pid = DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == current_pid:
            return False
    except Exception:
        pass

    cloaked = ctypes.c_int(0)
    try:
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0:
            if cloaked.value != 0:
                return False
    except Exception:
        pass

    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if (ex_style & win32con.WS_EX_TOOLWINDOW) and not (ex_style & win32con.WS_EX_APPWINDOW):
            return False

        owner = win32gui.GetWindow(hwnd, win32con.GW_OWNER)
        if owner and not (ex_style & win32con.WS_EX_APPWINDOW):
            return False

        rect = win32gui.GetWindowRect(hwnd)
        if (rect[2] - rect[0] <= 0) or (rect[3] - rect[1] <= 0):
            return False
    except Exception:
        return False

    return True

def get_open_windows():
    windows = []
    def callback(hwnd, _):
        if is_alt_tab_window(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            windows.append((title, hwnd))
        return True
    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass
    junk = {"Program Manager", "Settings", "Microsoft Text Input Application", "Windows Input Experience"}
    seen = set()
    cleaned = []
    for title, hwnd in windows:
        if title not in junk and title not in seen:
            seen.add(title)
            cleaned.append((title, hwnd))
    return sorted(cleaned, key=lambda x: x[0].lower())

def get_window_dimensions(hwnd):
    try:
        fr = RECT()
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(fr), ctypes.sizeof(fr)) == 0:
            w = fr.right - fr.left
            h = fr.bottom - fr.top
        else:
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
        return max(0, w), max(0, h)
    except Exception:
        try:
            rect = win32gui.GetWindowRect(hwnd)
            return max(0, rect[2] - rect[0]), max(0, rect[3] - rect[1])
        except Exception:
            return 0, 0

def calculate_window_aspect_ratio(hwnd):
    try:
        w, h = get_window_dimensions(hwnd)
        if w <= 0 or h <= 0:
            return None, 0, 0
        common_ratios = [
            (16, 9), (4, 3), (21, 9), (16, 10), (3, 2),
            (1, 1), (9, 16), (3, 4), (18, 9), (32, 9)
        ]
        target_ratio = w / h
        best_match = None
        best_diff = float("inf")
        for num, den in common_ratios:
            diff = abs((num / den) - target_ratio)
            if diff < best_diff and diff < 0.05:
                best_diff = diff
                best_match = f"{num}:{den}"
        if best_match:
            return best_match, w, h
        divisor = math.gcd(w, h)
        if divisor > 10:
            sim_w = w // divisor
            sim_h = h // divisor
            if sim_w < 100 and sim_h < 100:
                return f"{sim_w}:{sim_h}", w, h
        return f"{round(target_ratio, 2)}:1", w, h
    except Exception:
        return None, 0, 0

def find_window_by_title(title_substring):
    if not title_substring:
        return None
    hwnds = []
    def callback(hwnd, collector):
        if win32gui.IsWindowVisible(hwnd):
            text = win32gui.GetWindowText(hwnd)
            if text and title_substring.lower() in text.lower():
                collector.append(hwnd)
        return True
    try:
        win32gui.EnumWindows(callback, hwnds)
    except Exception:
        pass
    return hwnds[0] if hwnds else None

def position_window(hwnd, rect):
    try:
        placement = win32gui.GetWindowPlacement(hwnd)
        if placement[1] == win32con.SW_SHOWMINIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        elif placement[1] == win32con.SW_SHOWMAXIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_NORMAL)

        pad_left, pad_top, pad_right, pad_bottom = get_window_margins(hwnd)

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
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

class POINT(ctypes.Structure):
    _fields_ = [
        ('x', wintypes.LONG),
        ('y', wintypes.LONG)
    ]

class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', wintypes.DWORD),
        ('szDevice', wintypes.WCHAR * 32)
    ]

MONITORENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    wintypes.HANDLE,
    wintypes.HANDLE,
    ctypes.POINTER(RECT),
    wintypes.LPARAM
)

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

def enable_dpi_awareness():
    """
    Enables Per-Monitor DPI Awareness v2 so Win32 coordinate APIs and Qt coordinate
    systems operate in un-stretched physical pixels on all display scales (100%, 125%, 150%, 200%).
    """
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return True
    except Exception:
        pass

    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return True
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return True
    except Exception:
        pass
    return False

# Automatically invoke upon module import to protect all downstream coordinate queries
enable_dpi_awareness()

def _extract_monitor_info(hmonitor):
    if not hmonitor:
        return None
    try:
        mi = MONITORINFOEXW()
        mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
            ml, mt, mr, mb = mi.rcMonitor.left, mi.rcMonitor.top, mi.rcMonitor.right, mi.rcMonitor.bottom
            wl, wt, wr, wb = mi.rcWork.left, mi.rcWork.top, mi.rcWork.right, mi.rcWork.bottom
            dpi_x = ctypes.c_uint(96)
            dpi_y = ctypes.c_uint(96)
            try:
                # MDT_EFFECTIVE_DPI = 0
                ctypes.windll.shcore.GetDpiForMonitor(hmonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
            except Exception:
                pass
            dpi = dpi_x.value if dpi_x.value > 0 else 96
            return {
                "device": mi.szDevice,
                "monitor": (ml, mt, mr - ml, mb - mt),
                "work": (wl, wt, wr - wl, wb - wt),
                "dpi": dpi,
                "scale": dpi / 96.0,
            }
    except Exception:
        pass
    return None

def get_primary_monitor_info():
    try:
        # MONITOR_DEFAULTTOPRIMARY = 1
        hmon = ctypes.windll.user32.MonitorFromPoint(POINT(0, 0), 1)
        info = _extract_monitor_info(hmon)
        if info:
            return info
    except Exception:
        pass
    sw, sh = get_screen_resolution()
    return {
        "device": "",
        "monitor": (0, 0, sw, sh),
        "work": (0, 0, sw, sh),
        "dpi": 96,
        "scale": 1.0,
    }

def get_monitor_info_from_point(x, y):
    try:
        # MONITOR_DEFAULTTONEAREST = 2
        hmon = ctypes.windll.user32.MonitorFromPoint(POINT(int(x), int(y)), 2)
        info = _extract_monitor_info(hmon)
        if info:
            return info
    except Exception:
        pass
    return get_primary_monitor_info()

def get_monitor_info_from_hwnd(hwnd):
    if hwnd:
        try:
            # MONITOR_DEFAULTTONEAREST = 2
            hmon = ctypes.windll.user32.MonitorFromWindow(int(hwnd), 2)
            info = _extract_monitor_info(hmon)
            if info:
                return info
        except Exception:
            pass
    return get_primary_monitor_info()

def get_monitor_info_by_name(device_name):
    if device_name:
        matched = []
        def _cb(hmon, hdc, lprect, lparam):
            info = _extract_monitor_info(hmon)
            if info and info["device"] == device_name:
                matched.append(info)
                return False
            return True
        try:
            ctypes.windll.user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(_cb), 0)
            if matched:
                return matched[0]
        except Exception:
            pass
    return get_primary_monitor_info()

def get_cursor_pos():
    pt = POINT()
    try:
        if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
            return pt.x, pt.y
    except Exception:
        pass
    return 0, 0

def get_screen_resolution():
    """
    Returns (width, height) of the primary display in physical pixels.
    """
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

def get_screen_work_area():
    """
    Returns (x, y, width, height) of the primary monitor's physical work area,
    which excludes the Windows taskbar and docked appbars regardless of
    where the taskbar is positioned (bottom, top, left, right) or DPI scale.
    """
    try:
        hmon = ctypes.windll.user32.MonitorFromPoint(POINT(0, 0), 1)
        info = _extract_monitor_info(hmon)
        if info:
            wx, wy, ww, wh = info["work"]
            if ww > 0 and wh > 0:
                return wx, wy, ww, wh
    except Exception:
        pass
    try:
        rect = RECT()
        # SPI_GETWORKAREA = 0x0030
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            x = rect.left
            y = rect.top
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w > 0 and h > 0:
                return x, y, w, h
    except Exception:
        pass
    sw, sh = get_screen_resolution()
    return 0, 0, sw, sh

def get_window_margins(hwnd):
    """
    Returns (pad_left, pad_top, pad_right, pad_bottom) in physical pixels by comparing
    GetWindowRect (which includes invisible resize borders) with
    DwmGetWindowAttribute (actual visual frame).
    """
    try:
        wr = win32gui.GetWindowRect(hwnd)
        fr = RECT()
        # 9 is DWMWA_EXTENDED_FRAME_BOUNDS
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(fr), ctypes.sizeof(fr)) == 0:
            if wr[2] > wr[0] and wr[3] > wr[1] and fr.right > fr.left and fr.bottom > fr.top:
                pad_left = fr.left - wr[0]
                pad_top = fr.top - wr[1]
                pad_right = wr[2] - fr.right
                pad_bottom = wr[3] - fr.bottom
                if all(-32 <= p <= 64 for p in (pad_left, pad_top, pad_right, pad_bottom)):
                    return pad_left, pad_top, pad_right, pad_bottom
    except Exception:
        pass
    return 0, 0, 0, 0

def get_window_visual_rect(hwnd):
    """
    Returns {'x': left, 'y': top, 'width': w, 'height': h} of the visual DWM frame
    in physical pixels, or None if unavailable.
    """
    if not hwnd:
        return None
    try:
        fr = RECT()
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(fr), ctypes.sizeof(fr)) == 0:
            w = fr.right - fr.left
            h = fr.bottom - fr.top
            if w > 0 and h > 0:
                return {"x": fr.left, "y": fr.top, "width": w, "height": h}
    except Exception:
        pass
    try:
        wr = win32gui.GetWindowRect(hwnd)
        w = wr[2] - wr[0]
        h = wr[3] - wr[1]
        if w > 0 and h > 0:
            return {"x": wr[0], "y": wr[1], "width": w, "height": h}
    except Exception:
        pass
    return None

def is_window_minimized(hwnd):
    try:
        return bool(ctypes.windll.user32.IsIconic(int(hwnd)))
    except Exception:
        return False

def is_window_maximized(hwnd):
    try:
        return bool(ctypes.windll.user32.IsZoomed(int(hwnd)))
    except Exception:
        return False

def get_foreground_hwnd():
    try:
        return int(ctypes.windll.user32.GetForegroundWindow())
    except Exception:
        return 0

def get_window_pid(hwnd):
    try:
        pid = wintypes.DWORD(0)
        ctypes.windll.user32.GetWindowThreadProcessId(int(hwnd), ctypes.byref(pid))
        return int(pid.value)
    except Exception:
        return 0

def is_alt_tab_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    title = win32gui.GetWindowText(hwnd).strip()
    if not title:
        return False

    if title.lower() in ("windowzones", "appzones"):
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

def is_vscode_window_hwnd(hwnd):
    if not hwnd:
        return False
    try:
        if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
            return False
        if get_window_pid(hwnd) == os.getpid():
            return False
        cls_name = win32gui.GetClassName(hwnd)
        if cls_name != "Chrome_WidgetWin_1":
            return False
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return False
        t_low = title.lower()
        is_code_title = (
            t_low == "visual studio code"
            or t_low.endswith(" - visual studio code")
            or t_low.endswith(" - visual studio code - insiders")
            or t_low == "vscodium"
            or t_low.endswith(" - vscodium")
        )
        if not is_code_title:
            return False

        cloaked = ctypes.c_int(0)
        try:
            if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0:
                if cloaked.value != 0:
                    return False
        except Exception:
            pass

        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if (ex_style & win32con.WS_EX_TOOLWINDOW) and not (ex_style & win32con.WS_EX_APPWINDOW):
            return False
        owner = win32gui.GetWindow(hwnd, win32con.GW_OWNER)
        if owner and not (ex_style & win32con.WS_EX_APPWINDOW):
            return False
        return True
    except Exception:
        return False

def get_open_vscode_windows():
    """
    Enumerates all visible top-level VS Code windows in Z-order (front-most first).
    Returns a list of dicts with hwnd, title, is_minimized, is_maximized, and visual rect.
    """
    results = []
    def callback(hwnd, _):
        if is_vscode_window_hwnd(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            results.append({
                "hwnd": int(hwnd),
                "title": title,
                "is_minimized": is_window_minimized(hwnd),
                "is_maximized": is_window_maximized(hwnd),
                "rect": get_window_visual_rect(hwnd),
            })
        return True
    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass
    return results

def activate_window(hwnd):
    """
    Reliably restores (if minimized) and brings a target window to the foreground.
    """
    if not hwnd:
        return False
    try:
        hwnd = int(hwnd)
        if not win32gui.IsWindow(hwnd):
            return False
        user32 = ctypes.windll.user32
        if user32.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        fg_hwnd = user32.GetForegroundWindow()
        cur_tid = ctypes.windll.kernel32.GetCurrentThreadId()
        fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
        tgt_tid = user32.GetWindowThreadProcessId(hwnd, None)

        attached_fg = False
        attached_tgt = False
        try:
            if fg_tid and fg_tid != cur_tid:
                attached_fg = bool(user32.AttachThreadInput(cur_tid, fg_tid, True))
            if tgt_tid and tgt_tid != cur_tid:
                attached_tgt = bool(user32.AttachThreadInput(cur_tid, tgt_tid, True))
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        finally:
            if attached_tgt:
                user32.AttachThreadInput(cur_tid, tgt_tid, False)
            if attached_fg:
                user32.AttachThreadInput(cur_tid, fg_tid, False)
        return True
    except Exception:
        try:
            win32gui.SetForegroundWindow(int(hwnd))
            return True
        except Exception:
            return False

def close_window(hwnd):
    if not hwnd:
        return False
    try:
        win32gui.PostMessage(int(hwnd), win32con.WM_CLOSE, 0, 0)
        return True
    except Exception:
        return False

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

def find_window_by_title(title_substring, exact=False):
    if not title_substring:
        return None
    target = title_substring.strip().lower()
    hwnds = []
    def callback(hwnd, collector):
        if win32gui.IsWindowVisible(hwnd):
            text = win32gui.GetWindowText(hwnd).strip()
            if text:
                text_lower = text.lower()
                if (exact and text_lower == target) or (not exact and target in text_lower):
                    collector.append(hwnd)
        return True
    try:
        win32gui.EnumWindows(callback, hwnds)
    except Exception:
        pass
    return hwnds[0] if hwnds else None

def position_window(hwnd, rect, no_activate=False):
    try:
        placement = win32gui.GetWindowPlacement(hwnd)
        if placement[1] == win32con.SW_SHOWMINIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        elif placement[1] == win32con.SW_SHOWMAXIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_NORMAL)

        tx = int(round(rect["x"]))
        ty = int(round(rect["y"]))
        tw = int(round(rect["width"]))
        th = int(round(rect["height"]))

        pad_left, pad_top, pad_right, pad_bottom = get_window_margins(hwnd)

        x = tx - pad_left
        y = ty - pad_top
        w = tw + pad_left + pad_right
        h = th + pad_top + pad_bottom

        flags = (win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE) if no_activate else 0
        z_after = 0 if no_activate else win32con.HWND_TOP

        win32gui.SetWindowPos(
            hwnd, z_after,
            x, y, w, h,
            flags
        )

        # Second pass: verify actual DWM visual frame after any WM_DPICHANGED or unmaximize reflow
        fr = RECT()
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(fr), ctypes.sizeof(fr)) == 0:
            actual = (fr.left, fr.top, fr.right - fr.left, fr.bottom - fr.top)
            if actual != (tx, ty, tw, th):
                pl2, pt2, pr2, pb2 = get_window_margins(hwnd)
                nx = tx - pl2
                ny = ty - pt2
                nw = tw + pl2 + pr2
                nh = th + pt2 + pb2
                wr2 = win32gui.GetWindowRect(hwnd)
                if (nx, ny, nw, nh) != (wr2[0], wr2[1], wr2[2] - wr2[0], wr2[3] - wr2[1]):
                    win32gui.SetWindowPos(
                        hwnd, 0,
                        nx, ny, nw, nh,
                        win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
                    )
    except Exception as e:
        print(f"Failed to position window {hwnd}: {e}", flush=True)
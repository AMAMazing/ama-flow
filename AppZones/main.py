import json
import os
import win32gui
import win32con
import ctypes
from ctypes import wintypes

class RECT(ctypes.Structure):
    _fields_ = [('left', wintypes.LONG), 
                ('top', wintypes.LONG), 
                ('right', wintypes.LONG), 
                ('bottom', wintypes.LONG)]

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
        else:
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
        print(f"Failed to position window {hwnd}: {e}")

def main():
    # Ensure process is DPI aware so coordinates perfectly match screen pixels
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
            
    print("Starting AppZones Sleek Auto-Layout Manager...")
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    config = load_config(config_path)
    
    # Support new preset schema while maintaining backwards compatibility
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
            print(f"Positioning '{title}' to {rect}")
            position_window(hwnd, rect)
        else:
            print(f"Could not find running window for: '{title}'")

if __name__ == "__main__":
    main()
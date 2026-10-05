import json
import os
import win32gui
import win32con

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
        
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOP,
            int(rect["x"]), int(rect["y"]), int(rect["width"]), int(rect["height"]),
            0
        )
    except Exception as e:
        print(f"Failed to position window {hwnd}: {e}")

def main():
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
import os
import json

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
MAIN_SCRIPT = os.path.join(APP_DIR, "main.py")
GUI_SCRIPT = os.path.join(APP_DIR, "gui.py")

DEFAULT_CHROME_SIZES = {
    "Equal Size": "equal",
    "432px": "432",
    "590px": "590"
}

DEFAULT_MEDIA_PROFILES = {
    "16:9 (PiP)": {
        "aspect_ratio": "16:9",
        "apps": ["Picture in picture", "YouTube", "Netflix", "Disney+", "Paramount+"]
    },
    "MYAEW (3:2)": {
        "aspect_ratio": "3:2",
        "apps": ["MYAEW"]
    },
    "Square (1:1)": {
        "aspect_ratio": "1:1",
        "apps": ["YouTube Music", "Spotify"]
    },
    "Classic (4:3)": {
        "aspect_ratio": "4:3",
        "apps": []
    },
    "Ultrawide (21:9)": {
        "aspect_ratio": "21:9",
        "apps": []
    }
}

DEFAULT_LAYOUT_SETTINGS = {
    "vscode_side": "Right",
    "chrome_sizing": "432px",
    "active_media_profile": "Auto (Smart Detect)",
    "chrome_sizes": DEFAULT_CHROME_SIZES,
    "media_profiles": DEFAULT_MEDIA_PROFILES
}

DEFAULT_CORNER_SETTINGS = {
    "fullscreen_app": "Visual Studio Code",
    "media_app": "Picture in picture",
    "corner": "Bottom-Right",
    "max_width": 640,
    "max_height": 360,
    "active_media_profile": "16:9 (PiP)"
}

DEFAULT_APP_TITLES_3WIN = {
    "vscode": "Visual Studio Code",
    "chrome": "Google Chrome",
    "media": "Picture in picture"
}

DEFAULT_KEYBINDINGS = {
    "open_gui": "Ctrl+Win+Z",
    "snap_modifier": "Ctrl",
    "apply_layout": "Win+Shift+Z"
}

def parse_hotkey(hotkey_str):
    """
    Parses a hotkey string like 'Ctrl+Win+Z' or 'Win+Shift+Z' into (modifiers, vk_code).
    Returns (mod, vk) or (None, None) if invalid.
    """
    if not hotkey_str or not isinstance(hotkey_str, str):
        return None, None

    parts = [p.strip().lower() for p in hotkey_str.replace("-", "+").split("+") if p.strip()]
    if not parts:
        return None, None

    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008

    mod = 0
    key_token = None

    for part in parts:
        if part in ("win", "windows", "super", "meta"):
            mod |= MOD_WIN
        elif part in ("ctrl", "control"):
            mod |= MOD_CONTROL
        elif part in ("shift",):
            mod |= MOD_SHIFT
        elif part in ("alt", "menu"):
            mod |= MOD_ALT
        else:
            key_token = part

    if not key_token:
        return None, None

    vk = None
    if len(key_token) == 1:
        c = key_token.upper()
        if 'A' <= c <= 'Z' or '0' <= c <= '9':
            vk = ord(c)
        elif c == ' ':
            vk = 0x20
    else:
        if key_token.startswith("f") and key_token[1:].isdigit():
            f_num = int(key_token[1:])
            if 1 <= f_num <= 24:
                vk = 0x70 + (f_num - 1)
        elif key_token in ("space", "spacebar"):
            vk = 0x20
        elif key_token in ("tab",):
            vk = 0x09
        elif key_token in ("enter", "return"):
            vk = 0x0D
        elif key_token in ("esc", "escape"):
            vk = 0x1B
        elif key_token in ("up",):
            vk = 0x26
        elif key_token in ("down",):
            vk = 0x28
        elif key_token in ("left",):
            vk = 0x25
        elif key_token in ("right",):
            vk = 0x27

    if vk is None:
        return None, None

    return mod, vk

def parse_modifier_vk(modifier_str):
    """
    Parses a modifier string into a virtual key code for GetAsyncKeyState.
    Supports Ctrl (0x11), Shift (0x10), Alt (0x12), Win (0x5B).
    Defaults to 0x11 (VK_CONTROL).
    """
    s = (modifier_str or "").strip().lower()
    if "alt" in s:
        return 0x12  # VK_MENU
    if "shift" in s:
        return 0x10  # VK_SHIFT
    if "win" in s:
        return 0x5B  # VK_LWIN
    return 0x11     # VK_CONTROL

def format_hotkey_display(hotkey_str):
    """
    Normalizes a hotkey string to human-readable format, e.g. 'Ctrl + Win + Z'.
    """
    if not hotkey_str:
        return ""
    parts = [p.strip() for p in hotkey_str.replace("-", "+").split("+") if p.strip()]
    normalized = []
    for p in parts:
        pl = p.lower()
        if pl in ("win", "windows"):
            normalized.append("Win")
        elif pl in ("ctrl", "control"):
            normalized.append("Ctrl")
        elif pl == "shift":
            normalized.append("Shift")
        elif pl in ("alt", "menu"):
            normalized.append("Alt")
        else:
            normalized.append(p.upper() if len(p) <= 3 else p.capitalize())
    return " + ".join(normalized)

def load_config(path=None):
    cfg_path = path or CONFIG_PATH
    if not os.path.exists(cfg_path):
        return {
            "mode": "3_window",
            "keybindings": dict(DEFAULT_KEYBINDINGS),
            "layout_settings": dict(DEFAULT_LAYOUT_SETTINGS),
            "corner_settings": dict(DEFAULT_CORNER_SETTINGS),
            "zones": []
        }
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "keybindings" not in data or not isinstance(data["keybindings"], dict):
                data["keybindings"] = dict(DEFAULT_KEYBINDINGS)
            if "layout_settings" not in data or not isinstance(data["layout_settings"], dict):
                data["layout_settings"] = dict(DEFAULT_LAYOUT_SETTINGS)
            if "corner_settings" not in data or not isinstance(data["corner_settings"], dict):
                data["corner_settings"] = dict(DEFAULT_CORNER_SETTINGS)
            return data
    except Exception:
        return {
            "mode": "3_window",
            "keybindings": dict(DEFAULT_KEYBINDINGS),
            "layout_settings": dict(DEFAULT_LAYOUT_SETTINGS),
            "corner_settings": dict(DEFAULT_CORNER_SETTINGS),
            "zones": []
        }

def save_config(data, path=None):
    cfg_path = path or CONFIG_PATH
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
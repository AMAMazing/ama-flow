import os
import json

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
MAIN_SCRIPT = os.path.join(APP_DIR, "main.py")
GUI_SCRIPT = os.path.join(APP_DIR, "gui.py")

DEFAULT_CHROME_SIZES = {
    "Equal Size": "equal",
    "432px": "432"
}

DEFAULT_MEDIA_PROFILES = {
    "16:9 (PiP)": "16:9",
    "4:3 (Classic)": "4:3",
    "21:9 (Ultrawide)": "21:9",
    "1:1 (Square)": "1:1",
    "MYAEW": "16:9"
}

DEFAULT_LAYOUT_SETTINGS = {
    "vscode_side": "Right",
    "chrome_sizing": "Equal Size",
    "active_media_profile": "16:9 (PiP)"
}

DEFAULT_CORNER_SETTINGS = {
    "fullscreen_app": "",
    "media_app": "Netflix",
    "corner": "Bottom-Right",
    "max_width": 720,
    "max_height": 450,
    "active_media_profile": "16:9 (PiP)"
}

DEFAULT_APP_TITLES_3WIN = {
    "vscode": "Visual Studio Code",
    "chrome": "Google Chrome",
    "media": "Netflix"
}

def load_config(path=None):
    cfg_path = path or CONFIG_PATH
    if not os.path.exists(cfg_path):
        return {"zones": []}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"zones": []}

def save_config(data, path=None):
    cfg_path = path or CONFIG_PATH
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
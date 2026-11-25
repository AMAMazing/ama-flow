import sys
import os
import time
import subprocess
import ctypes
from ctypes import wintypes
import win32con
from PyQt6.QtCore import QAbstractNativeEventFilter, QTimer

try:
    from ..core.config import (
        CONFIG_PATH,
        GUI_SCRIPT,
        DEFAULT_KEYBINDINGS,
        load_config,
        parse_hotkey,
    )
except (ImportError, ValueError):
    from core.config import (
        CONFIG_PATH,
        GUI_SCRIPT,
        DEFAULT_KEYBINDINGS,
        load_config,
        parse_hotkey,
    )

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

_user32 = ctypes.windll.user32
_user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    LowLevelKeyboardProc,
    wintypes.HINSTANCE,
    wintypes.DWORD,
]
_user32.SetWindowsHookExW.restype = ctypes.c_void_p
_user32.CallNextHookEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32.CallNextHookEx.restype = ctypes.c_ssize_t
_user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
_user32.UnhookWindowsHookEx.restype = wintypes.BOOL


class HotkeyFilter(QAbstractNativeEventFilter):
    """
    Native Windows event filter listening for global hotkeys:
    - Hotkey 1: Open WindowZones GUI control panel
    - Hotkey 2: Apply current layout immediately
    - Hotkey 3: Open integrated VS Code Hub UI
    Includes a low-level keyboard hook (WH_KEYBOARD_LL) so OS-reserved shortcuts
    like Win+Shift+A work reliably on Windows 11 even when RegisterHotKey is blocked.
    """
    def __init__(self, on_open_gui=None, on_apply_layout=None, on_open_vscode_hub=None):
        super().__init__()
        self.on_open_gui = on_open_gui
        self.on_apply_layout = on_apply_layout
        self.on_open_vscode_hub = on_open_vscode_hub

        self._last_trigger_ts = {1: 0.0, 2: 0.0, 3: 0.0}
        self._cfg_mtime = -1.0
        self._parsed_targets = {}
        self._refresh_parsed_hotkeys()

        self._ll_proc = LowLevelKeyboardProc(self._low_level_kb_proc)
        self._ll_hook = _user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._ll_proc, None, 0)

    def _refresh_parsed_hotkeys(self):
        try:
            mtime = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else 0.0
            if mtime == self._cfg_mtime and self._parsed_targets:
                return
            self._cfg_mtime = mtime
            cfg = load_config(CONFIG_PATH)
            kb = cfg.get("keybindings", {})
            raw = {
                1: kb.get("open_gui", DEFAULT_KEYBINDINGS["open_gui"]),
                2: kb.get("apply_layout", DEFAULT_KEYBINDINGS["apply_layout"]),
                3: kb.get("open_vscode_hub", DEFAULT_KEYBINDINGS["open_vscode_hub"]),
            }
            parsed = {}
            for hk_id, hk_str in raw.items():
                mod, vk = parse_hotkey(hk_str)
                if mod is not None and vk is not None:
                    parsed[hk_id] = (mod, vk)
            self._parsed_targets = parsed
        except Exception:
            pass

    def _dispatch_hotkey(self, hk_id: int):
        now = time.monotonic()
        if now - self._last_trigger_ts.get(hk_id, 0.0) < 0.22:
            return
        self._last_trigger_ts[hk_id] = now

        if hk_id == 1:
            if self.on_open_gui:
                self.on_open_gui()
            else:
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen(
                    [sys.executable, GUI_SCRIPT],
                    creationflags=DETACHED_PROCESS,
                    close_fds=True,
                )
        elif hk_id == 2:
            if self.on_apply_layout:
                self.on_apply_layout()
        elif hk_id == 3:
            if self.on_open_vscode_hub:
                self.on_open_vscode_hub()

    @staticmethod
    def _current_modifiers() -> int:
        ga = _user32.GetAsyncKeyState
        mod = 0
        if (ga(0x11) & 0x8000) or (ga(0xA2) & 0x8000) or (ga(0xA3) & 0x8000):
            mod |= MOD_CONTROL
        if (ga(0x10) & 0x8000) or (ga(0xA0) & 0x8000) or (ga(0xA1) & 0x8000):
            mod |= MOD_SHIFT
        if (ga(0x12) & 0x8000) or (ga(0xA4) & 0x8000) or (ga(0xA5) & 0x8000):
            mod |= MOD_ALT
        if (ga(0x5B) & 0x8000) or (ga(0x5C) & 0x8000):
            mod |= MOD_WIN
        return mod

    def _low_level_kb_proc(self, nCode, wParam, lParam):
        try:
            if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                kb_struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk_code = int(kb_struct.vkCode)
                # Ignore standalone modifier key presses
                if vk_code not in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5):
                    self._refresh_parsed_hotkeys()
                    active_mod = self._current_modifiers()
                    if active_mod:
                        for hk_id, (req_mod, req_vk) in self._parsed_targets.items():
                            if vk_code == req_vk and active_mod == req_mod:
                                QTimer.singleShot(0, lambda hid=hk_id: self._dispatch_hotkey(hid))
                                return 1
        except Exception:
            pass
        return _user32.CallNextHookEx(self._ll_hook, nCode, wParam, lParam)

    def nativeEventFilter(self, eventType, message):
        try:
            msg_obj = ctypes.wintypes.MSG.from_address(int(message))
            if msg_obj.message == win32con.WM_HOTKEY:
                hk_id = int(msg_obj.wParam)
                if hk_id in (1, 2, 3):
                    self._dispatch_hotkey(hk_id)
                    return True, 0
        except Exception:
            pass
        return False, 0
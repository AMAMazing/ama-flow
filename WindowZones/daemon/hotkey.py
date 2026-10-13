import sys
import os
import subprocess
import ctypes
import win32con
from PyQt6.QtCore import QAbstractNativeEventFilter

try:
    from ..core.config import GUI_SCRIPT
except (ImportError, ValueError):
    from core.config import GUI_SCRIPT

class HotkeyFilter(QAbstractNativeEventFilter):
    """
    Native Windows event filter listening for global hotkeys:
    - Hotkey 1: Open WindowZones GUI control panel
    - Hotkey 2: Apply current layout immediately
    """
    def __init__(self, on_open_gui=None, on_apply_layout=None):
        super().__init__()
        self.on_open_gui = on_open_gui
        self.on_apply_layout = on_apply_layout

    def nativeEventFilter(self, eventType, message):
        try:
            msg_obj = ctypes.wintypes.MSG.from_address(int(message))
            if msg_obj.message == win32con.WM_HOTKEY:
                if msg_obj.wParam == 1:
                    if self.on_open_gui:
                        self.on_open_gui()
                    else:
                        DETACHED_PROCESS = 0x00000008
                        subprocess.Popen(
                            [sys.executable, GUI_SCRIPT],
                            creationflags=DETACHED_PROCESS,
                            close_fds=True
                        )
                    return True, 0
                elif msg_obj.wParam == 2:
                    if self.on_apply_layout:
                        self.on_apply_layout()
                    return True, 0
        except Exception:
            pass
        return False, 0
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
    Native Windows event filter listening for the global hotkey (Win+Shift+Z)
    and launching the AppZones GUI control panel.
    """
    def nativeEventFilter(self, eventType, message):
        try:
            msg_obj = ctypes.wintypes.MSG.from_address(int(message))
            if msg_obj.message == win32con.WM_HOTKEY and msg_obj.wParam == 1:
                # Use DETACHED_PROCESS to fully isolate GUI from daemon terminal so ctrl+c won't kill it
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen(
                    [sys.executable, GUI_SCRIPT],
                    creationflags=DETACHED_PROCESS,
                    close_fds=True
                )
                return True, 0
        except Exception:
            pass
        return False, 0
import sys
import ctypes
from ctypes import wintypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QAbstractNativeEventFilter

app = QApplication(sys.argv)

class Filter(QAbstractNativeEventFilter):
    def nativeEventFilter(self, eventType, message):
        print("nativeEventFilter called! type(message):", type(message), "value:", message, flush=True)
        try:
            addr = int(message)
            msg = wintypes.MSG.from_address(addr)
            print("Successfully extracted MSG:", msg.message, flush=True)
        except Exception as e:
            print("Extraction failed:", e, flush=True)
        return False, 0

f = Filter()
app.installNativeEventFilter(f)

# Post a message to trigger nativeEventFilter
import win32gui, win32con
w = QApplication.allWidgets()
# Create a dummy widget so there's a window message
from PyQt6.QtWidgets import QWidget
dummy = QWidget()
dummy.show()
app.processEvents()
print("Test completed.")
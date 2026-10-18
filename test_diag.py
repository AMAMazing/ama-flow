import sys
import os

print("Testing comtypes import...", flush=True)
try:
    import comtypes
    import comtypes.client
    comtypes.CoInitialize()
    from comtypes.gen import UIAutomationClient
    print("UIAutomationClient imported successfully!", flush=True)
except Exception as e:
    print(f"Import failed: {type(e).__name__}: {e}", flush=True)

import win32gui

print("\n--- All Visible Top-Level Windows ---", flush=True)
def enum_all(hwnd, _):
    if win32gui.IsWindowVisible(hwnd):
        t = win32gui.GetWindowText(hwnd).strip()
        c = win32gui.GetClassName(hwnd)
        if t:
            print(f"HWND: {hwnd:8x} | Class: {c:30} | Title: {t[:60]}", flush=True)
    return True

win32gui.EnumWindows(enum_all, None)
print("\nDone.", flush=True)
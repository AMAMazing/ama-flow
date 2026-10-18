import os
import sys
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

def test():
    print("Testing patched comtypes initialization...", flush=True)
    try:
        import comtypes
        import comtypes._tlib_version_checker
        # Disable the rigid mtime check so Windows OS updates don't break the wrapper
        comtypes._tlib_version_checker._check_version = lambda actual, tlib_cached_mtime=None: None
        
        import comtypes.client
        comtypes.CoInitialize()
        
        try:
            from comtypes.gen import UIAutomationClient
        except Exception:
            # If not yet generated or corrupted, generate from typelib
            comtypes.client.GetModule("UIAutomationCore.dll")
            from comtypes.gen import UIAutomationClient

        uia = comtypes.client.CreateObject(
            UIAutomationClient.CUIAutomation,
            interface=UIAutomationClient.IUIAutomation
        )
        print("CUIAutomation initialized successfully!", flush=True)

        cond_toolbar = uia.CreatePropertyCondition(30012, "WebAppFrameToolbarView")
        cond_menu_btn = uia.CreatePropertyCondition(30012, "WebAppMenuButton")
        TreeScope_Descendants = 4

        def enum_cb(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            if cls_buff.value != "Chrome_WidgetWin_1":
                return True
            title_buff = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, title_buff, 512)
            title = title_buff.value.strip()
            print(f"Window: HWND={hex(hwnd)} Title='{title}'", flush=True)

            try:
                elem = uia.ElementFromHandle(hwnd)
                if elem:
                    tb = elem.FindFirst(TreeScope_Descendants, cond_toolbar)
                    print(f"  WebAppFrameToolbarView found: {tb is not None}", flush=True)
                    if tb:
                        mb = tb.FindFirst(TreeScope_Descendants, cond_menu_btn)
                        print(f"  WebAppMenuButton found: {mb is not None}", flush=True)
                        if mb:
                            print(f"  Button Name: '{mb.CurrentName}'", flush=True)
            except Exception as ex:
                print(f"  UIA query error: {ex}", flush=True)

            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    except Exception as e:
        print(f"Fatal error: {type(e).__name__}: {e}", flush=True)

if __name__ == "__main__":
    test()
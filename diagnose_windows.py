import ctypes
from ctypes import wintypes
import sys

user32 = ctypes.windll.user32

def inspect_windows():
    print("=== Scanning Chrome_WidgetWin_1 Windows ===")
    import comtypes
    import comtypes.client
    comtypes.CoInitialize()
    from comtypes.gen import UIAutomationClient

    uia = comtypes.client.CreateObject(
        UIAutomationClient.CUIAutomation,
        interface=UIAutomationClient.IUIAutomation
    )

    TreeScope_Children = 2
    TreeScope_Descendants = 4

    def enum_cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls_name = cls_buff.value

        if cls_name != "Chrome_WidgetWin_1":
            return True

        title_buff = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title_buff, 512)
        title = title_buff.value.strip()

        ex_style = user32.GetWindowLongW(hwnd, -20)
        is_topmost = bool(ex_style & 0x00000008)

        print(f"\n--- HWND: {hwnd} (hex: {hex(hwnd)}) | Title: '{title}' | Topmost: {is_topmost} ---")

        # Inspect UI Automation element
        try:
            elem = uia.ElementFromHandle(hwnd)
            if not elem:
                print("  UIAutomation ElementFromHandle returned None")
                return True

            print(f"  Root Name: '{elem.CurrentName}' | Class: '{elem.CurrentClassName}' | AutomationId: '{elem.CurrentAutomationId}'")

            # Check toolbar condition
            cond_toolbar = uia.CreatePropertyCondition(30012, "WebAppFrameToolbarView")
            toolbar = elem.FindFirst(TreeScope_Descendants, cond_toolbar)
            print(f"  WebAppFrameToolbarView found: {toolbar is not None}")

            # Check menu button condition
            cond_menu_btn = uia.CreatePropertyCondition(30012, "WebAppMenuButton")
            menu_btn = elem.FindFirst(TreeScope_Descendants, cond_menu_btn)
            print(f"  WebAppMenuButton found: {menu_btn is not None}")
            if menu_btn:
                print(f"    menu_btn Name: '{menu_btn.CurrentName}' | AutomationId: '{menu_btn.CurrentAutomationId}'")

            # Let's inspect all top-level children or descendants to see what classes / automation IDs exist now
            true_cond = uia.CreateTrueCondition()
            children = elem.FindAll(TreeScope_Children, true_cond)
            if children:
                count = children.Length
                print(f"  Direct children count: {count}")
                for i in range(min(count, 10)):
                    child = children.GetElement(i)
                    print(f"    Child {i}: Name='{child.CurrentName}' | Class='{child.CurrentClassName}' | AutoId='{child.CurrentAutomationId}'")

            # Search for any element whose class name contains "Web" or "App" or "Toolbar"
            descendants = elem.FindAll(TreeScope_Descendants, true_cond)
            if descendants:
                d_count = descendants.Length
                print(f"  Total descendants count: {d_count}")
                for i in range(d_count):
                    d = descendants.GetElement(i)
                    c_name = d.CurrentClassName or ""
                    a_id = d.CurrentAutomationId or ""
                    n = d.CurrentName or ""
                    if any(k in c_name.lower() or k in a_id.lower() or "control" in n.lower() for k in ["toolbar", "webapp", "menu", "frame", "custom"]):
                        print(f"    Interesting Descendant: Class='{c_name}' | AutoId='{a_id}' | Name='{n}'")
        except Exception as e:
            print(f"  Error inspecting UIA: {e}")

        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

if __name__ == "__main__":
    inspect_windows()
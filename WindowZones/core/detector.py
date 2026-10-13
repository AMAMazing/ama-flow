import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

DEFAULT_APP_PROFILES = {
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

class MediaDetector:
    """
    Robust detector for Chrome Picture-in-Picture and standalone PWA windows.
    Utilizes Windows UIAutomation COM interfaces to differentiate standalone PWAs
    from standard Chrome browsing tabs.
    """
    def __init__(self):
        self._uia = None
        self._cond_toolbar = None
        self._cond_menu_btn = None
        self._initialized = False

    def _init_com(self):
        if not self._initialized:
            try:
                import comtypes
                import comtypes.client
                comtypes.CoInitialize()
                from comtypes.gen import UIAutomationClient
                self._uia = comtypes.client.CreateObject(
                    UIAutomationClient.CUIAutomation,
                    interface=UIAutomationClient.IUIAutomation
                )
                self._cond_toolbar = self._uia.CreatePropertyCondition(30012, "WebAppFrameToolbarView")
                self._cond_menu_btn = self._uia.CreatePropertyCondition(30012, "WebAppMenuButton")
                self._initialized = True
            except Exception as e:
                self._initialized = False

    def get_open_chrome_and_pwa_windows(self):
        """
        Enumerates all visible Chrome_WidgetWin_1 windows and categorizes them.
        Returns a list of dicts:
          [{'hwnd': hwnd, 'title': title, 'is_pip': bool, 'is_pwa': bool, 'app_name': str, 'topmost': bool}]
        """
        self._init_com()
        found = []
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

            if not title or "Visual Studio Code" in title or "WindowZones" in title or "AppZones" in title:
                return True

            ex_style = user32.GetWindowLongW(hwnd, -20)
            is_topmost = bool(ex_style & 0x00000008)
            lower_title = title.lower()

            # 1. Check for Picture-in-Picture
            if "picture in picture" in lower_title or "picture-in-picture" in lower_title or lower_title == "pip":
                found.append({
                    "hwnd": hwnd,
                    "title": title,
                    "is_pip": True,
                    "is_pwa": False,
                    "app_name": "Picture in picture",
                    "topmost": is_topmost
                })
                return True

            # 2. Check for PWA via UI Automation
            if self._uia and self._cond_toolbar:
                try:
                    elem = self._uia.ElementFromHandle(hwnd)
                    if elem:
                        toolbar = elem.FindFirst(TreeScope_Descendants, self._cond_toolbar)
                        if toolbar:
                            btn = toolbar.FindFirst(TreeScope_Descendants, self._cond_menu_btn)
                            app_name = ""
                            if btn:
                                raw_name = btn.CurrentName or ""
                                app_name = raw_name.replace("Customize and control ", "").strip()
                            if not app_name:
                                app_name = title

                            found.append({
                                "hwnd": hwnd,
                                "title": title,
                                "is_pip": False,
                                "is_pwa": True,
                                "app_name": app_name,
                                "topmost": is_topmost
                            })
                            return True
                except Exception:
                    pass

            # Standard Chrome window (not a PWA or PiP)
            found.append({
                "hwnd": hwnd,
                "title": title,
                "is_pip": False,
                "is_pwa": False,
                "app_name": "Google Chrome",
                "topmost": is_topmost
            })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return found

    def detect_active_media(self, media_profiles=None):
        """
        Detects if an active media window (PWA or PiP) is open and matches it to a profile.
        Returns:
            (detected_app_name, detected_hwnd, detected_title, aspect_ratio_str, profile_name)
            or (None, None, None, None, None) if no media window is open.
        """
        profiles = media_profiles or DEFAULT_APP_PROFILES
        windows = self.get_open_chrome_and_pwa_windows()

        # Check for media windows (PiP or PWA)
        media_candidates = [w for w in windows if w["is_pip"] or w["is_pwa"]]
        if not media_candidates:
            return None, None, None, None, None

        # Give priority to PiP first, then topmost, then first PWA
        media_candidates.sort(key=lambda w: (not w["is_pip"], not w["topmost"]))
        chosen = media_candidates[0]
        app_name = chosen["app_name"]

        # Match app_name to a profile
        matched_profile_name = None
        matched_aspect_ratio = "16:9"

        app_name_lower = app_name.lower()

        for prof_name, prof_data in profiles.items():
            if isinstance(prof_data, dict):
                ar = prof_data.get("aspect_ratio", "16:9")
                apps = prof_data.get("apps", [])
                for a in apps:
                    if a.lower() == app_name_lower or a.lower() in app_name_lower or app_name_lower in a.lower():
                        matched_profile_name = prof_name
                        matched_aspect_ratio = ar
                        break
            elif isinstance(prof_data, str):
                # Legacy simple string format e.g. "16:9"
                if prof_name.lower() in app_name_lower or app_name_lower in prof_name.lower():
                    matched_profile_name = prof_name
                    matched_aspect_ratio = prof_data
                    break
            if matched_profile_name:
                break

        # If not matched to any specific configured list, infer common defaults
        if not matched_profile_name:
            if chosen["is_pip"]:
                matched_profile_name = "16:9 (PiP)"
                matched_aspect_ratio = "16:9"
            elif "aew" in app_name_lower:
                matched_profile_name = "MYAEW (3:2)"
                matched_aspect_ratio = "3:2"
            elif "music" in app_name_lower or "spotify" in app_name_lower:
                matched_profile_name = "Square (1:1)"
                matched_aspect_ratio = "1:1"
            else:
                matched_profile_name = f"{app_name} (Auto)"
                matched_aspect_ratio = "16:9"

        return app_name, chosen["hwnd"], chosen["title"], matched_aspect_ratio, matched_profile_name

# Singleton instance
detector = MediaDetector()
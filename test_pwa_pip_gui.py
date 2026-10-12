import sys
import time
import ctypes
from ctypes import wintypes
import threading
import tkinter as tk
from tkinter import ttk

# Windows API bindings
user32 = ctypes.windll.user32

# Known canonical names mapping
CANONICAL_PWAS = {
    "netflix": "Netflix",
    "youtube music": "YouTube Music",
    "youtube": "YouTube",
    "myaew": "MYAEW",
    "disney+": "Disney+",
    "disney plus": "Disney+",
    "paramount+": "Paramount+",
    "paramount plus": "Paramount+",
    "learn thai 100": "Learn Thai 100",
    "my daily to do": "My Daily To Do",
}

class PwaPipScanner:
    def __init__(self):
        self._initialized = False
        self._uia = None
        self._cond_toolbar = None
        self._cond_menu_btn = None

    def _init_com(self):
        if not self._initialized:
            import comtypes
            import comtypes.client
            comtypes.CoInitialize()
            from comtypes.gen import UIAutomationClient
            
            self._uia = comtypes.client.CreateObject(
                UIAutomationClient.CUIAutomation,
                interface=UIAutomationClient.IUIAutomation
            )
            # Property IDs: 30012 = ClassNamePropertyId
            self._cond_toolbar = self._uia.CreatePropertyCondition(30012, "WebAppFrameToolbarView")
            self._cond_menu_btn = self._uia.CreatePropertyCondition(30012, "WebAppMenuButton")
            self._initialized = True

    def scan(self):
        self._init_com()
        results = []
        TreeScope_Descendants = 4

        def enum_window_callback(hwnd, lparam):
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

            # Ignore Visual Studio Code and our own GUI
            if "Visual Studio Code" in title or "PWA & PiP Detector" in title:
                return True

            ex_style = user32.GetWindowLongW(hwnd, -20)
            is_topmost = bool(ex_style & 0x00000008)
            lower_title = title.lower()

            # 1. Detection of Chrome Picture-in-Picture
            if (
                "picture in picture" in lower_title
                or "picture-in-picture" in lower_title
                or lower_title == "pip"
            ):
                results.append({
                    "category": "PiP",
                    "display_name": "Chrome Picture-in-Picture",
                    "hwnd": hwnd,
                    "window_title": title,
                    "topmost": is_topmost,
                })
                return True

            # 2. Detection of Installed PWA Standalone Windows
            # Standard Chrome browser windows contain regular toolbars, tabs, and omnibox.
            # Installed PWA windows have a WebAppFrameToolbarView and WebAppMenuButton.
            try:
                elem = self._uia.ElementFromHandle(hwnd)
                if not elem:
                    return True

                toolbar = elem.FindFirst(TreeScope_Descendants, self._cond_toolbar)
                if toolbar:
                    btn = toolbar.FindFirst(TreeScope_Descendants, self._cond_menu_btn)
                    raw_app_name = ""
                    if btn:
                        # WebAppMenuButton name is always formatted as: "Customize and control <AppName>"
                        raw_app_name = btn.CurrentName.replace("Customize and control ", "").strip()

                    # Fallback to window title or root element name if needed
                    if not raw_app_name:
                        raw_app_name = elem.CurrentName.strip()

                    # Resolve canonical name
                    display_name = raw_app_name
                    matched_key = raw_app_name.lower()
                    for key, canonical in CANONICAL_PWAS.items():
                        if key == matched_key or key in matched_key:
                            display_name = canonical
                            break

                    results.append({
                        "category": "PWA",
                        "display_name": display_name,
                        "hwnd": hwnd,
                        "window_title": title,
                        "topmost": is_topmost,
                    })
            except Exception:
                pass

            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_window_callback), 0)
        return results


class DetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PWA & PiP Detector")
        self.root.geometry("460x520")
        self.root.minsize(400, 360)
        
        # Configure Always On Top
        self.root.attributes("-topmost", True)
        
        # Dark theme styling
        self.bg_color = "#121214"
        self.card_bg = "#1f1f23"
        self.card_border = "#2e2e34"
        self.text_primary = "#f4f4f6"
        self.text_secondary = "#9e9ea7"
        self.accent_pip = "#38bdf8"    # Sky blue
        self.accent_pwa = "#4ade80"    # Emerald green
        self.accent_none = "#71717a"   # Zinc gray

        self.root.configure(bg=self.bg_color)
        
        self.scanner = PwaPipScanner()
        self.is_scanning = False
        self.detected_items = []

        self._build_ui()
        self._start_scan_loop()

    def _build_ui(self):
        # Header frame
        header_frame = tk.Frame(self.root, bg=self.bg_color)
        header_frame.pack(fill="x", padx=18, pady=(16, 8))

        title_label = tk.Label(
            header_frame,
            text="PWA & PiP Detector",
            font=("Segoe UI", 15, "bold"),
            fg=self.text_primary,
            bg=self.bg_color
        )
        title_label.pack(side="left")

        # Topmost badge
        topmost_badge = tk.Label(
            header_frame,
            text="ALWAYS ON TOP",
            font=("Segoe UI", 8, "bold"),
            fg="#60a5fa",
            bg="#1e293b",
            padx=7,
            pady=3
        )
        topmost_badge.pack(side="right")

        # Subtitle / description
        sub_label = tk.Label(
            self.root,
            text="Live tracking of Chrome Picture-in-Picture & installed web apps",
            font=("Segoe UI", 9),
            fg=self.text_secondary,
            bg=self.bg_color
        )
        sub_label.pack(anchor="w", padx=18, pady=(0, 10))

        # Status summary bar
        self.summary_card = tk.Frame(self.root, bg=self.card_bg, highlightbackground=self.card_border, highlightthickness=1)
        self.summary_card.pack(fill="x", padx=18, pady=(0, 12))

        self.status_icon = tk.Label(
            self.summary_card,
            text="●",
            font=("Segoe UI", 12),
            fg=self.accent_none,
            bg=self.card_bg
        )
        self.status_icon.pack(side="left", padx=(12, 6), pady=8)

        self.status_text = tk.Label(
            self.summary_card,
            text="Scanning windows...",
            font=("Segoe UI", 10, "bold"),
            fg=self.text_primary,
            bg=self.card_bg
        )
        self.status_text.pack(side="left", pady=8)

        self.count_badge = tk.Label(
            self.summary_card,
            text="0 Active",
            font=("Segoe UI", 9, "bold"),
            fg=self.text_secondary,
            bg="#27272a",
            padx=8,
            pady=2
        )
        self.count_badge.pack(side="right", padx=12, pady=8)

        # Content list area
        list_container = tk.Frame(self.root, bg=self.bg_color)
        list_container.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        list_header = tk.Label(
            list_container,
            text="CURRENTLY OPEN",
            font=("Segoe UI", 8, "bold"),
            fg=self.text_secondary,
            bg=self.bg_color
        )
        list_header.pack(anchor="w", pady=(0, 4))

        # Canvas with scrollbar for cards
        self.canvas = tk.Canvas(list_container, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.cards_frame = tk.Frame(self.canvas, bg=self.bg_color)

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(xscrollcommand="", yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bottom footer bar
        footer_frame = tk.Frame(self.root, bg=self.bg_color)
        footer_frame.pack(fill="x", padx=18, pady=(4, 14))

        self.last_updated_label = tk.Label(
            footer_frame,
            text="Polling every 1.5s",
            font=("Segoe UI", 8),
            fg=self.text_secondary,
            bg=self.bg_color
        )
        self.last_updated_label.pack(side="left")

        self.scan_btn = tk.Button(
            footer_frame,
            text="Scan Now",
            font=("Segoe UI", 8, "bold"),
            fg=self.text_primary,
            bg="#27272a",
            activebackground="#3f3f46",
            activeforeground=self.text_primary,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._trigger_immediate_scan
        )
        self.scan_btn.pack(side="right")

    def _render_cards(self, items):
        # Clear existing children
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        if not items:
            empty_card = tk.Frame(
                self.cards_frame,
                bg=self.card_bg,
                highlightbackground=self.card_border,
                highlightthickness=1,
                padx=16,
                pady=24
            )
            empty_card.pack(fill="x", pady=6)

            tk.Label(
                empty_card,
                text="No PWA or PiP windows detected",
                font=("Segoe UI", 10, "bold"),
                fg=self.text_secondary,
                bg=self.card_bg
            ).pack()

            tk.Label(
                empty_card,
                text="Open Netflix, YouTube, YouTube Music, MYAEW, Disney+, Paramount+ or PiP",
                font=("Segoe UI", 8),
                fg="#64748b",
                bg=self.card_bg
            ).pack(pady=(4, 0))

            self.status_icon.configure(fg=self.accent_none)
            self.status_text.configure(text="Idle — No targets active")
            self.count_badge.configure(text="0 Active", bg="#27272a", fg=self.text_secondary)
            return

        self.status_icon.configure(fg=self.accent_pwa)
        self.status_text.configure(text=f"Active targets found ({len(items)})")
        self.count_badge.configure(text=f"{len(items)} Active", bg="#14532d", fg="#86efac")

        for item in items:
            is_pip = item["category"] == "PiP"
            badge_color = self.accent_pip if is_pip else self.accent_pwa
            badge_bg = "#082f49" if is_pip else "#052e16"

            card = tk.Frame(
                self.cards_frame,
                bg=self.card_bg,
                highlightbackground=self.card_border,
                highlightthickness=1,
                padx=14,
                pady=12
            )
            card.pack(fill="x", pady=4)

            # Card Header row
            header_row = tk.Frame(card, bg=self.card_bg)
            header_row.pack(fill="x")

            name_lbl = tk.Label(
                header_row,
                text=item["display_name"],
                font=("Segoe UI", 12, "bold"),
                fg=self.text_primary,
                bg=self.card_bg
            )
            name_lbl.pack(side="left")

            category_badge = tk.Label(
                header_row,
                text=item["category"],
                font=("Segoe UI", 8, "bold"),
                fg=badge_color,
                bg=badge_bg,
                padx=6,
                pady=2
            )
            category_badge.pack(side="right")

            # Details row
            details_text = f"Window Title: \"{item['window_title']}\"  •  HWND: {hex(item['hwnd'])}"
            details_lbl = tk.Label(
                card,
                text=details_text,
                font=("Segoe UI", 8),
                fg=self.text_secondary,
                bg=self.card_bg,
                anchor="w",
                justify="left"
            )
            details_lbl.pack(fill="x", pady=(6, 0))

    def _trigger_immediate_scan(self):
        if not self.is_scanning:
            threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        self.is_scanning = True
        try:
            results = self.scanner.scan()
            self.root.after(0, self._on_scan_completed, results)
        except Exception as e:
            pass
        finally:
            self.is_scanning = False

    def _on_scan_completed(self, results):
        self.detected_items = results
        self._render_cards(results)
        cur_time = time.strftime("%H:%M:%S")
        self.last_updated_label.configure(text=f"Last updated: {cur_time}")

    def _start_scan_loop(self):
        def loop():
            while True:
                if not self.is_scanning:
                    self._scan_worker()
                time.sleep(1.5)

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = DetectorGUI(root)
    root.mainloop()
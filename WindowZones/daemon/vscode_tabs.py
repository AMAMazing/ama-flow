import os
import time
import ctypes
import win32gui
import win32con

from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QPushButton, QLabel,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QObject, QTimer, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFontMetrics, QMouseEvent

try:
    from ..core.config import CONFIG_PATH, load_config
    from ..core.vscode_hub_engine import get_hub_engine
    from ..core.win_utils import (
        get_open_vscode_windows,
        get_monitor_info_from_hwnd,
        get_window_visual_rect,
        get_foreground_hwnd,
        activate_window,
        close_window,
        position_window,
        is_window_minimized,
        is_window_maximized,
        get_window_pid,
    )
    from ..ui.vscode_hub import VSCodeHubDropdown
except (ImportError, ValueError):
    from core.config import CONFIG_PATH, load_config
    from core.vscode_hub_engine import get_hub_engine
    from core.win_utils import (
        get_open_vscode_windows,
        get_monitor_info_from_hwnd,
        get_window_visual_rect,
        get_foreground_hwnd,
        activate_window,
        close_window,
        position_window,
        is_window_minimized,
        is_window_maximized,
        get_window_pid,
    )
    from ui.vscode_hub import VSCodeHubDropdown


TAB_BAR_HEIGHT_LOGICAL = 36


def get_tab_bar_physical_height(scale=1.0):
    return max(28, int(round(TAB_BAR_HEIGHT_LOGICAL * (scale or 1.0))))


class TabItemWidget(QFrame):
    activated = pyqtSignal(int)
    close_requested = pyqtSignal(int)

    def __init__(self, hwnd, label_text, full_title, icon_path=None, is_active=False, parent=None):
        super().__init__(parent)
        self.hwnd = int(hwnd)
        self.label_text = label_text
        self.full_title = full_title
        self.icon_path = icon_path
        self.is_active = is_active
        self._hovered = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        self.setMinimumWidth(104)
        self.setMaximumWidth(215)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setToolTip(full_title)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 2, 6, 2)
        layout.setSpacing(6)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(18, 18)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._set_icon(icon_path)
        layout.addWidget(self.icon_lbl)

        self.title_lbl = QLabel()
        self.title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.title_lbl, 1)

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setToolTip("Close VS Code window")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                color: #8f8f9e;
                font-size: 13px;
                font-weight: 600;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.14);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: #e81123;
                color: #ffffff;
            }
        """)
        self.close_btn.clicked.connect(lambda: self.close_requested.emit(self.hwnd))
        layout.addWidget(self.close_btn)

        self._apply_style()
        self._update_elided_text()

    def _set_icon(self, icon_path):
        self.icon_path = icon_path
        self.icon_lbl.clear()
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if not pix.isNull():
                self.icon_lbl.setPixmap(
                    pix.scaled(
                        16,
                        16,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.icon_lbl.setStyleSheet("background: transparent; border: none;")
                return
        self.icon_lbl.setText("📁")
        self.icon_lbl.setStyleSheet("font-size: 13px; color: #d4d4d4; background: transparent; border: none;")

    def _update_elided_text(self):
        fm = QFontMetrics(self.title_lbl.font())
        avail = max(40, self.width() - 56)
        elided = fm.elidedText(self.label_text, Qt.TextElideMode.ElideRight, avail)
        self.title_lbl.setText(elided)

    def _apply_style(self):
        if self.is_active:
            self.setStyleSheet("""
                TabItemWidget {
                    background: #26262d;
                    border-top: 2px solid #007acc;
                    border-left: 1px solid #3a3a45;
                    border-right: 1px solid #3a3a45;
                    border-bottom: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
            """)
            self.title_lbl.setStyleSheet(
                "color: #ffffff; font-size: 12px; font-weight: 600; background: transparent; border: none;"
            )
        else:
            bg = "#212128" if self._hovered else "#17171c"
            self.setStyleSheet(f"""
                TabItemWidget {{
                    background: {bg};
                    border-top: 1px solid transparent;
                    border-left: 1px solid transparent;
                    border-right: 1px solid #26262f;
                    border-bottom: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }}
            """)
            self.title_lbl.setStyleSheet(
                "color: #a6a6b4; font-size: 12px; font-weight: 500; background: transparent; border: none;"
            )

    def update_state(self, label_text, full_title, icon_path, is_active):
        if label_text != self.label_text:
            self.label_text = label_text
            self._update_elided_text()
        if full_title != self.full_title:
            self.full_title = full_title
            self.setToolTip(full_title)
        if icon_path != self.icon_path:
            self._set_icon(icon_path)
        if is_active != self.is_active:
            self.is_active = is_active
            self._apply_style()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided_text()

    def enterEvent(self, event):
        self._hovered = True
        if not self.is_active:
            self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if not self.is_active:
            self._apply_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.hwnd)
            event.accept()
            return
        if event.button() == Qt.MouseButton.MiddleButton:
            self.close_requested.emit(self.hwnd)
            event.accept()
            return
        super().mousePressEvent(event)


class PlusTabButton(QPushButton):
    """
    Chrome-style '+' button next to VS Code tabs.
    Visually connects its bottom edge directly into VSCodeHubDropdown when open.
    """
    def __init__(self, parent=None):
        super().__init__("+", parent)
        self._connected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(30, 28)
        self.setToolTip("Open a VS Code project")
        self._apply_style()

    def set_connected(self, connected: bool):
        if self._connected != connected:
            self._connected = connected
            self._apply_style()

    def _apply_style(self):
        if self._connected:
            self.setStyleSheet("""
                PlusTabButton {
                    background: #1e1e23;
                    color: #ffffff;
                    border-top: 1.5px solid #007acc;
                    border-left: 1.5px solid #007acc;
                    border-right: 1.5px solid #007acc;
                    border-bottom: none;
                    border-top-left-radius: 7px;
                    border-top-right-radius: 7px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                    font-size: 16px;
                    font-weight: 600;
                    padding-bottom: 1px;
                }
            """)
        else:
            self.setStyleSheet("""
                PlusTabButton {
                    background: transparent;
                    color: #b4b4c2;
                    border: 1px solid transparent;
                    border-radius: 7px;
                    font-size: 16px;
                    font-weight: 600;
                    padding-bottom: 1px;
                }
                PlusTabButton:hover {
                    background: #292932;
                    color: #ffffff;
                    border: 1px solid #3c3c48;
                }
                PlusTabButton:pressed {
                    background: #1e1e24;
                    color: #38bdf8;
                }
            """)


class VSCodeTabBar(QWidget):
    tab_clicked = pyqtSignal(int)
    tab_close_clicked = pyqtSignal(int)
    plus_clicked = pyqtSignal()
    drag_delta = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WindowZonesVSCodeTabBar")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedHeight(TAB_BAR_HEIGHT_LOGICAL)

        self._tab_widgets = {}
        self._ordered_hwnds = []
        self._dragging = False
        self._drag_last_global = QPoint()

        root = QHBoxLayout(self)
        root.setContentsMargins(6, 5, 6, 0)
        root.setSpacing(3)

        self.tabs_layout = QHBoxLayout()
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(2)
        root.addLayout(self.tabs_layout)

        self.plus_btn = PlusTabButton(self)
        self.plus_btn.clicked.connect(self.plus_clicked.emit)
        root.addWidget(self.plus_btn, 0, Qt.AlignmentFlag.AlignBottom)

        root.addStretch(1)

    def set_tabs(self, tab_entries, active_hwnd):
        """
        tab_entries: list of dicts with keys: hwnd, name, title, icon
        """
        new_order = [e["hwnd"] for e in tab_entries]
        if new_order != self._ordered_hwnds:
            # Clear layout and rebuild in stable order
            while self.tabs_layout.count():
                item = self.tabs_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
            self._tab_widgets.clear()
            self._ordered_hwnds = list(new_order)

            for entry in tab_entries:
                hwnd = entry["hwnd"]
                tab = TabItemWidget(
                    hwnd=hwnd,
                    label_text=entry["name"],
                    full_title=entry["title"],
                    icon_path=entry.get("icon"),
                    is_active=(hwnd == active_hwnd),
                    parent=self,
                )
                tab.activated.connect(self.tab_clicked.emit)
                tab.close_requested.connect(self.tab_close_clicked.emit)
                self.tabs_layout.addWidget(tab, 0, Qt.AlignmentFlag.AlignBottom)
                self._tab_widgets[hwnd] = tab
        else:
            for entry in tab_entries:
                hwnd = entry["hwnd"]
                tab = self._tab_widgets.get(hwnd)
                if tab:
                    tab.update_state(
                        label_text=entry["name"],
                        full_title=entry["title"],
                        icon_path=entry.get("icon"),
                        is_active=(hwnd == active_hwnd),
                    )

        # Dynamically shrink tab max-width if many tabs are open so '+' always stays visible
        count = max(1, len(tab_entries))
        avail_w = max(160, self.width() - 56)
        per_tab_max = max(86, min(215, (avail_w // count) - 4))
        for tab in self._tab_widgets.values():
            tab.setMaximumWidth(per_tab_max)
            tab.setMinimumWidth(min(104, per_tab_max))

    def get_plus_global_rect(self) -> QRect:
        top_left = self.plus_btn.mapToGlobal(QPoint(0, 0))
        return QRect(top_left, self.plus_btn.size())

    def set_plus_connected(self, connected: bool):
        self.plus_btn.set_connected(connected)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        # Sleek Chrome-style dark tab strip header
        painter.setPen(QPen(QColor("#2c2c36"), 1))
        painter.setBrush(QBrush(QColor("#141419")))
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, 4), 8, 8)

        # Subtle bottom seam connecting cleanly to VS Code window below
        painter.setPen(QPen(QColor("#2c2c36"), 1))
        painter.drawLine(0, rect.height() - 1, rect.width(), rect.height() - 1)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_last_global = event.globalPosition().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            cur = event.globalPosition().toPoint()
            dx = cur.x() - self._drag_last_global.x()
            dy = cur.y() - self._drag_last_global.y()
            if dx or dy:
                self._drag_last_global = cur
                self.drag_delta.emit(dx, dy)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        super().mouseReleaseEvent(event)


class VSCodeTabsManager(QObject):
    """
    Monitors open VS Code windows and manages the Chrome-style tab bar above VS Code.
    Modes (configured in Workspace Settings):
      - Auto: activates as soon as 2+ VS Code windows are open
      - Enabled: active whenever 1+ VS Code window is open
      - Disabled: never shown
    """
    def __init__(self, engine=None, on_open_hub=None, parent=None):
        super().__init__(parent)
        self.engine = engine or get_hub_engine()
        self.on_open_hub = on_open_hub
        self.mode = "Auto"

        self._tab_order = []
        self._active_hwnd = None
        self._tabs_active = False
        self._adjusted_hwnds = {}
        self._pending_snap_rect = None
        self._pending_snap_until = 0.0
        self._last_dropdown_hide_ts = 0.0
        self._last_geometry = None

        self.tab_bar = VSCodeTabBar()
        self.tab_bar.tab_clicked.connect(self._on_tab_clicked)
        self.tab_bar.tab_close_clicked.connect(self._on_tab_close_clicked)
        self.tab_bar.plus_clicked.connect(self._on_plus_clicked)
        self.tab_bar.drag_delta.connect(self._on_bar_dragged)

        self.dropdown = VSCodeHubDropdown(engine=self.engine)
        self.dropdown.closed.connect(self._on_dropdown_closed)
        self.dropdown.open_full_hub_requested.connect(self._on_open_full_hub)
        self.dropdown.content.project_launched.connect(self._on_project_launched_from_dropdown)

        self.engine.projects_updated.connect(lambda _p: self.refresh_now())

        self.reload_mode_from_config()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.on_tick)
        self.poll_timer.start(100)

    def reload_mode_from_config(self):
        cfg = load_config(CONFIG_PATH)
        mode = cfg.get("layout_settings", {}).get("vscode_tabs_mode", "Auto")
        if mode not in ("Auto", "Enabled", "Disabled"):
            mode = "Auto"
        self.mode = mode
        if self.mode == "Disabled" and self._tabs_active:
            self._deactivate_tabs()

    def is_tabs_active_for_count(self, count: int) -> bool:
        if self.mode == "Disabled":
            return False
        if self.mode == "Enabled":
            return count >= 1
        return count >= 2

    def should_reserve_top_space(self) -> bool:
        if self.mode == "Disabled":
            return False
        wins = get_open_vscode_windows()
        return self.is_tabs_active_for_count(len(wins))

    def refresh_now(self):
        self.on_tick()

    def _find_qscreen(self, device_name):
        if device_name:
            for scr in QApplication.screens():
                if scr.name() == device_name:
                    return scr
        return QApplication.primaryScreen()

    def _phys_rect_to_qt_rect(self, phys_x, phys_y, phys_w, phys_h, mon_info):
        scr = self._find_qscreen(mon_info.get("device"))
        if not scr:
            return QRect(int(phys_x), int(phys_y), int(phys_w), int(phys_h)), QRect(0, 0, 1920, 1080)
        sg = scr.geometry()
        mx, my, mw, mh = mon_info["monitor"]
        sx = (sg.width() / float(mw)) if mw > 0 else 1.0
        sy = (sg.height() / float(mh)) if mh > 0 else 1.0

        lx = sg.x() + int(round((phys_x - mx) * sx))
        ly = sg.y() + int(round((phys_y - my) * sy))
        lw = max(120, int(round(phys_w * sx)))
        lh = max(TAB_BAR_HEIGHT_LOGICAL, int(round(phys_h * sy)))
        return QRect(lx, ly, lw, lh), scr.availableGeometry()

    def _ensure_top_room_for_window(self, hwnd, win_rect, mon_info, is_max):
        if is_max or not win_rect:
            return win_rect
        wx, wy, ww, wh = mon_info["work"]
        bar_h_phys = get_tab_bar_physical_height(mon_info.get("scale", 1.0))
        needed_top = wy + bar_h_phys

        if win_rect["y"] < needed_top and win_rect["y"] >= wy - 6:
            # Avoid fighting if user is actively holding left mouse button to drag
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                return win_rect
            delta = needed_top - win_rect["y"]
            new_h = win_rect["height"]
            if needed_top + new_h > wy + wh:
                new_h = max(240, (wy + wh) - needed_top)
            new_rect = {
                "x": win_rect["x"],
                "y": needed_top,
                "width": win_rect["width"],
                "height": new_h,
            }
            if hwnd not in self._adjusted_hwnds:
                self._adjusted_hwnds[hwnd] = {
                    "orig_y": win_rect["y"],
                    "orig_h": win_rect["height"],
                    "delta": delta,
                }
            position_window(hwnd, new_rect, no_activate=True)
            updated = get_window_visual_rect(hwnd)
            return updated or new_rect
        return win_rect

    def _restore_adjusted_windows(self):
        for hwnd, info in list(self._adjusted_hwnds.items()):
            try:
                if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd) and not is_window_minimized(hwnd) and not is_window_maximized(hwnd):
                    cur = get_window_visual_rect(hwnd)
                    if cur and abs(cur["y"] - (info["orig_y"] + info["delta"])) <= 12:
                        restored = {
                            "x": cur["x"],
                            "y": info["orig_y"],
                            "width": cur["width"],
                            "height": cur["height"] + info["delta"],
                        }
                        position_window(hwnd, restored, no_activate=True)
            except Exception:
                pass
        self._adjusted_hwnds.clear()

    def _deactivate_tabs(self):
        self._tabs_active = False
        if self.dropdown.isVisible():
            self.dropdown.hide()
        if self.tab_bar.isVisible():
            self.tab_bar.hide()
        self.tab_bar.set_plus_connected(False)
        self._last_geometry = None
        self._restore_adjusted_windows()

    def _sync_z_order(self, active_hwnd):
        try:
            bar_hwnd = int(self.tab_bar.winId())
            if not bar_hwnd or not active_hwnd:
                return
            fg = get_foreground_hwnd()
            if fg == active_hwnd or self.dropdown.isVisible():
                win32gui.SetWindowPos(
                    bar_hwnd,
                    win32con.HWND_TOP,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                )
                return

            prev = win32gui.GetWindow(active_hwnd, win32con.GW_HWNDPREV)
            if prev == bar_hwnd:
                return
            # Walk up past own process helper windows if needed
            guard = 0
            while prev and get_window_pid(prev) == os.getpid() and guard < 6:
                prev = win32gui.GetWindow(prev, win32con.GW_HWNDPREV)
                guard += 1

            insert_after = prev if prev else win32con.HWND_TOP
            win32gui.SetWindowPos(
                bar_hwnd,
                insert_after,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def on_tick(self):
        wins = get_open_vscode_windows()
        win_by_hwnd = {w["hwnd"]: w for w in wins}

        # Clean up stale entries from order & adjusted map
        self._tab_order = [h for h in self._tab_order if h in win_by_hwnd]
        for h in list(self._adjusted_hwnds.keys()):
            if h not in win_by_hwnd:
                del self._adjusted_hwnds[h]

        new_hwnds = []
        for w in wins:
            if w["hwnd"] not in self._tab_order:
                self._tab_order.append(w["hwnd"])
                new_hwnds.append(w["hwnd"])

        # If a new VS Code window was just launched from the '+' dropdown, stack it into the active slot
        if new_hwnds and self._pending_snap_rect and time.monotonic() <= self._pending_snap_until:
            for nh in new_hwnds:
                position_window(nh, self._pending_snap_rect, no_activate=False)
                self._active_hwnd = nh
            self._pending_snap_rect = None

        if not self.is_tabs_active_for_count(len(wins)):
            if self._tabs_active or self.tab_bar.isVisible():
                self._deactivate_tabs()
            return

        self._tabs_active = True

        fg = get_foreground_hwnd()
        if fg in win_by_hwnd and not win_by_hwnd[fg]["is_minimized"]:
            self._active_hwnd = fg
        elif self._active_hwnd not in win_by_hwnd or win_by_hwnd[self._active_hwnd]["is_minimized"]:
            # Pick front-most non-minimized VS Code window
            non_min = [w for w in wins if not w["is_minimized"]]
            self._active_hwnd = non_min[0]["hwnd"] if non_min else None

        if not self._active_hwnd or self._active_hwnd not in win_by_hwnd:
            if self.tab_bar.isVisible() and not self.dropdown.isVisible():
                self.tab_bar.hide()
            return

        active_info = win_by_hwnd[self._active_hwnd]
        if active_info["is_minimized"]:
            if self.tab_bar.isVisible() and not self.dropdown.isVisible():
                self.tab_bar.hide()
            return

        mon_info = get_monitor_info_from_hwnd(self._active_hwnd)
        win_rect = active_info["rect"]
        if not win_rect:
            return

        win_rect = self._ensure_top_room_for_window(
            self._active_hwnd, win_rect, mon_info, active_info["is_maximized"]
        )
        if not win_rect:
            return

        bar_h_phys = get_tab_bar_physical_height(mon_info.get("scale", 1.0))
        wx, wy, ww, wh = mon_info["work"]

        bar_x_phys = win_rect["x"]
        bar_y_phys = max(wy, win_rect["y"] - bar_h_phys)
        bar_w_phys = win_rect["width"]

        qt_rect, _avail = self._phys_rect_to_qt_rect(bar_x_phys, bar_y_phys, bar_w_phys, bar_h_phys, mon_info)

        # Build tab entries in stable order with project icons from shared VSCodeHubEngine
        tab_entries = []
        for hwnd in self._tab_order:
            w = win_by_hwnd.get(hwnd)
            if not w:
                continue
            proj_name, _proj, icon_path = self.engine.get_project_for_window_title(w["title"])
            tab_entries.append({
                "hwnd": hwnd,
                "name": proj_name,
                "title": w["title"],
                "icon": icon_path,
            })

        if self._last_geometry != qt_rect:
            self.tab_bar.setGeometry(qt_rect)
            self._last_geometry = qt_rect

        self.tab_bar.set_tabs(tab_entries, self._active_hwnd)

        if not self.tab_bar.isVisible():
            self.tab_bar.show()

        self._sync_z_order(self._active_hwnd)

    def _on_tab_clicked(self, hwnd):
        if self.dropdown.isVisible():
            self.dropdown.hide()

        prev_hwnd = self._active_hwnd
        prev_rect = get_window_visual_rect(prev_hwnd) if prev_hwnd and prev_hwnd != hwnd else None
        prev_max = is_window_maximized(prev_hwnd) if prev_hwnd and prev_hwnd != hwnd else False

        self._active_hwnd = hwnd
        # Keep stacked tabs seamlessly aligned in the same slot if switching from a non-maximized window
        if prev_rect and not prev_max and not is_window_maximized(hwnd):
            cur_rect = get_window_visual_rect(hwnd)
            if cur_rect and cur_rect != prev_rect:
                position_window(hwnd, prev_rect, no_activate=False)
        activate_window(hwnd)
        QTimer.singleShot(30, self.refresh_now)

    def _on_tab_close_clicked(self, hwnd):
        close_window(hwnd)
        QTimer.singleShot(150, self.refresh_now)

    def _on_plus_clicked(self):
        # Debounce so clicking '+' while dropdown is open toggles it closed cleanly
        if time.monotonic() - self._last_dropdown_hide_ts < 0.22:
            return
        if self.dropdown.isVisible():
            self.dropdown.hide()
            return

        plus_rect = self.tab_bar.get_plus_global_rect()
        mon_info = get_monitor_info_from_hwnd(self._active_hwnd)
        scr = self._find_qscreen(mon_info.get("device"))
        avail = scr.availableGeometry() if scr else QRect(0, 0, 1920, 1080)

        self.tab_bar.set_plus_connected(True)
        self.dropdown.open_from_anchor(plus_rect, avail)

    def _on_dropdown_closed(self):
        self._last_dropdown_hide_ts = time.monotonic()
        self.tab_bar.set_plus_connected(False)

    def _on_open_full_hub(self):
        if self.on_open_hub:
            self.on_open_hub()

    def _on_project_launched_from_dropdown(self, _path):
        # Remember active VS Code window rect so the newly spawned window snaps into the tab group
        if self._active_hwnd and not is_window_maximized(self._active_hwnd):
            self._pending_snap_rect = get_window_visual_rect(self._active_hwnd)
            self._pending_snap_until = time.monotonic() + 8.0

    def _on_bar_dragged(self, dx, dy):
        if not self._active_hwnd or is_window_maximized(self._active_hwnd):
            return
        mon_info = get_monitor_info_from_hwnd(self._active_hwnd)
        scale = mon_info.get("scale", 1.0) or 1.0
        rect = get_window_visual_rect(self._active_hwnd)
        if not rect:
            return
        new_rect = {
            "x": rect["x"] + int(round(dx * scale)),
            "y": rect["y"] + int(round(dy * scale)),
            "width": rect["width"],
            "height": rect["height"],
        }
        position_window(self._active_hwnd, new_rect, no_activate=True)
        self.refresh_now()
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QLineEdit, QComboBox, QMessageBox, QTabWidget,
    QApplication
)
from PyQt6.QtCore import Qt, QMimeData, QPoint, pyqtSignal
from PyQt6.QtGui import QDrag

try:
    from core.win_utils import get_open_windows
    from core.detector import detector
except (ImportError, ValueError):
    from ..core.win_utils import get_open_windows
    from ..core.detector import detector


class DraggableAppChip(QPushButton):
    """
    A chip representing an assigned app that can be clicked to remove
    or dragged to another aspect ratio category.
    """
    def __init__(self, app_name, parent_profile, on_remove, parent=None):
        super().__init__(f"{app_name}  ×", parent)
        self.app_name = app_name
        self.parent_profile = parent_profile
        self.on_remove = on_remove
        self.drag_start_pos = None

        self.setObjectName("tag_btn")
        self.setToolTip(f"Drag to move to another ratio, or click '×' to remove")
        self.clicked.connect(lambda: self.on_remove(self.parent_profile, self.app_name))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or not self.drag_start_pos:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-appzones-media", f"{self.parent_profile}::{self.app_name}".encode("utf-8"))
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)


class AspectRatioRow(QFrame):
    """
    A card representing an aspect ratio category.
    Accepts dropped media chips and supports reordering & deletion.
    """
    def __init__(self, prof_name, prof_data, on_delete, on_move, on_drop_app, on_remove_app, can_move_up, can_move_down, parent=None):
        super().__init__(parent)
        self.prof_name = prof_name
        self.prof_data = prof_data
        self.on_delete = on_delete
        self.on_move = on_move
        self.on_drop_app = on_drop_app
        self.on_remove_app = on_remove_app

        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Reorder Buttons (Up / Down)
        order_box = QVBoxLayout()
        order_box.setSpacing(1)
        btn_up = QPushButton("▲")
        btn_up.setFixedSize(16, 14)
        btn_up.setStyleSheet("background: transparent; color: #8e8e93; border: none; font-size: 9px;")
        btn_up.setEnabled(can_move_up)
        btn_up.clicked.connect(lambda: self.on_move(self.prof_name, -1))
        order_box.addWidget(btn_up)

        btn_down = QPushButton("▼")
        btn_down.setFixedSize(16, 14)
        btn_down.setStyleSheet("background: transparent; color: #8e8e93; border: none; font-size: 9px;")
        btn_down.setEnabled(can_move_down)
        btn_down.clicked.connect(lambda: self.on_move(self.prof_name, 1))
        order_box.addWidget(btn_down)
        layout.addLayout(order_box)

        # Profile Title & Aspect Ratio Badge
        info_box = QHBoxLayout()
        info_box.setSpacing(8)

        lbl_name = QLabel(self.prof_name)
        lbl_name.setStyleSheet("font-weight: 600; color: #f2f2f7; font-size: 13px; min-width: 100px;")
        info_box.addWidget(lbl_name)

        ar_str = self.prof_data.get("aspect_ratio", "16:9") if isinstance(self.prof_data, dict) else str(self.prof_data)
        lbl_ar = QLabel(ar_str)
        lbl_ar.setStyleSheet("color: #0a84ff; font-weight: 600; font-size: 11px; background: rgba(10, 132, 255, 0.14); padding: 3px 8px; border-radius: 5px;")
        info_box.addWidget(lbl_ar)
        layout.addLayout(info_box)

        # App Chips container
        self.chips_container = QWidget()
        self.chips_container.setStyleSheet("background: transparent;")
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(6)

        apps = self.prof_data.get("apps", []) if isinstance(self.prof_data, dict) else []
        for app in apps:
            chip = DraggableAppChip(app, self.prof_name, self.on_remove_app, self)
            self.chips_layout.addWidget(chip)

        self.chips_layout.addStretch()
        layout.addWidget(self.chips_container, 1)

        # Delete Category Button (allows deleting ANY aspect ratio)
        btn_delete = QPushButton("✕")
        btn_delete.setFixedSize(22, 22)
        btn_delete.setToolTip(f"Delete '{self.prof_name}' aspect ratio category")
        btn_delete.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #636366;
                border: none;
                font-size: 13px;
                border-radius: 11px;
            }
            QPushButton:hover {
                background: #ff453a;
                color: #ffffff;
            }
        """)
        btn_delete.clicked.connect(lambda: self.on_delete(self.prof_name))
        layout.addWidget(btn_delete)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-appzones-media"):
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #202028;
                    border: 1px solid #0a84ff;
                    border-radius: 10px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 10px;
            }
        """)

    def dropEvent(self, event):
        raw = event.mimeData().data("application/x-appzones-media").data().decode("utf-8")
        src_profile, app_name = raw.split("::", 1)
        self.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 10px;
            }
        """)
        if src_profile != self.prof_name:
            self.on_drop_app(src_profile, self.prof_name, app_name)
        event.acceptProposedAction()


class AddAspectRatioDialog(QDialog):
    """
    Clean Apple-style modal dialog to add an aspect ratio:
    - Tab 1: Custom Ratio (enter ratio or common format)
    - Tab 2: From Open Window (select any currently open window to measure its ratio!)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Aspect Ratio")
        self.setFixedSize(420, 290)
        self.setStyleSheet("""
            QDialog {
                background-color: #121214;
            }
            QLabel {
                color: #e5e5ea;
                font-size: 12px;
            }
            QLineEdit, QComboBox {
                background-color: #1c1c1e;
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                background-color: #161619;
                padding: 12px;
            }
            QTabBar::tab {
                background: #1c1c1e;
                color: #8e8e93;
                padding: 6px 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: #2c2c30;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

        # TAB 1: Custom Ratio
        tab_custom = QWidget()
        lay_custom = QVBoxLayout(tab_custom)
        lay_custom.setSpacing(10)

        lay_custom.addWidget(QLabel("Profile Name:"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Cinema (2.39:1) or Anime")
        lay_custom.addWidget(self.txt_name)

        lay_custom.addWidget(QLabel("Aspect Ratio (e.g. 16:9, 4:3, 2.39:1, 1:1):"))
        self.txt_ratio = QLineEdit()
        self.txt_ratio.setPlaceholderText("16:9")
        lay_custom.addWidget(self.txt_ratio)
        lay_custom.addStretch()

        self.tabs.addTab(tab_custom, "Custom Ratio")

        # TAB 2: From Open Window
        tab_window = QWidget()
        lay_window = QVBoxLayout(tab_window)
        lay_window.setSpacing(10)

        lay_window.addWidget(QLabel("Select an open window to measure its aspect ratio:"))
        self.combo_windows = QComboBox()

        self.open_wins_data = []
        try:
            detected = detector.get_open_chrome_and_pwa_windows()
            # Also general windows
            general = get_open_windows()
            seen_hwnds = set()

            for w in detected:
                if w["hwnd"] not in seen_hwnds and "Visual Studio Code" not in w["app_name"] and "AppZones" not in w["app_name"]:
                    self.open_wins_data.append((w["app_name"], w["hwnd"]))
                    seen_hwnds.add(w["hwnd"])

            for title, hwnd in general:
                if hwnd not in seen_hwnds and "visual studio code" not in title.lower() and "appzones" not in title.lower() and "cline" not in title.lower():
                    self.open_wins_data.append((title, hwnd))
                    seen_hwnds.add(hwnd)
        except Exception:
            pass

        if not self.open_wins_data:
            self.combo_windows.addItem("No other windows currently open", None)
        else:
            for title, hwnd in self.open_wins_data:
                self.combo_windows.addItem(title[:35], hwnd)

        lay_window.addWidget(self.combo_windows)

        lay_window.addWidget(QLabel("Assign default ratio for this window:"))
        self.txt_win_ratio = QLineEdit("16:9")
        lay_window.addWidget(self.txt_win_ratio)
        lay_window.addStretch()

        self.tabs.addTab(tab_window, "From Open Window")

        layout.addWidget(self.tabs)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("secondary_action")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Add Profile")
        btn_save.setObjectName("primary_action")
        btn_save.clicked.connect(self.accept)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def get_result(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            name = self.txt_name.text().strip()
            ratio = self.txt_ratio.text().strip() or "16:9"
            if not name:
                name = f"Ratio ({ratio})"
            return name, ratio, []
        else:
            sel_text = self.combo_windows.currentText().strip()
            ratio = self.txt_win_ratio.text().strip() or "16:9"
            if not sel_text or "No other windows" in sel_text:
                return f"Window ({ratio})", ratio, []
            name = f"{sel_text} ({ratio})"
            return name, ratio, [sel_text]
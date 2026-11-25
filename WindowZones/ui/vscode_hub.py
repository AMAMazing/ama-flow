import os
import sys
import ctypes
from datetime import datetime

if __package__ in (None, ""):
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QScrollArea, QLabel, QMessageBox,
    QLineEdit, QFrame, QDialog, QDialogButtonBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QPen, QBrush, QMouseEvent, QPixmap, QKeyEvent
)
from PyQt6.QtSvg import QSvgRenderer

try:
    from core.vscode_hub_engine import get_hub_engine, find_project_icon
    from core.config import CONFIG_PATH, load_config, save_config
except (ImportError, ValueError):
    from ..core.vscode_hub_engine import get_hub_engine, find_project_icon
    from ..core.config import CONFIG_PATH, load_config, save_config


SVG_ICONS = {
    "ignore": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M22 19V9C22 7.89543 21.1046 7 20 7H12L10 5H4C2.89543 5 2 5.89543 2 7V19C2 20.1046 2.89543 21 4 21H20C21.1046 21 22 20.1046 22 19Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M9 14H15" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
    "minimize": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M20 12H4" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
    "maximize": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M8 3H5C3.89543 3 3 3.89543 3 5V8" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M16 3H19C20.1046 3 21 3.89543 21 5V8" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M8 21H5C3.89543 21 3 20.1046 3 19V16" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M16 21H19C20.1046 21 21 20.1046 21 19V16" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
    "restore": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M8 21H5C3.89543 21 3 20.1046 3 19V14" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M21 10V5C21 3.89543 20.1046 3 19 3H14" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M10 21V19C10 17.8954 10.8954 17 12 17H19C20.1046 17 21 17.8954 21 19V21H10Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
    "close": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M18 6L6 18" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M6 6L18 18" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
    "grid": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect x="3" y="3" width="7" height="7" rx="1.5" stroke="#e1e1e1" stroke-width="2"/>
<rect x="14" y="3" width="7" height="7" rx="1.5" stroke="#e1e1e1" stroke-width="2"/>
<rect x="3" y="14" width="7" height="7" rx="1.5" stroke="#e1e1e1" stroke-width="2"/>
<rect x="14" y="14" width="7" height="7" rx="1.5" stroke="#e1e1e1" stroke-width="2"/>
</svg>""",
    "list": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M8 6H21" stroke="#e1e1e1" stroke-width="2" stroke-linecap="round"/>
<path d="M8 12H21" stroke="#e1e1e1" stroke-width="2" stroke-linecap="round"/>
<path d="M8 18H21" stroke="#e1e1e1" stroke-width="2" stroke-linecap="round"/>
<circle cx="4" cy="6" r="1.5" fill="#e1e1e1"/>
<circle cx="4" cy="12" r="1.5" fill="#e1e1e1"/>
<circle cx="4" cy="18" r="1.5" fill="#e1e1e1"/>
</svg>""",
    "expand": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M15 3H21V9" stroke="#d4d4d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M10 14L21 3" stroke="#d4d4d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M18 13V19C18 20.1046 17.1046 21 16 21H5C3.89543 21 3 20.1046 3 19V8C3 6.89543 3.89543 6 5 6H11" stroke="#d4d4d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
}


def apply_project_icon(label: QLabel, icon_path, size: int):
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedSize(size + 6, size + 6)
    label.setStyleSheet("background: transparent; border: none;")
    if icon_path and os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            return
    font_px = max(16, int(size * 0.82))
    label.setText("📁")
    label.setStyleSheet(f"font-size: {font_px}px; color: #d4d4d4; background: transparent; border: none;")


class SvgIconButton(QPushButton):
    def __init__(self, icon_name, width=36, height=28, icon_px=15, parent=None):
        super().__init__(parent)
        self._icon_px = icon_px
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._renderer = QSvgRenderer()
        self.setIconName(icon_name)

    def setIconName(self, name):
        self._icon_name = name
        if name in SVG_ICONS:
            self._renderer.load(SVG_ICONS[name].encode("utf-8"))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        x = (r.width() - self._icon_px) / 2.0
        y = (r.height() - self._icon_px) / 2.0
        self._renderer.render(painter, QRectF(x, y, self._icon_px, self._icon_px))


class ProjectCardButton(QPushButton):
    def __init__(self, project_data, compact=False, checkable=False, parent=None):
        super().__init__(parent)
        self.project_path = project_data["path"]
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if checkable:
            self.setCheckable(True)

        w, h = (132, 118) if compact else (176, 156)
        icon_sz = 34 if compact else 48
        self.setFixedSize(w, h)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(6 if compact else 10)

        icon_label = QLabel()
        apply_project_icon(icon_label, project_data.get("icon"), icon_sz)
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(project_data.get("name", ""))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_font = "12px" if compact else "13px"
        name_label.setStyleSheet(
            f"font-size: {name_font}; font-weight: 500; color: #e6e6eb; background: transparent; border: none;"
        )
        layout.addWidget(name_label)

        mtime = project_data.get("mtime")
        if mtime:
            try:
                date_str = datetime.fromtimestamp(mtime).strftime("%b %d, %Y")
                date_label = QLabel(date_str)
                date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                date_label.setStyleSheet("font-size: 10px; color: #8c8c96; background: transparent; border: none;")
                layout.addWidget(date_label)
            except Exception:
                pass

        self.setToolTip(self.project_path)
        self.setStyleSheet("""
            ProjectCardButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2d2d32, stop:1 #242428);
                border: 1px solid #3c3c44;
                border-radius: 11px;
            }
            ProjectCardButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a3a42, stop:1 #2d2d34);
                border: 1px solid #007acc;
            }
            ProjectCardButton:pressed {
                background: #1d1d20;
                border: 1px solid #1b9bff;
            }
            ProjectCardButton:checked {
                background: #0b4f7c;
                border: 1px solid #1b9bff;
            }
        """)


class ProjectListRowButton(QPushButton):
    def __init__(self, project_data, compact=False, parent=None):
        super().__init__(parent)
        self.project_path = project_data["path"]
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48 if compact else 54)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 12, 6)
        layout.setSpacing(10)

        icon_label = QLabel()
        apply_project_icon(icon_label, project_data.get("icon"), 22 if compact else 26)
        layout.addWidget(icon_label)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(1)

        name_lbl = QLabel(project_data.get("name", ""))
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #ededf2; background: transparent; border: none;")
        text_box.addWidget(name_lbl)

        parent_dir = os.path.dirname(self.project_path)
        if len(parent_dir) > 48:
            parent_dir = "..." + parent_dir[-45:]
        path_lbl = QLabel(parent_dir)
        path_lbl.setStyleSheet("font-size: 10px; color: #8c8c98; background: transparent; border: none;")
        text_box.addWidget(path_lbl)
        layout.addLayout(text_box, 1)

        mtime = project_data.get("mtime")
        if mtime:
            try:
                date_str = datetime.fromtimestamp(mtime).strftime("%b %d")
                date_lbl = QLabel(date_str)
                date_lbl.setStyleSheet("font-size: 10px; color: #7e7e8a; background: transparent; border: none;")
                layout.addWidget(date_lbl)
            except Exception:
                pass

        self.setToolTip(self.project_path)
        self.setStyleSheet("""
            ProjectListRowButton {
                background: #252529;
                border: 1px solid #35353d;
                border-radius: 9px;
                text-align: left;
            }
            ProjectListRowButton:hover {
                background: #303038;
                border: 1px solid #007acc;
            }
            ProjectListRowButton:pressed {
                background: #1c1c20;
                border: 1px solid #1b9bff;
            }
        """)


class IgnoreFoldersDialog(QDialog):
    def __init__(self, all_paths, ignored_folders=None, parent=None):
        super().__init__(parent)
        self.all_paths = list(all_paths or [])
        self.selected_paths_set = set(ignored_folders or [])
        self.setWindowTitle("Select Folders to Ignore")
        self.resize(840, 560)
        self.setStyleSheet("QDialog { background-color: #1c1c20; color: #e6e6eb; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        title = QLabel("Select folders to hide from VS Code Hub")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #ffffff;")
        main_layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: #1c1c20; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #3e3e46; border-radius: 5px; min-height: 24px; }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, 1)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate()

    def _populate(self):
        cols = 4
        norm_selected = {os.path.normcase(os.path.normpath(p)) for p in self.selected_paths_set}
        for i, path in enumerate(self.all_paths):
            try:
                mtime = os.path.getmtime(path)
            except Exception:
                mtime = 0
            pdata = {
                "path": path,
                "name": os.path.basename(path) or path,
                "mtime": mtime,
                "icon": find_project_icon(path),
            }
            btn = ProjectCardButton(pdata, compact=False, checkable=True)
            if os.path.normcase(os.path.normpath(path)) in norm_selected:
                btn.setChecked(True)
            btn.toggled.connect(self._on_toggled)
            self.grid_layout.addWidget(btn, i // cols, i % cols)
        self.grid_layout.setRowStretch((len(self.all_paths) // cols) + 1, 1)

    def _on_toggled(self, checked):
        btn = self.sender()
        if not btn:
            return
        if checked:
            self.selected_paths_set.add(btn.project_path)
        else:
            self.selected_paths_set = {
                p for p in self.selected_paths_set
                if os.path.normcase(os.path.normpath(p)) != os.path.normcase(os.path.normpath(btn.project_path))
            }

    def selected_paths(self):
        return list(self.selected_paths_set)


class VSCodeHubContentWidget(QWidget):
    """
    Shared VS Code Hub browser engine UI used by both:
    - The standalone VS Code Hub window (hotkey 4)
    - The connected '+' dropdown on the VS Code tab bar
    Supports real-time search, Grid view (like VSCode-Hub), and List view.
    """
    project_launched = pyqtSignal(str)
    view_mode_changed = pyqtSignal(str)
    projects_count_changed = pyqtSignal(int)

    def __init__(
        self,
        engine=None,
        compact=False,
        initial_view_mode="grid",
        force_new_window=False,
        show_expand_btn=False,
        on_expand=None,
        parent=None,
    ):
        super().__init__(parent)
        self.engine = engine or get_hub_engine()
        self.compact = compact
        self.view_mode = initial_view_mode if initial_view_mode in ("grid", "list") else "grid"
        self.force_new_window = force_new_window
        self.show_expand_btn = show_expand_btn
        self.on_expand = on_expand
        self._filtered_projects = []

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(80)
        self._resize_timer.timeout.connect(self.render_projects)

        self._build_ui()
        self.engine.projects_updated.connect(self._on_projects_updated)
        self._on_projects_updated(self.engine.get_projects())

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar: Search + Grid/List Toggle (+ optional Expand Hub)
        bar = QFrame()
        bar.setStyleSheet(
            "QFrame { background: #232328; border-bottom: 1px solid #35353e; }"
        )
        bar_layout = QHBoxLayout(bar)
        if self.compact:
            bar_layout.setContentsMargins(10, 8, 10, 8)
            bar_layout.setSpacing(6)
        else:
            bar_layout.setContentsMargins(24, 12, 24, 12)
            bar_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search projects...")
        self.search_input.textChanged.connect(self.filter_projects)
        self.search_input.returnPressed.connect(self._launch_first_match)
        pad = "7px 10px" if self.compact else "10px 14px"
        fsize = "12px" if self.compact else "14px"
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: #32323a;
                border: 1px solid #44444f;
                border-radius: 7px;
                padding: {pad};
                font-size: {fsize};
                color: #ececf2;
            }}
            QLineEdit:focus {{
                border: 1px solid #007acc;
                background: #2a2a30;
            }}
        """)
        bar_layout.addWidget(self.search_input, 1)

        toggle_style = """
            QPushButton {
                background: #2c2c33;
                border: 1px solid #3e3e48;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #383842;
                border: 1px solid #555564;
            }
            QPushButton:checked {
                background: #007acc;
                border: 1px solid #299cf5;
            }
        """

        self.btn_grid = SvgIconButton("grid", width=30, height=30, icon_px=14)
        self.btn_grid.setCheckable(True)
        self.btn_grid.setToolTip("Grid view")
        self.btn_grid.setStyleSheet(toggle_style)
        self.btn_grid.clicked.connect(lambda: self.set_view_mode("grid"))
        bar_layout.addWidget(self.btn_grid)

        self.btn_list = SvgIconButton("list", width=30, height=30, icon_px=14)
        self.btn_list.setCheckable(True)
        self.btn_list.setToolTip("List view")
        self.btn_list.setStyleSheet(toggle_style)
        self.btn_list.clicked.connect(lambda: self.set_view_mode("list"))
        bar_layout.addWidget(self.btn_list)

        if self.show_expand_btn and self.on_expand:
            self.btn_expand = SvgIconButton("expand", width=30, height=30, icon_px=14)
            self.btn_expand.setToolTip("Open full VS Code Hub")
            self.btn_expand.setStyleSheet(toggle_style)
            self.btn_expand.clicked.connect(self.on_expand)
            bar_layout.addWidget(self.btn_expand)

        root.addWidget(bar)

        # Scrollable Projects Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: transparent; width: 8px; margin: 4px 2px 4px 0; }
            QScrollBar::handle:vertical { background: #3e3e46; border-radius: 4px; min-height: 28px; }
            QScrollBar::handle:vertical:hover { background: #52525e; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.items_host = QWidget()
        self.items_host.setStyleSheet("background: transparent;")
        self.content_layout.addWidget(self.items_host)
        self.content_layout.addStretch(1)

        self.scroll_area.setWidget(self.scroll_content)
        root.addWidget(self.scroll_area, 1)

        self._sync_toggle_buttons()

    def _sync_toggle_buttons(self):
        self.btn_grid.setChecked(self.view_mode == "grid")
        self.btn_list.setChecked(self.view_mode == "list")

    def set_view_mode(self, mode, emit_signal=True):
        if mode not in ("grid", "list"):
            return
        changed = (mode != self.view_mode)
        self.view_mode = mode
        self._sync_toggle_buttons()
        self.render_projects()
        if changed and emit_signal:
            self.view_mode_changed.emit(mode)

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def clear_search(self):
        self.search_input.setText("")

    def open_ignore_dialog(self):
        paths = self.engine.get_all_known_paths_for_ignore_dialog()
        dlg = IgnoreFoldersDialog(paths, self.engine.get_ignored_folders(), self)
        if dlg.exec():
            self.engine.set_ignored_folders(dlg.selected_paths())

    def _on_projects_updated(self, projects):
        self.projects_count_changed.emit(len(projects))
        self.filter_projects()

    def filter_projects(self):
        q = self.search_input.text().strip().lower()
        all_projs = self.engine.get_projects()
        if q:
            self._filtered_projects = [
                p for p in all_projs
                if q in (p.get("name") or "").lower() or q in (p.get("path") or "").lower()
            ]
        else:
            self._filtered_projects = all_projs
        self.render_projects()

    def _launch_first_match(self):
        if self._filtered_projects:
            self._open_project(self._filtered_projects[0]["path"])

    def _open_project(self, path):
        ok, err = self.engine.open_project(path, force_new_window=self.force_new_window)
        if not ok:
            QMessageBox.critical(self, "VS Code Hub", f"Failed to open project:\n{err}")
            return
        self.search_input.setText("")
        self.project_launched.emit(path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.view_mode == "grid":
            self._resize_timer.start()

    def render_projects(self):
        # Replace items_host cleanly to switch between QGridLayout and QVBoxLayout
        old_host = self.items_host
        self.content_layout.removeWidget(old_host)
        old_host.deleteLater()

        self.items_host = QWidget()
        self.items_host.setStyleSheet("background: transparent;")

        data_list = self._filtered_projects
        if not data_list:
            v = QVBoxLayout(self.items_host)
            v.setContentsMargins(20, 36, 20, 36)
            empty = QLabel("No matching VS Code projects found.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #888894; font-size: 13px; background: transparent;")
            v.addWidget(empty)
            self.content_layout.insertWidget(0, self.items_host)
            return

        if self.view_mode == "list":
            v = QVBoxLayout(self.items_host)
            m = 10 if self.compact else 24
            v.setContentsMargins(m, 10, m, 12)
            v.setSpacing(6 if self.compact else 8)
            for proj in data_list:
                row_btn = ProjectListRowButton(proj, compact=self.compact)
                row_btn.clicked.connect(lambda checked=False, p=proj["path"]: self._open_project(p))
                v.addWidget(row_btn)
        else:
            grid = QGridLayout(self.items_host)
            spacing = 10 if self.compact else 18
            margin = 12 if self.compact else 26
            card_w = 132 if self.compact else 176
            grid.setSpacing(spacing)
            grid.setContentsMargins(margin, 12 if self.compact else 24, margin, 14)

            vp_w = self.scroll_area.viewport().width()
            if vp_w <= 0:
                vp_w = self.width() or (440 if self.compact else 1080)
            avail = max(card_w, vp_w - (margin * 2))
            cols = max(1, (avail + spacing) // (card_w + spacing))

            for i, proj in enumerate(data_list):
                card = ProjectCardButton(proj, compact=self.compact)
                card.clicked.connect(lambda checked=False, p=proj["path"]: self._open_project(p))
                grid.addWidget(card, i // cols, i % cols)
            grid.setColumnStretch(cols, 1)

        self.content_layout.insertWidget(0, self.items_host)


class VSCodeHubDropdown(QWidget):
    """
    Popup dropdown visually connected directly to the '+' button on the VS Code tab bar.
    Shares the exact same VSCodeHubEngine and VSCodeHubContentWidget as VSCodeHubWindow.
    """
    closed = pyqtSignal()
    open_full_hub_requested = pyqtSignal()

    CONNECTOR_H = 9

    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine or get_hub_engine()
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.connector_left = 14
        self.connector_width = 28

        cfg = load_config(CONFIG_PATH)
        initial_view = cfg.get("layout_settings", {}).get("vscode_tabs_dropdown_view", "grid")

        root = QVBoxLayout(self)
        root.setContentsMargins(1, self.CONNECTOR_H + 1, 1, 1)
        root.setSpacing(0)

        self.content = VSCodeHubContentWidget(
            engine=self.engine,
            compact=True,
            initial_view_mode=initial_view,
            force_new_window=True,
            show_expand_btn=True,
            on_expand=self._request_full_hub,
            parent=self,
        )
        self.content.project_launched.connect(self._on_project_launched)
        self.content.view_mode_changed.connect(self._on_view_mode_changed)
        root.addWidget(self.content)

    def _request_full_hub(self):
        self.hide()
        self.open_full_hub_requested.emit()

    def _on_project_launched(self, _path):
        self.hide()

    def _on_view_mode_changed(self, mode):
        try:
            cfg = load_config(CONFIG_PATH)
            cfg.setdefault("layout_settings", {})["vscode_tabs_dropdown_view"] = mode
            save_config(cfg, CONFIG_PATH)
        except Exception:
            pass

    def open_from_anchor(self, plus_global_rect: QRect, screen_avail_rect: QRect):
        cfg = load_config(CONFIG_PATH)
        saved_view = cfg.get("layout_settings", {}).get("vscode_tabs_dropdown_view", self.content.view_mode)
        if saved_view != self.content.view_mode:
            self.content.set_view_mode(saved_view, emit_signal=False)

        self.engine.start_scan()

        popup_w = 456 if self.content.view_mode == "grid" else 390
        popup_h = 420
        popup_w = min(popup_w, max(280, screen_avail_rect.width() - 24))
        popup_h = min(popup_h, max(260, screen_avail_rect.height() - 60))

        # Align dropdown just below the '+' button, clamped horizontally to monitor
        desired_x = plus_global_rect.left() - 16
        min_x = screen_avail_rect.left() + 6
        max_x = screen_avail_rect.right() - popup_w - 6
        popup_x = max(min_x, min(desired_x, max_x))
        popup_y = plus_global_rect.bottom() - self.CONNECTOR_H + 1

        # Compute connector bridge position aligned precisely with the '+' button
        conn_l = plus_global_rect.left() - popup_x
        conn_w = max(22, plus_global_rect.width())
        conn_l = max(8, min(conn_l, popup_w - conn_w - 8))
        self.connector_left = int(conn_l)
        self.connector_width = int(conn_w)

        self.setGeometry(popup_x, popup_y, popup_w, popup_h)
        self.content.render_projects()
        self.show()
        self.raise_()
        self.activateWindow()
        self.content.focus_search()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width() - 1
        h = self.height() - 1
        top_y = float(self.CONNECTOR_H)
        r = 12.0
        c_left = float(self.connector_left)
        c_right = float(min(w - r, self.connector_left + self.connector_width))
        c_left = max(r, c_left)

        path = QPainterPath()
        # Start at top-left of connector neck (open top connects directly to '+' button)
        path.moveTo(c_left, 0.0)
        path.lineTo(c_left, top_y - 3.0)
        path.quadTo(c_left, top_y, c_left - 4.0, top_y)
        path.lineTo(r, top_y)
        path.quadTo(0.5, top_y, 0.5, top_y + r)
        path.lineTo(0.5, h - r)
        path.quadTo(0.5, h, r, h)
        path.lineTo(w - r, h)
        path.quadTo(w, h, w, h - r)
        path.lineTo(w, top_y + r)
        path.quadTo(w, top_y, w - r, top_y)
        path.lineTo(c_right + 4.0, top_y)
        path.quadTo(c_right, top_y, c_right, top_y - 3.0)
        path.lineTo(c_right, 0.0)

        fill_path = QPainterPath(path)
        fill_path.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#1e1e23")))
        painter.drawPath(fill_path)

        # Draw crisp connected border leaving the top connector seam open into the '+' button
        painter.setPen(QPen(QColor("#007acc"), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.closed.emit()


class VSCodeHubWindow(QMainWindow):
    """
    Standalone native VS Code Hub UI absorbed into WindowZones.
    Triggered by the 4th configurable global hotkey or System Tray / Control Panel.
    Powered by the exact same VSCodeHubEngine and VSCodeHubContentWidget as the tab bar '+' dropdown.
    """
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine or get_hub_engine()
        self.drag_pos = QPoint()

        self.setWindowTitle("VS Code Hub - WindowZones")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1120, 740)
        self.setMinimumSize(680, 480)

        self._build_ui()

    def _build_ui(self):
        self.background_frame = QFrame(self)
        self.background_frame.setObjectName("hubBackgroundFrame")
        self.background_frame.setStyleSheet(
            "#hubBackgroundFrame { background-color: #1c1c20; border: 1px solid #383842; border-radius: 14px; }"
        )
        self.setCentralWidget(self.background_frame)

        main_layout = QVBoxLayout(self.background_frame)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.header = self._create_header()
        main_layout.addWidget(self.header)

        self.content = VSCodeHubContentWidget(
            engine=self.engine,
            compact=False,
            initial_view_mode="grid",
            force_new_window=False,
            show_expand_btn=False,
            parent=self,
        )
        self.content.project_launched.connect(self._on_project_launched)
        self.content.projects_count_changed.connect(self._update_count_label)
        main_layout.addWidget(self.content, 1)

        self._update_count_label(len(self.engine.get_projects()))

    def _create_header(self):
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #005a9e);
                border-top-left-radius: 13px;
                border-top-right-radius: 13px;
            }
        """)
        header.setMouseTracking(True)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 8, 0)

        title = QLabel("VS Code Projects")
        title.setStyleSheet("font-size: 17px; font-weight: 600; color: white; background: transparent;")
        layout.addWidget(title)
        layout.addStretch()

        self.count_label = QLabel("Loading...")
        self.count_label.setStyleSheet(
            "font-size: 13px; color: rgba(255, 255, 255, 0.85); background: transparent; margin-right: 16px;"
        )
        layout.addWidget(self.count_label)

        btn_style = """
            QPushButton { background-color: transparent; border: none; border-radius: 5px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 0.1); }
        """

        ignore_btn = SvgIconButton("ignore", width=38, height=30, icon_px=16)
        ignore_btn.setToolTip("Manage Ignored Folders")
        ignore_btn.setStyleSheet(btn_style)
        ignore_btn.clicked.connect(self._open_ignore_folders)
        layout.addWidget(ignore_btn)

        controls = QHBoxLayout()
        controls.setSpacing(2)

        min_btn = SvgIconButton("minimize", width=38, height=30, icon_px=15)
        min_btn.setStyleSheet(btn_style)
        min_btn.clicked.connect(self.showMinimized)

        self.max_btn = SvgIconButton("maximize", width=38, height=30, icon_px=15)
        self.max_btn.setStyleSheet(btn_style)
        self.max_btn.clicked.connect(self.toggle_maximize_restore)

        close_btn = SvgIconButton("close", width=38, height=30, icon_px=15)
        close_btn.setStyleSheet(btn_style + "QPushButton:hover { background-color: #E81123; }")
        close_btn.clicked.connect(self.hide_and_trim)

        controls.addWidget(min_btn)
        controls.addWidget(self.max_btn)
        controls.addWidget(close_btn)
        layout.addLayout(controls)
        return header

    def _open_ignore_folders(self):
        self.content.open_ignore_dialog()

    def _update_count_label(self, count):
        self.count_label.setText(f"{count} project{'s' if count != 1 else ''}")

    def _on_project_launched(self, _path):
        self.hide_and_trim()

    def trim_memory(self):
        if sys.platform == "win32":
            try:
                ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            except Exception:
                pass

    def show_hub(self):
        self.engine.start_scan()
        self.content.render_projects()
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()
        self.content.focus_search()

    def toggle_hub(self):
        if self.isVisible() and not self.isMinimized() and self.isActiveWindow():
            self.hide_and_trim()
        else:
            self.show_hub()

    def hide_and_trim(self):
        self.hide()
        self.trim_memory()

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setIconName("maximize")
            self.background_frame.setStyleSheet(
                "#hubBackgroundFrame { background-color: #1c1c20; border: 1px solid #383842; border-radius: 14px; }"
            )
            self.header.setStyleSheet(
                "QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #005a9e); border-top-left-radius: 13px; border-top-right-radius: 13px; }"
            )
        else:
            self.showMaximized()
            self.max_btn.setIconName("restore")
            self.background_frame.setStyleSheet(
                "#hubBackgroundFrame { background-color: #1c1c20; border: none; border-radius: 0px; }"
            )
            self.header.setStyleSheet(
                "QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #005a9e); border-top-left-radius: 0px; border-top-right-radius: 0px; }"
            )

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_and_trim()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide_and_trim()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.header.underMouse():
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            if self.isMaximized():
                self.toggle_maximize_restore()
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_pos = QPoint()
        event.accept()


if __name__ == "__main__":
    from core.win_utils import enable_dpi_awareness
    enable_dpi_awareness()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    hub = VSCodeHubWindow()
    hub.show_hub()
    sys.exit(app.exec())
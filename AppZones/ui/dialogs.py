from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton

try:
    from core.win_utils import get_open_windows
except (ImportError, ValueError):
    from ..core.win_utils import get_open_windows

class AppSelectDialog(QDialog):
    """
    Modal dialog allowing users to pick an active window from all running Alt-Tab windows.
    """
    def __init__(self, parent=None, return_hwnd=False):
        super().__init__(parent)
        self.return_hwnd = return_hwnd
        self.selected_hwnd = None
        self.setWindowTitle("Select Open Application")
        self.setMinimumSize(440, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        lbl = QLabel("Choose a running application:")
        lbl.setObjectName("subtitle")
        layout.addWidget(lbl)

        self.list = QListWidget()
        self.window_items = get_open_windows()
        for title, hwnd in self.window_items:
            self.list.addItem(title)
        layout.addWidget(self.list)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_select = QPushButton("Select")
        btn_select.setObjectName("primary")
        btn_select.clicked.connect(self.on_select)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_select)
        layout.addLayout(btn_box)

    def on_select(self):
        idx = self.list.currentRow()
        if 0 <= idx < len(self.window_items):
            self.selected_hwnd = self.window_items[idx][1]
            self.accept()
        else:
            self.reject()

    def get_selected(self):
        if self.list.currentItem():
            return self.list.currentItem().text()
        return ""
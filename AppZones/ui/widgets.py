from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import Qt

class NoWheelComboBox(QComboBox):
    """
    QComboBox that ignores mouse wheel scroll events to prevent
    unintentional selection changes while scrolling.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()
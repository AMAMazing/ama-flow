import sys
import os

WINDOWZONES_DIR = os.path.dirname(os.path.abspath(__file__))
if WINDOWZONES_DIR not in sys.path:
    sys.path.insert(0, WINDOWZONES_DIR)

from core.win_utils import enable_dpi_awareness
enable_dpi_awareness()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
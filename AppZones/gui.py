import sys
import os
from PyQt6.QtWidgets import QApplication

# Ensure the AppZones directory is in sys.path so modules resolve cleanly
APPZONES_DIR = os.path.dirname(os.path.abspath(__file__))
if APPZONES_DIR not in sys.path:
    sys.path.insert(0, APPZONES_DIR)

from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
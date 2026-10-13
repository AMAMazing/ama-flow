import sys
import os

WINDOWZONES_DIR = os.path.dirname(os.path.abspath(__file__))
if WINDOWZONES_DIR not in sys.path:
    sys.path.insert(0, WINDOWZONES_DIR)

from daemon.service import run_daemon, apply_layout_statically

def main():
    run_daemon()

if __name__ == "__main__":
    main()
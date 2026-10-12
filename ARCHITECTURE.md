# AppZones Architecture & LLM Navigation Guide

This document maps the AppZones codebase to enable fast, targeted modifications without needing to read every file or write monolithic code.

---

## 1. System Overview

AppZones is a Windows desktop application that manages window tiling and Picture-in-Picture (PiP) layouts for multi-window productivity. It has two modes of operation:
1. **3-Window Layout (`3_window`)**: Splits the screen between Visual Studio Code, Google Chrome, and a media/aspect-ratio-constrained window.
2. **Corner Pinning / PiP (`corner`)**: Snaps a secondary media window into a specified corner of the active primary window.

Two entry points exist:
- **`AppZones/gui.py`**: PyQt6 GUI for configuring layouts, profiles, and snapping preferences.
- **`AppZones/main.py`**: Background daemon service monitoring active windows and enforcing layouts via Windows API hooks/hotkeys.
- **`AppZones/config.json`**: Single source of truth for persistent configuration.

---

## 2. Codebase Map & Module Responsibilities

### Root & Entry Points
| File | Responsibility | Key Classes / Functions |
| :--- | :--- | :--- |
| `AppZones/gui.py` | UI launch script; initializes PyQt6 Fusion application | `main()` |
| `AppZones/main.py` | Daemon launch script; starts layout enforcement service | `main()` |
| `AppZones/config.json` | Persistent user configuration (layout modes, dimensions, zone targets) | JSON schema |
| `AppZones/run.bat` | Batch launcher for daemon | - |
| `AppZones/run_gui.bat` | Batch launcher for GUI | - |

---

### `AppZones/core/` - Business Logic & Windows API
Pure Python and Win32 logic. Independent of UI components.

| File | Responsibility | Key Definitions |
| :--- | :--- | :--- |
| `core/config.py` | Loads and saves configuration JSON with default fallbacks | `load_config()`, `save_config()` |
| `core/layout_engine.py` | Pure geometric calculations: aspect ratios, rectangle coords, smart window detection | `parse_aspect_ratio()`, `detect_smart_media_window()`, `calculate_rects()`, `calculate_fullscreen_corner_rects()`, `calculate_smart_layout()` |
| `core/win_utils.py` | Windows Win32 API interactions via ctypes/win32gui: window enumeration, margins, dimension query, placement | `RECT`, `get_screen_resolution()`, `get_window_margins()`, `get_open_windows()`, `position_window()` |

---

### `AppZones/daemon/` - Background Service & Event Handling
Event loop and hotkey interceptors for real-time window management.

| File | Responsibility | Key Definitions |
| :--- | :--- | :--- |
| `daemon/service.py` | Daemon orchestrator; polls or triggers layout enforcement | `AppZonesDaemon`, `run_daemon()`, `apply_layout_statically()`, `get_active_zones_for_current_state()` |
| `daemon/hotkey.py` | Low-level native Windows hotkey event filter for PyQt | `HotkeyFilter(QAbstractNativeEventFilter)` |
| `daemon/overlay.py` | Visual snapping feedback overlay | `OverlayWidget(QWidget)` |

---

### `AppZones/ui/` - PyQt6 User Interface
Frontend controls and visual configuration panels.

| File | Responsibility | Key Definitions |
| :--- | :--- | :--- |
| `ui/main_window.py` | Primary window hosting mode tabs, status displays, and persistence hooks | `MainWindow(QMainWindow)` |
| `ui/three_window_panel.py` | Settings view for 3-Window split layout | `ThreeWindowPanel(QFrame)` |
| `ui/corner_panel.py` | Settings view for Corner PiP mode | `CornerPanel(QFrame)` |
| `ui/dialogs.py` | Modal windows (e.g., active window picker) | `AppSelectDialog(QDialog)` |
| `ui/overlay.py` | Interactive preview overlay for window bounds | `FullscreenPreviewOverlay(QWidget)` |
| `ui/widgets.py` | Custom UI components (e.g., wheel-immune dropdowns) | `NoWheelComboBox(QComboBox)` |
| `ui/styles.py` | Central QSS styles and color themes | Style constants and QSS strings |

---

## 3. Configuration Contract (`config.json`)

The configuration JSON adheres to the following structure:
```json
{
  "mode": "3_window", // or "corner"
  "layout_settings": {
    "vscode_side": "Right",
    "chrome_sizing": "432px",
    "active_media_profile": "MYAEW (3:2)",
    "chrome_sizes": { ... },
    "media_profiles": { ... }
  },
  "corner_settings": {
    "fullscreen_app": "Visual Studio Code",
    "media_app": "Picture in picture",
    "corner": "Bottom-Left",
    "max_width": 612,
    "max_height": 344,
    "active_media_profile": "16:9 (PiP)"
  },
  "zones": [
    {
      "window_title": "...",
      "role": "media" | "chrome" | "vscode",
      "pos": "Bottom-Left" | "Top-Left" | "Right",
      "stat": "...",
      "val": "...",
      "rect": { "x": 0, "y": 0, "width": 0, "height": 0 }
    }
  ]
}
```

---

## 4. "Where to Make Changes" Action Recipes

When asked to implement a feature or fix a bug, refer to this table to modify ONLY the required files:

| Task / Feature Request | Target File(s) | Notes |
| :--- | :--- | :--- |
| **Add a new layout calculation or aspect ratio rule** | `AppZones/core/layout_engine.py` | Modify or add calculation functions; ensure output dict matches `{x, y, width, height}` |
| **Change how windows are detected, filtered, or positioned** | `AppZones/core/win_utils.py` | Uses Win32 ctypes (`user32.dll`); verify DPI scaling & window margins |
| **Add a new config property or default option** | `AppZones/core/config.py` & `AppZones/config.json` | Update default fallback dict and JSON schema |
| **Update global hotkeys or snapping triggers** | `AppZones/daemon/hotkey.py` & `AppZones/daemon/service.py` | Manages native Windows message loop and hotkey registration |
| **Modify 3-Window configuration UI** | `AppZones/ui/three_window_panel.py` | Panel emits updates back to `MainWindow` |
| **Modify Corner PiP configuration UI** | `AppZones/ui/corner_panel.py` | Manages corner dropdowns, sizing sliders |
| **Update UI theme, button styling, or layout margins** | `AppZones/ui/styles.py` | Keep styling in QSS strings to avoid hardcoding colors across widgets |
| **Modify the visual preview / border highlights** | `AppZones/ui/overlay.py` (GUI) or `AppZones/daemon/overlay.py` (Daemon) | Semi-transparent framing widgets |

---

## 5. Development Guidelines for LLMs

1. **Keep Modules Focused**: Do NOT re-merge modular code back into single files. Each module should remain under 300-400 lines.
2. **Path Resolution**: Both `main.py` and `gui.py` prepend `APPZONES_DIR` to `sys.path`. Keep imports relative to `AppZones` root (e.g., `from core.config import load_config`).
3. **No Win32 API calls in UI**: The UI classes should delegate window math to `core/layout_engine.py` and window inspection to `core/win_utils.py`.
4. **Preserve Configuration Integrity**: When saving config, use `core.config.save_config()` to avoid race conditions or corrupted JSON.

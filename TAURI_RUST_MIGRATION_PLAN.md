# AppZones: Phased Architecture Plan (Python Prototyping to Tauri & Rust)

## 1. Executive Summary & Core Philosophy

Developing desktop window-management tools, tiling managers, and system hooks directly in native systems languages from day one typically leads to slow iteration cycles, complex Win32 FFI debugging, and high architectural friction.

The recommended engineering strategy is a **3-phase progressive transition**:
1. **Phase 1: Rapid Prototyping & Logic Validation in Python** (Current)
2. **Phase 2: Hybrid Bridge (Tauri v2 Frontend + Python Daemon)**
3. **Phase 3: Pure Native Rust Core (Standalone Single-Binary Production Release)**

This approach guarantees that layout math, UX paradigms, and Windows edge cases (multi-DPI, virtual desktops, fullscreen apps) are 100% solved before committing them to strict Rust memory models.

---

## 2. Phase Breakdown

### Phase 1: Python Engine & Win32 Logic Validation (Current Stage)
* **Objective:** Validate layout calculations, window positioning ergonomics, and user workflows with minimal development friction.
* **Key Components:**
  * **Layout Engine (`AppZones/core/layout_engine.py`):** Pure mathematical models for tiling, grid subdivisions, gutters, padding, and screen bounding box constraints.
  * **Win32 Event Hooks:** Testing low-level window hooks via `ctypes` / `pywin32` (`SetWinEventHook`, `EVENT_SYSTEM_MOVESIZEEND`, `WH_SHELL`).
  * **Multi-Monitor & DPI:** Handling display resolution changes (`EnumDisplayMonitors`, `GetMonitorInfoW`, per-monitor DPI awareness).
  * **Snapping UX:** Perfecting mouse snap-zone triggers, keyboard shortcuts, and overlay preview behavior.
* **Success Criteria:** A feature-complete desktop tool where all behavioral edge cases and UI snapping interactions feel seamless and reliable.

---

### Phase 2: Hybrid Architecture (Tauri v2 UI + Python Daemon)
* **Objective:** Decouple the user interface from Python GUI frameworks (Tkinter/PyQt) in favor of a modern, lightweight web frontend powered by Tauri, while retaining the validated Python engine.
* **Architecture Overview:**
```
+-----------------------------------------------------------+
|                        Tauri v2                           |
|  - Modern Webview Frontend (Svelte / Vue / React)         |
|  - Native Windows System Tray (No Terminal Window)         |
|  - Global Hotkey Manager & Overlay Canvas                 |
+-----------------------------+-----------------------------+
                              |
                              | Local IPC (WebSocket / Named Pipe)
                              v
+-----------------------------------------------------------+
|                   Python Background Daemon                |
|  - Layout Math & Preset State                             |
|  - Low-level Win32 Window Snapping & Positioning          |
|  - App Assignment Rules & Config Persistence              |
+-----------------------------------------------------------+
```
* **Key Advantages:**
  * **System Tray & Zero Console Window:** Tauri natively manages the background process lifecycle, sitting in the Windows notification tray with instant right-click menus.
  * **Modern Reactive Interface:** Sleek zone-editor, visual layout customizer, and customizable glass/acrylic overlay styling using CSS/Tailwind.
  * **Rapid UI Hot-Reloading:** UI tweaks happen in milliseconds using web dev tools without restarting the Win32 hooks.
* **IPC Bridge Implementation:**
  * Fast local JSON-RPC over localhost WebSocket or Windows Named Pipes (`\\.\pipe\appzones_ipc`).

---

### Phase 3: Pure Native Rust Core (Standalone Single-Binary Production Release)
* **Objective:** Eliminate the Python runtime and interpreter overhead completely. Deliver a self-contained ~12 MB executable with near-zero resource consumption.
* **Component Migration Map:**

| Python Component | Rust Equivalent | Crate / Technology |
| :--- | :--- | :--- |
| `layout_engine.py` | Geometric calculation module | Pure Rust struct & algorithms |
| `ctypes` Win32 calls | Native Win32 API calls | `windows-rs` / `windows-sys` |
| `config.json` parser | Type-safe serde models | `serde`, `serde_json` |
| Window Event Listener | WinEvent Hook / Shell Hook | `SetWinEventHook` in background thread |
| Hotkey Manager | System-wide global hotkeys | Tauri global-shortcut / `RegisterHotKey` |

* **Production Performance Profile:**
  * **Idle RAM Usage:** Reduced from ~45-70 MB (Python) to **8-15 MB** (Rust + WebView2).
  * **Cold Startup Time:** Reduced from ~1.5s to **<150ms**.
  * **Installer Size:** Compact single installer (~10-15 MB) without bundled Python DLLs or virtual environments.
  * **Distribution:** Clean code signing, Windows Store compatibility, and seamless auto-updater via Tauri Updater.

---

## 3. Step-by-Step Implementation Roadmap

1. **Milestone 1 (Python):** Complete and polish `layout_engine.py`, multi-monitor detection, and configuration saving in the existing Python codebase.
2. **Milestone 2 (Python IPC):** Expose a lightweight local JSON-RPC / WebSocket interface on the Python side to receive layout commands and dispatch window states.
3. **Milestone 3 (Tauri Scaffolding):** Initialize a Tauri v2 application with system tray support and a settings/overlay window.
4. **Milestone 4 (Hybrid Verification):** Wire Tauri frontend commands to the Python IPC daemon and verify smooth snapping and tray operation.
5. **Milestone 5 (Rust Layout Port):** Rewrite `layout_engine.py` in Rust within Tauri's backend `src-tauri/src/`.
6. **Milestone 6 (Rust Win32 Port):** Replace the Python daemon entirely with `windows-rs` hooks inside the Tauri Rust core.
7. **Milestone 7 (Release):** Package final production installer with MSIS/NSIS bundling and automated updater.

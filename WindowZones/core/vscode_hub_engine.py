import os
import re
import sys
import json
import subprocess
from urllib.parse import unquote
from PyQt6.QtCore import QObject, QThread, pyqtSignal

try:
    from .config import APP_DIR, VSCODE_HUB_CACHE_PATH, VSCODE_HUB_CONFIG_PATH
except (ImportError, ValueError):
    from core.config import APP_DIR, VSCODE_HUB_CACHE_PATH, VSCODE_HUB_CONFIG_PATH


COMMON_ICON_NAMES = ("favicon.ico", "icon.ico", "logo.ico", "app.ico")


def find_project_icon(project_path):
    """
    Matches VSCode-Hub icon discovery: checks common .ico filenames first,
    then falls back to the first .ico within the first 50 directory entries.
    """
    if not project_path or not os.path.isdir(project_path):
        return None
    try:
        for name in COMMON_ICON_NAMES:
            candidate = os.path.join(project_path, name)
            if os.path.exists(candidate):
                return candidate
        files = os.listdir(project_path)
        for item in files[:50]:
            if item.lower().endswith(".ico"):
                return os.path.join(project_path, item)
    except Exception:
        pass
    return None


def find_vscode_executable(cached_path=None):
    if cached_path and os.path.exists(cached_path):
        return cached_path

    appdata_path = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "")
    possible_paths = [
        os.path.join(appdata_path, "Programs", "Microsoft VS Code", "Code.exe"),
        os.path.join(appdata_path, "Programs", "Microsoft VS Code", "bin", "code.cmd"),
        os.path.join(program_files, "Microsoft VS Code", "Code.exe"),
        os.path.join(program_files, "Microsoft VS Code", "bin", "code.cmd"),
    ]
    if program_files_x86:
        possible_paths.append(os.path.join(program_files_x86, "Microsoft VS Code", "Code.exe"))

    for path in possible_paths:
        if path and os.path.exists(path):
            return path

    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(["where", "code"], capture_output=True, text=True, creationflags=flags)
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line and os.path.exists(line):
                return line
    except Exception:
        pass
    return None


def extract_vscode_project_name(window_title):
    """
    Extracts the folder/workspace name from a VS Code window title.
    Examples:
      'main.py - WindowZones - Visual Studio Code' -> 'WindowZones'
      'WindowZones - Visual Studio Code' -> 'WindowZones'
      'WindowZones (Workspace) - Visual Studio Code' -> 'WindowZones'
      'main.py - WindowZones [WSL: Ubuntu] - Visual Studio Code' -> 'WindowZones'
      'Visual Studio Code' -> 'Visual Studio Code'
    """
    if not window_title:
        return "VS Code"
    clean = window_title.strip()
    suffixes = (
        " - Visual Studio Code - Insiders",
        " - Visual Studio Code",
        " - VSCodium",
    )
    for suf in suffixes:
        if clean.lower().endswith(suf.lower()):
            clean = clean[: -len(suf)].strip()
            break

    if not clean:
        return "Visual Studio Code"

    parts = [p.strip() for p in clean.split(" - ") if p.strip()]
    if not parts:
        return "Visual Studio Code"

    # Strip trailing [Administrator] or similar bracketed suffixes if separated
    while len(parts) > 1 and parts[-1].startswith("[") and parts[-1].endswith("]"):
        parts.pop()

    workspace = parts[-1]
    workspace = re.sub(r"\s*\(Workspace\)\s*$", "", workspace, flags=re.IGNORECASE)
    workspace = re.sub(r"\s*\[[^\]]+\]\s*$", "", workspace)
    workspace = workspace.lstrip("●• ").strip()
    return workspace or "Visual Studio Code"


def _uri_to_local_path(uri):
    if not uri or not isinstance(uri, str):
        return None
    if not uri.startswith("file:///"):
        return None
    raw = unquote(uri[8:])
    if sys.platform == "win32":
        raw = raw.replace("/", "\\")
        if len(raw) >= 2 and raw[1] == ":":
            raw = raw[0].upper() + raw[1:]
    return os.path.normpath(raw)


class ProjectScannerWorker(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, ignored_folders, cached_vscode_path=None):
        super().__init__()
        self.ignored_folders = {os.path.normcase(os.path.normpath(p)) for p in (ignored_folders or []) if p}
        self.cached_vscode_path = cached_vscode_path

    def _collect_uris_from_storage(self, storage_data):
        uris = []
        # Primary source used by VSCode-Hub
        profile_ws = storage_data.get("profileAssociations", {}).get("workspaces", {})
        if isinstance(profile_ws, dict):
            uris.extend(profile_ws.keys())

        # Supplemental recent entries in VS Code storage.json
        opened = storage_data.get("openedPathsList", {})
        if isinstance(opened, dict):
            for entry in opened.get("entries", []):
                if isinstance(entry, dict):
                    folder_uri = entry.get("folderUri")
                    if folder_uri:
                        uris.append(folder_uri)
            for ws in opened.get("workspaces3", []):
                if isinstance(ws, str):
                    uris.append(ws)
                elif isinstance(ws, dict) and ws.get("folderUri"):
                    uris.append(ws["folderUri"])
        return uris

    def run(self):
        vscode_path = find_vscode_executable(self.cached_vscode_path)
        try:
            appdata = os.environ.get("APPDATA", "")
            possible_paths = [
                os.path.join(appdata, "Code", "User", "globalStorage", "storage.json"),
                os.path.join(appdata, "Code - Insiders", "User", "globalStorage", "storage.json"),
                os.path.join(appdata, "VSCodium", "User", "globalStorage", "storage.json"),
            ]
            storage_path = next((p for p in possible_paths if os.path.exists(p)), None)
            if not storage_path:
                self.finished.emit([], vscode_path or "")
                return

            with open(storage_path, "r", encoding="utf-8") as f:
                storage_data = json.load(f)

            project_uris = self._collect_uris_from_storage(storage_data)
            seen_norm = set()
            final_projects = []

            for uri in project_uris:
                path = _uri_to_local_path(uri)
                if not path:
                    continue
                norm_key = os.path.normcase(path)
                if norm_key in seen_norm or norm_key in self.ignored_folders:
                    continue
                seen_norm.add(norm_key)

                if os.path.isdir(path):
                    try:
                        mtime = os.path.getmtime(path)
                    except Exception:
                        mtime = 0
                    icon = find_project_icon(path)
                    final_projects.append({
                        "path": path,
                        "name": os.path.basename(path) or path,
                        "mtime": mtime,
                        "icon": icon,
                    })

            final_projects.sort(key=lambda x: x["mtime"], reverse=True)

            try:
                with open(VSCODE_HUB_CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(final_projects, f, indent=2)
            except Exception:
                pass

            self.finished.emit(final_projects, vscode_path or "")
        except Exception:
            self.finished.emit([], vscode_path or "")


class VSCodeHubEngine(QObject):
    """
    Shared VS Code Hub backend powering both the standalone Hub window
    and the VS Code tab bar (+ dropdown and tab project icons).
    """
    projects_updated = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.projects = []
        self.all_discovered_paths = []
        self.ignored_folders = []
        self.vscode_exe = None
        self._scanner = None
        self._by_name_lower = {}
        self._load_hub_config()
        self._load_cache()

    def _load_hub_config(self):
        if os.path.exists(VSCODE_HUB_CONFIG_PATH):
            try:
                with open(VSCODE_HUB_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.vscode_exe = data.get("vscode_path")
                self.ignored_folders = list(data.get("ignored_folders", []))
                return
            except Exception:
                pass

        # One-time migration from legacy VSCode-Hub folder if present
        legacy_dir = os.path.join(APP_DIR, "VSCode-Hub")
        legacy_cfg = os.path.join(legacy_dir, "launcher_config.json")
        legacy_ign = os.path.join(legacy_dir, "ignored_folders.json")
        if os.path.exists(legacy_cfg):
            try:
                with open(legacy_cfg, "r", encoding="utf-8") as f:
                    self.vscode_exe = json.load(f).get("vscode_path")
            except Exception:
                pass
        if os.path.exists(legacy_ign):
            try:
                with open(legacy_ign, "r", encoding="utf-8") as f:
                    ign = json.load(f)
                    if isinstance(ign, list):
                        self.ignored_folders = ign
            except Exception:
                pass

    def _save_hub_config(self):
        try:
            with open(VSCODE_HUB_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "vscode_path": self.vscode_exe,
                        "ignored_folders": self.ignored_folders,
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass

    def _rebuild_index(self):
        idx = {}
        for p in self.projects:
            name = (p.get("name") or "").strip().lower()
            if name and name not in idx:
                idx[name] = p
        self._by_name_lower = idx

    def _load_cache(self):
        cache_path = VSCODE_HUB_CACHE_PATH
        if not os.path.exists(cache_path):
            legacy_cache = os.path.join(APP_DIR, "VSCode-Hub", "project_cache.json")
            if os.path.exists(legacy_cache):
                cache_path = legacy_cache
            else:
                return
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                ign = {os.path.normcase(os.path.normpath(p)) for p in self.ignored_folders if p}
                self.projects = [
                    p for p in data
                    if isinstance(p, dict) and p.get("path")
                    and os.path.normcase(os.path.normpath(p["path"])) not in ign
                ]
                self._rebuild_index()
        except Exception:
            pass

    def start_scan(self):
        if self._scanner is not None and self._scanner.isRunning():
            return
        self._scanner = ProjectScannerWorker(self.ignored_folders, self.vscode_exe)
        self._scanner.finished.connect(self._on_scan_finished)
        self._scanner.start()

    def _on_scan_finished(self, projects, vscode_path):
        if vscode_path and vscode_path != self.vscode_exe:
            self.vscode_exe = vscode_path
            self._save_hub_config()
        self.projects = projects
        self._rebuild_index()
        self.projects_updated.emit(self.projects)

    def get_projects(self):
        return list(self.projects)

    def get_ignored_folders(self):
        return list(self.ignored_folders)

    def set_ignored_folders(self, paths):
        self.ignored_folders = [os.path.normpath(p) for p in paths if p]
        self._save_hub_config()
        self.start_scan()

    def get_all_known_paths_for_ignore_dialog(self):
        seen = set()
        result = []
        for p in [proj["path"] for proj in self.projects] + list(self.ignored_folders):
            norm = os.path.normcase(os.path.normpath(p))
            if norm not in seen and os.path.isdir(p):
                seen.add(norm)
                result.append(os.path.normpath(p))
        return result

    def get_project_for_window_title(self, window_title):
        proj_name = extract_vscode_project_name(window_title)
        key = proj_name.lower()
        proj = self._by_name_lower.get(key)
        if proj:
            return proj_name, proj, proj.get("icon")
        # Try matching any segment in window title against known project names
        for seg in reversed([s.strip() for s in (window_title or "").split(" - ") if s.strip()]):
            seg_clean = re.sub(r"\s*\(Workspace\)\s*$", "", seg, flags=re.IGNORECASE)
            seg_clean = re.sub(r"\s*\[[^\]]+\]\s*$", "", seg_clean).lstrip("●• ").strip().lower()
            if seg_clean in self._by_name_lower:
                matched = self._by_name_lower[seg_clean]
                return matched.get("name", proj_name), matched, matched.get("icon")
        return proj_name, None, None

    def open_project(self, path, force_new_window=False):
        if not self.vscode_exe or not os.path.exists(self.vscode_exe):
            self.vscode_exe = find_vscode_executable()
            if self.vscode_exe:
                self._save_hub_config()
        if not self.vscode_exe:
            return False, "Could not find VS Code executable (Code.exe)."
        try:
            cmd = [self.vscode_exe, "-n", path] if force_new_window else [self.vscode_exe, path]
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.Popen(cmd, creationflags=flags)
            return True, ""
        except Exception as e:
            return False, str(e)


_ENGINE_SINGLETON = None


def get_hub_engine():
    global _ENGINE_SINGLETON
    if _ENGINE_SINGLETON is None:
        _ENGINE_SINGLETON = VSCodeHubEngine()
    return _ENGINE_SINGLETON
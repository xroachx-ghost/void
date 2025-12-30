"""
Application launcher utilities.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .utils import SafeSubprocess


@dataclass(frozen=True)
class LauncherEntry:
    name: str
    args: List[str]
    terminal: bool


def _default_entries() -> List[LauncherEntry]:
    return [
        LauncherEntry(name="Void Suite", args=["--gui"], terminal=False),
        LauncherEntry(name="Void Suite (CLI)", args=[], terminal=True),
    ]


def install_start_menu(app_name: str = "Void Suite") -> Dict[str, List[str]]:
    entries = _default_entries()
    system = platform.system()
    if system == "Windows":
        return _install_windows(app_name, entries)
    if system == "Linux":
        return _install_linux(entries)
    if system == "Darwin":
        return _install_darwin(entries)
    return {"created": [], "removed": [], "errors": [f"Unsupported platform: {system}"]}


def uninstall_start_menu(app_name: str = "Void Suite") -> Dict[str, List[str]]:
    entries = _default_entries()
    system = platform.system()
    if system == "Windows":
        return _uninstall_windows(app_name, entries)
    if system == "Linux":
        return _uninstall_linux(entries)
    if system == "Darwin":
        return _uninstall_darwin(entries)
    return {"created": [], "removed": [], "errors": [f"Unsupported platform: {system}"]}


def launcher_status(app_name: str = "Void Suite") -> Dict[str, List[str]]:
    entries = _default_entries()
    system = platform.system()
    if system == "Windows":
        return _status_windows(app_name, entries)
    if system == "Linux":
        return _status_linux(entries)
    if system == "Darwin":
        return _status_darwin(entries)
    return {"present": [], "missing": [], "errors": [f"Unsupported platform: {system}"]}


def _windows_start_menu_dir(app_name: str) -> Path:
    base = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return base / app_name


def _windows_python_executable(gui: bool) -> str:
    python_path = Path(sys.executable)
    if gui and python_path.name.lower().startswith("python"):
        candidate = python_path.with_name("pythonw.exe")
        if candidate.exists():
            return str(candidate)
    return str(python_path)


def _escape_powershell(value: str) -> str:
    return value.replace("'", "''")


def _install_windows(app_name: str, entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    created: List[str] = []
    errors: List[str] = []
    start_menu_dir = _windows_start_menu_dir(app_name)
    start_menu_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        shortcut_path = start_menu_dir / f"{entry.name}.lnk"
        args = ["-m", "void", *entry.args]
        python_exe = _windows_python_executable(gui=not entry.terminal)
        script = (
            "$shell = New-Object -ComObject WScript.Shell;"
            f"$shortcut = $shell.CreateShortcut('{_escape_powershell(str(shortcut_path))}');"
            f"$shortcut.TargetPath = '{_escape_powershell(python_exe)}';"
            f"$shortcut.Arguments = '{_escape_powershell(' '.join(args))}';"
            f"$shortcut.WorkingDirectory = '{_escape_powershell(str(Path.cwd()))}';"
            "$shortcut.Save();"
        )
        code, _, stderr = SafeSubprocess.run(["powershell", "-NoProfile", "-Command", script])
        if code == 0:
            created.append(str(shortcut_path))
        else:
            errors.append(stderr.strip() or f"Failed to create {shortcut_path}")
    return {"created": created, "removed": [], "errors": errors}


def _uninstall_windows(app_name: str, entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    removed: List[str] = []
    errors: List[str] = []
    start_menu_dir = _windows_start_menu_dir(app_name)
    for entry in entries:
        shortcut_path = start_menu_dir / f"{entry.name}.lnk"
        if shortcut_path.exists():
            try:
                shortcut_path.unlink()
                removed.append(str(shortcut_path))
            except OSError as exc:
                errors.append(str(exc))
    if start_menu_dir.exists() and not any(start_menu_dir.iterdir()):
        start_menu_dir.rmdir()
    return {"created": [], "removed": removed, "errors": errors}


def _status_windows(app_name: str, entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    present: List[str] = []
    missing: List[str] = []
    errors: List[str] = []
    start_menu_dir = _windows_start_menu_dir(app_name)
    for entry in entries:
        shortcut_path = start_menu_dir / f"{entry.name}.lnk"
        if shortcut_path.exists():
            present.append(str(shortcut_path))
        else:
            missing.append(str(shortcut_path))
    return {"present": present, "missing": missing, "errors": errors}


def _linux_apps_dir() -> Path:
    return Path.home() / ".local" / "share" / "applications"


def _linux_desktop_path(entry: LauncherEntry) -> Path:
    normalized = entry.name.lower().replace(" ", "-")
    return _linux_apps_dir() / f"{normalized}.desktop"


def _install_linux(entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    created: List[str] = []
    errors: List[str] = []
    apps_dir = _linux_apps_dir()
    apps_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        path = _linux_desktop_path(entry)
        exec_args = " ".join(["void", *entry.args])
        terminal = "true" if entry.terminal else "false"
        content = "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={entry.name}",
                f"Exec={exec_args}",
                f"Terminal={terminal}",
                "Categories=Utility;",
            ]
        )
        try:
            path.write_text(content, encoding="utf-8")
            created.append(str(path))
        except OSError as exc:
            errors.append(str(exc))
    return {"created": created, "removed": [], "errors": errors}


def _uninstall_linux(entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    removed: List[str] = []
    errors: List[str] = []
    for entry in entries:
        path = _linux_desktop_path(entry)
        if path.exists():
            try:
                path.unlink()
                removed.append(str(path))
            except OSError as exc:
                errors.append(str(exc))
    return {"created": [], "removed": removed, "errors": errors}


def _status_linux(entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    present: List[str] = []
    missing: List[str] = []
    errors: List[str] = []
    for entry in entries:
        path = _linux_desktop_path(entry)
        if path.exists():
            present.append(str(path))
        else:
            missing.append(str(path))
    return {"present": present, "missing": missing, "errors": errors}


def _darwin_apps_dir() -> Path:
    return Path.home() / "Applications"


def _darwin_command_path(entry: LauncherEntry) -> Path:
    normalized = entry.name.replace("/", "-")
    return _darwin_apps_dir() / f"{normalized}.command"


def _install_darwin(entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    created: List[str] = []
    errors: List[str] = []
    apps_dir = _darwin_apps_dir()
    apps_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        path = _darwin_command_path(entry)
        args = " ".join(entry.args)
        content = "\n".join(
            [
                "#!/bin/bash",
                f'cd "{Path.cwd()}"',
                f'void {args}'.strip(),
            ]
        )
        try:
            path.write_text(content, encoding="utf-8")
            path.chmod(0o755)
            created.append(str(path))
        except OSError as exc:
            errors.append(str(exc))
    return {"created": created, "removed": [], "errors": errors}


def _uninstall_darwin(entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    removed: List[str] = []
    errors: List[str] = []
    for entry in entries:
        path = _darwin_command_path(entry)
        if path.exists():
            try:
                path.unlink()
                removed.append(str(path))
            except OSError as exc:
                errors.append(str(exc))
    return {"created": [], "removed": removed, "errors": errors}


def _status_darwin(entries: List[LauncherEntry]) -> Dict[str, List[str]]:
    present: List[str] = []
    missing: List[str] = []
    errors: List[str] = []
    for entry in entries:
        path = _darwin_command_path(entry)
        if path.exists():
            present.append(str(path))
        else:
            missing.append(str(path))
    return {"present": present, "missing": missing, "errors": errors}

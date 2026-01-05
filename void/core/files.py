"""
File management for Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..config import Config
from .utils import SafeSubprocess


class FileManager:
    """Device file management"""

    @staticmethod
    def list_files(device_id: str, path: str = "/sdcard") -> List[Dict]:
        """List files in directory"""
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "ls", "-la", path])

        files = []
        if code == 0:
            for line in stdout.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 8:
                    files.append(
                        {
                            "permissions": parts[0],
                            "size": parts[4],
                            "date": f"{parts[5]} {parts[6]}",
                            "name": " ".join(parts[7:]),
                        }
                    )

        return files

    @staticmethod
    def pull_file(device_id: str, remote_path: str, local_path: Path = None) -> Dict:
        """Pull file from device"""
        if local_path is None:
            filename = Path(remote_path).name
            local_path = Config.EXPORTS_DIR / filename

        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "pull", remote_path, str(local_path)]
        )

        if code == 0 and local_path.exists():
            return {"success": True, "path": str(local_path), "size": local_path.stat().st_size}

        return {"success": False}

    @staticmethod
    def push_file(device_id: str, local_path: Path, remote_path: str) -> bool:
        """Push file to device"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "push", str(local_path), remote_path]
        )
        return code == 0

    @staticmethod
    def delete_file(device_id: str, path: str) -> bool:
        """Delete file on device"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "rm", "-f", path])
        return code == 0

    @staticmethod
    def create_folder(device_id: str, path: str) -> bool:
        """Create directory on device"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "mkdir", "-p", path])
        return code == 0

    @staticmethod
    def rename_file(device_id: str, old_path: str, new_path: str) -> bool:
        """Rename file or folder on device"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "mv", old_path, new_path])
        return code == 0

    @staticmethod
    def copy_file(device_id: str, source: str, dest: str) -> bool:
        """Copy file on device"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "cp", "-r", source, dest])
        return code == 0

    @staticmethod
    def move_file(device_id: str, source: str, dest: str) -> bool:
        """Move file on device (same as rename)"""
        return FileManager.rename_file(device_id, source, dest)

    @staticmethod
    def get_file_permissions(device_id: str, path: str) -> Dict:
        """Get file permissions"""
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "ls", "-l", path])

        if code == 0 and stdout:
            parts = stdout.strip().split()
            if parts:
                return {
                    "permissions": parts[0],
                    "owner": parts[2] if len(parts) > 2 else "",
                    "group": parts[3] if len(parts) > 3 else "",
                    "size": parts[4] if len(parts) > 4 else "",
                }

        return {}

    @staticmethod
    def set_file_permissions(device_id: str, path: str, mode: str) -> bool:
        """Set file permissions (chmod)

        Args:
            device_id: Device identifier
            path: File path on device
            mode: Permission mode (e.g., '755', '644')
        """
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "chmod", mode, path])
        return code == 0

    @staticmethod
    def search_files(device_id: str, path: str, pattern: str) -> List[str]:
        """Search for files by name pattern

        Args:
            device_id: Device identifier
            path: Directory to search in
            pattern: File name pattern (e.g., '*.jpg', 'log*')

        Returns:
            List of matching file paths
        """
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "find", path, "-name", pattern]
        )

        if code == 0 and stdout:
            return [line.strip() for line in stdout.strip().split("\n") if line.strip()]

        return []

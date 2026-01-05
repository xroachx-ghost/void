"""
App management for Android devices.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from typing import Any, Dict, List

from ..config import Config
from .utils import SafeSubprocess


class AppManager:
    """Application management"""

    @staticmethod
    def disable_app(device_id: str, package: str) -> bool:
        """Disable application"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "disable-user", "--user", "0", package]
        )
        return code == 0

    @staticmethod
    def enable_app(device_id: str, package: str) -> bool:
        """Enable application"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "pm", "enable", package])
        return code == 0

    @staticmethod
    def clear_app_data(device_id: str, package: str) -> bool:
        """Clear app data"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "pm", "clear", package])
        return code == 0

    @staticmethod
    def uninstall_app(device_id: str, package: str) -> bool:
        """Uninstall app"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "uninstall", package])
        return code == 0

    @staticmethod
    def backup_app(device_id: str, package: str) -> Dict[str, Any]:
        """Backup app APK"""
        # Get APK path
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "path", package]
        )

        if code == 0 and stdout:
            apk_path = stdout.replace("package:", "").strip()

            # Pull APK
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Config.BACKUP_DIR / f"{package}_{timestamp}.apk"

            code, _, _ = SafeSubprocess.run(
                ["adb", "-s", device_id, "pull", apk_path, str(output_path)]
            )

            if code == 0 and output_path.exists():
                return {
                    "success": True,
                    "path": str(output_path),
                    "size": output_path.stat().st_size,
                }

        return {"success": False}

    @staticmethod
    def list_apps(device_id: str, filter_type: str = "all") -> List[Dict]:
        """List installed apps"""
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "list", "packages"]
        )

        apps = []
        if code == 0:
            for line in stdout.strip().split("\n"):
                if line.startswith("package:"):
                    package = line.replace("package:", "").strip()

                    # Get app info
                    app_info = AppManager._get_app_info(device_id, package)

                    if filter_type == "system" and app_info.get("system"):
                        apps.append(app_info)
                    elif filter_type == "user" and not app_info.get("system"):
                        apps.append(app_info)
                    elif filter_type == "all":
                        apps.append(app_info)

        return apps

    @staticmethod
    def _get_app_info(device_id: str, package: str) -> Dict:
        """Get app information"""
        info = {"package": package}

        # Check if system app
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "path", package]
        )
        if code == 0:
            info["system"] = "/system/" in stdout

        # Get version
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "package", package]
        )
        if code == 0:
            for line in stdout.split("\n"):
                if "versionName=" in line:
                    info["version"] = line.split("versionName=")[1].split()[0]
                    break

        return info

    @staticmethod
    def install_apk(device_id: str, apk_path: str) -> bool:
        """Install APK file to device"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "install", "-r", apk_path])
        return code == 0

    @staticmethod
    def force_stop_app(device_id: str, package: str) -> bool:
        """Force stop running application"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "am", "force-stop", package]
        )
        return code == 0

    @staticmethod
    def grant_permission(device_id: str, package: str, permission: str) -> bool:
        """Grant permission to app"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "grant", package, permission]
        )
        return code == 0

    @staticmethod
    def revoke_permission(device_id: str, package: str, permission: str) -> bool:
        """Revoke permission from app"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "revoke", package, permission]
        )
        return code == 0

    @staticmethod
    def launch_app(device_id: str, package: str) -> bool:
        """Launch application by package name"""
        code, _, _ = SafeSubprocess.run(
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "monkey",
                "-p",
                package,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ]
        )
        return code == 0

    @staticmethod
    def get_app_info_detailed(device_id: str, package: str) -> Dict[str, Any]:
        """Get detailed app information including version, size, install date, permissions"""
        info = {"package": package}

        # Get package info with dumpsys
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "package", package]
        )

        if code == 0:
            lines = stdout.split("\n")
            for i, line in enumerate(lines):
                if "versionName=" in line:
                    info["version_name"] = line.split("versionName=")[1].split()[0]
                elif "versionCode=" in line:
                    parts = line.split("versionCode=")
                    if len(parts) > 1:
                        info["version_code"] = parts[1].split()[0]
                elif "firstInstallTime=" in line:
                    info["install_date"] = line.split("firstInstallTime=")[1].strip()
                elif "lastUpdateTime=" in line:
                    info["update_date"] = line.split("lastUpdateTime=")[1].strip()
                elif "targetSdk=" in line:
                    info["target_sdk"] = line.split("targetSdk=")[1].split()[0]

        # Get APK path and size
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "path", package]
        )
        if code == 0:
            apk_path = stdout.replace("package:", "").strip()
            info["apk_path"] = apk_path
            info["system"] = "/system/" in apk_path

            # Get size
            code, stdout, _ = SafeSubprocess.run(
                ["adb", "-s", device_id, "shell", "du", "-h", apk_path]
            )
            if code == 0:
                info["size"] = stdout.split()[0]

        # Get permissions
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "package", package]
        )
        if code == 0:
            permissions = []
            in_permissions = False
            for line in stdout.split("\n"):
                if "requested permissions:" in line.lower():
                    in_permissions = True
                elif in_permissions:
                    if line.strip().startswith("android.permission."):
                        perm = line.strip().split(":")[0]
                        permissions.append(perm)
                    elif not line.strip() or "install permissions" in line.lower():
                        break
            info["permissions"] = permissions

        return info

    @staticmethod
    def export_app_list(device_id: str, format: str = "csv") -> Dict[str, Any]:
        """Export installed apps to CSV or JSON

        Args:
            device_id: Device identifier
            format: 'csv' or 'json'

        Returns:
            Dict with success status and file path
        """
        apps = AppManager.list_apps(device_id, "all")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "csv":
            output_path = Config.BACKUP_DIR / f"apps_{timestamp}.csv"
            try:
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    if apps:
                        writer = csv.DictWriter(f, fieldnames=apps[0].keys())
                        writer.writeheader()
                        writer.writerows(apps)
                return {"success": True, "path": str(output_path), "count": len(apps)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        elif format == "json":
            output_path = Config.BACKUP_DIR / f"apps_{timestamp}.json"
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(apps, f, indent=2)
                return {"success": True, "path": str(output_path), "count": len(apps)}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Invalid format"}

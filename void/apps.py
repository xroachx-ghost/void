"""Application management."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .config import Config
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
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "pm", "path", package])

        if code == 0 and stdout:
            apk_path = stdout.replace("package:", "").strip()

            # Pull APK
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Config.BACKUP_DIR / f"{{package}}_{timestamp}.apk"

            code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "pull", apk_path, str(output_path)])

            if code == 0 and output_path.exists():
                return {"success": True, "path": str(output_path), "size": output_path.stat().st_size}

        return {"success": False}

    @staticmethod
    def list_apps(device_id: str, filter_type: str = "all") -> List[Dict]:
        """List installed apps"""
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "pm", "list", "packages"])

        apps: List[Dict[str, Any]] = []
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
        info: Dict[str, Any] = {"package": package}

        # Check if system app
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "pm", "path", package])
        if code == 0:
            info["system"] = "/system/" in stdout

        # Get version
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "dumpsys", "package", package])
        if code == 0:
            for line in stdout.split("\n"):
                if "versionName=" in line:
                    info["version"] = line.split("versionName=")[1].split()[0]
                    break

        return info

from __future__ import annotations

from pathlib import Path
from typing import Dict

from ..config import Config
from .device import DeviceDetector
from .utils import SafeSubprocess


class RecoveryWorkflow:
    """Safe recovery and restore workflows."""

    @staticmethod
    def reboot_to_recovery(device_id: str) -> Dict[str, str | bool]:
        """Reboot a device into recovery mode."""
        if not DeviceDetector._check_adb_ready(device_id):
            return {"success": False, "message": "Device not reachable over ADB."}
        code, _, stderr = SafeSubprocess.run(
            ["adb", "-s", device_id, "reboot", "recovery"],
            timeout=Config.TIMEOUT_MEDIUM,
        )
        if code == 0:
            return {"success": True, "message": "Rebooting to recovery."}
        return {"success": False, "message": stderr.strip() or "Failed to reboot to recovery."}

    @staticmethod
    def reboot_to_bootloader(device_id: str) -> Dict[str, str | bool]:
        """Reboot a device into bootloader mode."""
        if not DeviceDetector._check_adb_ready(device_id):
            return {"success": False, "message": "Device not reachable over ADB."}
        code, _, stderr = SafeSubprocess.run(
            ["adb", "-s", device_id, "reboot", "bootloader"],
            timeout=Config.TIMEOUT_MEDIUM,
        )
        if code == 0:
            return {"success": True, "message": "Rebooting to bootloader."}
        return {
            "success": False,
            "message": stderr.strip() or "Failed to reboot to bootloader.",
        }

    @staticmethod
    def reboot_to_system(device_id: str) -> Dict[str, str | bool]:
        """Reboot a device back to system UI."""
        if not DeviceDetector._check_adb_ready(device_id):
            return {"success": False, "message": "Device not reachable over ADB."}
        code, _, stderr = SafeSubprocess.run(
            ["adb", "-s", device_id, "reboot"],
            timeout=Config.TIMEOUT_MEDIUM,
        )
        if code == 0:
            return {"success": True, "message": "Rebooting device."}
        return {"success": False, "message": stderr.strip() or "Failed to reboot."}

    @staticmethod
    def sideload_update(device_id: str, package_path: Path) -> Dict[str, str | bool]:
        """Sideload an update package after ensuring recovery mode."""
        if not package_path.exists():
            return {"success": False, "message": "Update package not found."}
        reboot_result = RecoveryWorkflow.reboot_to_recovery(device_id)
        if not reboot_result.get("success"):
            return reboot_result
        code, _, stderr = SafeSubprocess.run(
            ["adb", "-s", device_id, "sideload", str(package_path)],
            timeout=Config.TIMEOUT_LONG,
        )
        if code == 0:
            return {"success": True, "message": "Sideload complete."}
        return {"success": False, "message": stderr.strip() or "Sideload failed."}

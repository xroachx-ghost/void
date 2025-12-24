"""Device detection."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from .database import db
from .utils import SafeSubprocess


class DeviceDetector:
    """Comprehensive device detection"""

    @staticmethod
    def detect_all() -> List[Dict[str, Any]]:
        """Detect all devices"""
        devices: List[Dict[str, Any]] = []
        devices.extend(DeviceDetector._detect_adb())
        devices.extend(DeviceDetector._detect_fastboot())

        # Update database
        for device in devices:
            db.update_device(device)

        return devices

    @staticmethod
    def _detect_adb() -> List[Dict[str, Any]]:
        """Detect ADB devices"""
        devices: List[Dict[str, Any]] = []
        try:
            code, stdout, _ = SafeSubprocess.run(["adb", "devices"])
            if code == 0:
                for line in stdout.strip().split("\n")[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            device_id = parts[0]
                            status = parts[1]

                            if status == "device":
                                info = DeviceDetector._get_adb_info(device_id)
                                devices.append({"id": device_id, "mode": "adb", "status": status, **info})
        except Exception:
            pass
        return devices

    @staticmethod
    def _get_adb_info(device_id: str) -> Dict[str, str]:
        """Get comprehensive device info"""
        info: Dict[str, str] = {}

        props = {
            "manufacturer": "ro.product.manufacturer",
            "model": "ro.product.model",
            "brand": "ro.product.brand",
            "device": "ro.product.device",
            "android_version": "ro.build.version.release",
            "sdk_version": "ro.build.version.sdk",
            "build_id": "ro.build.id",
            "security_patch": "ro.build.version.security_patch",
            "chipset": "ro.board.platform",
            "hardware": "ro.hardware",
            "serial": "ro.serialno",
            "bootloader": "ro.bootloader",
            "fingerprint": "ro.build.fingerprint",
        }

        for key, prop in props.items():
            try:
                code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "getprop", prop])
                if code == 0 and stdout.strip():
                    info[key] = stdout.strip()
            except Exception:
                pass

        # Get IMEI
        try:
            code, stdout, _ = SafeSubprocess.run(
                ["adb", "-s", device_id, "shell", "service", "call", "iphonesubinfo", "1"]
            )
            if code == 0:
                imei = "".join(c for c in stdout if c.isdigit())[:15]
                if len(imei) == 15:
                    info["imei"] = imei
        except Exception:
            pass

        # Battery info
        info["battery"] = DeviceDetector._get_battery_info(device_id)

        # Storage info
        info["storage"] = DeviceDetector._get_storage_info(device_id)

        # Screen info
        info["screen"] = DeviceDetector._get_screen_info(device_id)

        return info

    @staticmethod
    def _get_battery_info(device_id: str) -> Dict:
        """Get battery information"""
        try:
            code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "dumpsys", "battery"])
            if code == 0:
                battery: Dict[str, str] = {}
                for line in stdout.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower().replace(" ", "_")
                        battery[key] = value.strip()
                return battery
        except Exception:
            pass
        return {}

    @staticmethod
    def _get_storage_info(device_id: str) -> Dict:
        """Get storage information"""
        try:
            code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "df", "/data"])
            if code == 0:
                lines = stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        return {"total": parts[1], "used": parts[2], "available": parts[3]}
        except Exception:
            pass
        return {}

    @staticmethod
    def _get_screen_info(device_id: str) -> Dict:
        """Get screen information"""
        try:
            code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "wm", "size"])
            if code == 0:
                match = re.search(r"(\d+)x(\d+)", stdout)
                if match:
                    return {"width": match.group(1), "height": match.group(2)}
        except Exception:
            pass
        return {}

    @staticmethod
    def _detect_fastboot() -> List[Dict[str, Any]]:
        """Detect fastboot devices"""
        devices: List[Dict[str, Any]] = []
        try:
            code, stdout, _ = SafeSubprocess.run(["fastboot", "devices"])
            if code == 0:
                for line in stdout.strip().split("\n"):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            devices.append({"id": parts[0], "mode": "fastboot", "status": parts[1]})
        except Exception:
            pass
        return devices

"""System tweaks."""
from __future__ import annotations

from .utils import SafeSubprocess


class SystemTweaker:
    """System tweaks and optimizations"""

    @staticmethod
    def set_dpi(device_id: str, dpi: int) -> bool:
        """Change screen DPI"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "wm", "density", str(dpi)])
        return code == 0

    @staticmethod
    def set_animation_scale(device_id: str, scale: float) -> bool:
        """Set animation scale"""
        settings = [
            ("window_animation_scale", scale),
            ("transition_animation_scale", scale),
            ("animator_duration_scale", scale),
        ]

        success = True
        for setting, value in settings:
            code, _, _ = SafeSubprocess.run(
                ["adb", "-s", device_id, "shell", "settings", "put", "global", setting, str(value)]
            )
            success = success and (code == 0)

        return success

    @staticmethod
    def enable_developer_options(device_id: str) -> bool:
        """Enable developer options"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "put", "global", "development_settings_enabled", "1"]
        )
        return code == 0

    @staticmethod
    def enable_usb_debugging(device_id: str) -> bool:
        """Enable USB debugging"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "settings", "put", "global", "adb_enabled", "1"])
        return code == 0

    @staticmethod
    def set_screen_timeout(device_id: str, seconds: int) -> bool:
        """Set screen timeout"""
        ms = seconds * 1000
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "put", "system", "screen_off_timeout", str(ms)]
        )
        return code == 0

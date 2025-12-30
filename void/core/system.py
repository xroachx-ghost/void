"""
System-level utilities and tweaks.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .utils import SafeSubprocess


class SystemTweaker:
    """System tweaks and optimizations"""

    @staticmethod
    def set_dpi(device_id: str, dpi: int) -> bool:
        """Change screen DPI"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'wm', 'density', str(dpi)])
        return code == 0

    @staticmethod
    def set_animation_scale(device_id: str, scale: float) -> bool:
        """Set animation scale"""
        settings = [
            ('window_animation_scale', scale),
            ('transition_animation_scale', scale),
            ('animator_duration_scale', scale),
        ]

        success = True
        for setting, value in settings:
            code, _, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', setting, str(value)]
            )
            success = success and (code == 0)

        return success

    @staticmethod
    def enable_developer_options(device_id: str) -> bool:
        """Enable developer options"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'development_settings_enabled', '1']
        )
        return code == 0

    @staticmethod
    def enable_usb_debugging(device_id: str) -> bool:
        """Enable USB debugging"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'adb_enabled', '1']
        )
        return code == 0

    @staticmethod
    def force_usb_debugging(device_id: str) -> dict:
        """Attempt to force-enable USB debugging for engineering firmware."""
        steps = []

        def run_step(step: str, cmd: list[str]) -> bool:
            code, stdout, stderr = SafeSubprocess.run(cmd)
            detail = (stderr or stdout or "").strip()
            steps.append(
                {
                    "step": step,
                    "success": code == 0,
                    "detail": detail if detail else None,
                }
            )
            return code == 0

        run_step(
            "enable_developer_options",
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'development_settings_enabled', '1'],
        )
        run_step(
            "enable_usb_debugging_setting",
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'adb_enabled', '1'],
        )
        run_step(
            "set_usb_config",
            ['adb', '-s', device_id, 'shell', 'setprop', 'persist.sys.usb.config', 'mtp,adb'],
        )
        run_step(
            "set_adb_service",
            ['adb', '-s', device_id, 'shell', 'setprop', 'persist.service.adb.enable', '1'],
        )
        run_step("restart_adbd_stop", ['adb', '-s', device_id, 'shell', 'stop', 'adbd'])
        run_step("restart_adbd_start", ['adb', '-s', device_id, 'shell', 'start', 'adbd'])

        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'get', 'global', 'adb_enabled']
        )
        adb_enabled = code == 0 and stdout.strip() == "1"

        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'getprop', 'persist.sys.usb.config']
        )
        usb_config = stdout.strip() if code == 0 and stdout.strip() else None

        return {
            "success": adb_enabled or any(step["success"] for step in steps),
            "adb_enabled": adb_enabled,
            "usb_config": usb_config,
            "steps": steps,
        }

    @staticmethod
    def set_screen_timeout(device_id: str, seconds: int) -> bool:
        """Set screen timeout"""
        ms = seconds * 1000
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'system', 'screen_off_timeout', str(ms)]
        )
        return code == 0

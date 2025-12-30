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

    @staticmethod
    def reboot(device_id: str, mode: str = 'system') -> bool:
        """Reboot device to specified mode
        
        Args:
            device_id: Device identifier
            mode: One of 'system', 'recovery', 'bootloader', 'edl', 'safe'
            
        Returns:
            bool: True if command succeeded
        """
        mode_map = {
            'system': [],
            'recovery': ['recovery'],
            'bootloader': ['bootloader'],
            'edl': ['edl'],
            'safe': ['safe-mode']
        }
        
        args = ['adb', '-s', device_id, 'reboot'] + mode_map.get(mode, [])
        code, _, _ = SafeSubprocess.run(args)
        return code == 0

    @staticmethod
    def shutdown(device_id: str) -> bool:
        """Shutdown device"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'reboot', '-p'])
        return code == 0

    @staticmethod
    def get_adb_tcpip_status(device_id: str) -> dict:
        """Get ADB over TCP/IP status"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'getprop', 'service.adb.tcp.port'])
        port = stdout.strip() if code == 0 else ''
        
        # Get device IP
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'ip', 'addr', 'show', 'wlan0'])
        ip = ''
        if code == 0:
            for line in stdout.split('\n'):
                if 'inet ' in line:
                    ip = line.strip().split()[1].split('/')[0]
                    break
        
        return {
            'enabled': port and port != '-1' and port != '',
            'port': port if port and port != '-1' else None,
            'ip': ip if ip else None
        }

    @staticmethod
    def enable_adb_tcpip(device_id: str, port: int = 5555) -> bool:
        """Enable ADB over TCP/IP"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'tcpip', str(port)])
        return code == 0

    @staticmethod
    def disable_adb_tcpip(device_id: str) -> bool:
        """Disable ADB over TCP/IP (return to USB)"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'usb'])
        return code == 0

    @staticmethod
    def set_font_scale(device_id: str, scale: float) -> bool:
        """Change system font scale"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'system', 'font_scale', str(scale)]
        )
        return code == 0

    @staticmethod
    def toggle_battery_saver(device_id: str, enable: bool) -> bool:
        """Toggle battery saver mode"""
        value = '1' if enable else '0'
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'low_power', value]
        )
        return code == 0

    @staticmethod
    def toggle_stay_awake(device_id: str, enable: bool) -> bool:
        """Toggle stay awake while charging"""
        value = '7' if enable else '0'  # Bit flags: USB=2, AC=4, Wireless=1
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'stay_on_while_plugged_in', value]
        )
        return code == 0

    @staticmethod
    def get_oem_unlock_status(device_id: str) -> dict:
        """Check OEM unlock status"""
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'get', 'global', 'oem_unlock_enabled']
        )
        enabled = code == 0 and stdout.strip() == '1'
        
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'getprop', 'sys.oem_unlock_allowed']
        )
        allowed = code == 0 and stdout.strip() == '1'
        
        return {
            'enabled': enabled,
            'allowed': allowed
        }

    @staticmethod
    def get_encryption_status(device_id: str) -> dict:
        """Check device encryption status"""
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'getprop', 'ro.crypto.state']
        )
        state = stdout.strip() if code == 0 else ''
        
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'getprop', 'ro.crypto.type']
        )
        crypto_type = stdout.strip() if code == 0 else ''
        
        return {
            'encrypted': state == 'encrypted',
            'state': state,
            'type': crypto_type
        }

    @staticmethod
    def start_screen_recording(device_id: str, output_path: str, time_limit: int = 180) -> bool:
        """Start screen recording
        
        Args:
            device_id: Device identifier
            output_path: Output path on device (e.g., '/sdcard/screenrecord.mp4')
            time_limit: Recording time limit in seconds (max 180)
        """
        time_limit = min(time_limit, 180)  # Android limit
        code, _, _ = SafeSubprocess.run([
            'adb', '-s', device_id, 'shell', 'screenrecord', 
            '--time-limit', str(time_limit), output_path
        ])
        return code == 0

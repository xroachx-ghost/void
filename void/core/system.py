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
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "wm", "density", str(dpi)]
        )
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
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "settings",
                "put",
                "global",
                "development_settings_enabled",
                "1",
            ]
        )
        return code == 0

    @staticmethod
    def enable_usb_debugging(device_id: str) -> bool:
        """Enable USB debugging"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "put", "global", "adb_enabled", "1"]
        )
        return code == 0

    @staticmethod
    def force_usb_debugging(device_id: str, method: str = "all") -> dict:
        """
        Attempt to force-enable USB debugging using comprehensive methods.

        Args:
            device_id: Device identifier
            method: Specific method to use or 'all' for all methods
                   Options: 'all', 'standard', 'properties', 'settings_db',
                           'build_prop', 'adb_keys', 'recovery', 'root'

        Returns:
            dict: Results with success status, enabled status, and step details
        """
        steps = []

        def run_step(step: str, cmd: list[str], category: str = "standard") -> bool:
            code, stdout, stderr = SafeSubprocess.run(cmd)
            detail = (stderr or stdout or "").strip()
            steps.append(
                {
                    "step": step,
                    "category": category,
                    "success": code == 0,
                    "detail": detail if detail else None,
                }
            )
            return code == 0

        # Method 1: Standard Settings Commands
        if method in ["all", "standard"]:
            run_step(
                "enable_developer_options",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "settings",
                    "put",
                    "global",
                    "development_settings_enabled",
                    "1",
                ],
                "standard",
            )
            run_step(
                "enable_usb_debugging_setting",
                ["adb", "-s", device_id, "shell", "settings", "put", "global", "adb_enabled", "1"],
                "standard",
            )
            run_step(
                "stay_awake_while_charging",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "settings",
                    "put",
                    "global",
                    "stay_on_while_plugged_in",
                    "7",
                ],
                "standard",
            )

        # Method 2: System Properties
        if method in ["all", "properties"]:
            run_step(
                "set_usb_config_mtp_adb",
                ["adb", "-s", device_id, "shell", "setprop", "persist.sys.usb.config", "mtp,adb"],
                "properties",
            )
            run_step(
                "set_adb_service_enable",
                ["adb", "-s", device_id, "shell", "setprop", "persist.service.adb.enable", "1"],
                "properties",
            )
            run_step(
                "set_adb_debuggable",
                ["adb", "-s", device_id, "shell", "setprop", "persist.service.debuggable", "1"],
                "properties",
            )
            run_step(
                "set_sys_adb_enable",
                ["adb", "-s", device_id, "shell", "setprop", "sys.usb.config", "adb"],
                "properties",
            )
            run_step(
                "set_adb_tcp_port",
                ["adb", "-s", device_id, "shell", "setprop", "service.adb.tcp.port", "5555"],
                "properties",
            )

        # Method 3: ADB Daemon Control
        if method in ["all", "standard", "properties"]:
            run_step(
                "restart_adbd_stop", ["adb", "-s", device_id, "shell", "stop", "adbd"], "daemon"
            )
            run_step(
                "restart_adbd_start", ["adb", "-s", device_id, "shell", "start", "adbd"], "daemon"
            )

        # Method 4: Settings Database (SQLite) - Requires root or special permissions
        if method in ["all", "settings_db", "root"]:
            run_step(
                "sqlite_update_adb_enabled",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "su",
                    "-c",
                    "sqlite3 /data/data/com.android.providers.settings/databases/settings.db \"UPDATE global SET value=1 WHERE name='adb_enabled'\"",
                ],
                "settings_db",
            )
            run_step(
                "sqlite_update_development_enabled",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "su",
                    "-c",
                    "sqlite3 /data/data/com.android.providers.settings/databases/settings.db \"UPDATE global SET value=1 WHERE name='development_settings_enabled'\"",
                ],
                "settings_db",
            )

        # Method 5: Build.prop Modification - Requires root and remount
        if method in ["all", "build_prop", "root"]:
            run_step(
                "remount_system_rw",
                ["adb", "-s", device_id, "shell", "su", "-c", "mount -o remount,rw /system"],
                "build_prop",
            )
            # Add properties to build.prop
            run_step(
                "add_persist_adb_enable_to_buildprop",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "su",
                    "-c",
                    'echo "persist.service.adb.enable=1" >> /system/build.prop',
                ],
                "build_prop",
            )
            run_step(
                "add_persist_debuggable_to_buildprop",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "su",
                    "-c",
                    'echo "persist.service.debuggable=1" >> /system/build.prop',
                ],
                "build_prop",
            )
            run_step(
                "add_persist_usb_config_to_buildprop",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "su",
                    "-c",
                    'echo "persist.sys.usb.config=mtp,adb" >> /system/build.prop',
                ],
                "build_prop",
            )
            run_step(
                "remount_system_ro",
                ["adb", "-s", device_id, "shell", "su", "-c", "mount -o remount,ro /system"],
                "build_prop",
            )

        # Method 6: ADB Keys Authentication Bypass - Requires root
        if method in ["all", "adb_keys", "root"]:
            # Note: This would require the host's adbkey.pub, which we can't automatically provide
            run_step(
                "check_adb_keys",
                ["adb", "-s", device_id, "shell", "su", "-c", "ls -la /data/misc/adb/adb_keys"],
                "adb_keys",
            )
            run_step(
                "set_adb_keys_permissions",
                ["adb", "-s", device_id, "shell", "su", "-c", "chmod 644 /data/misc/adb/adb_keys"],
                "adb_keys",
            )

        # Method 7: Alternative USB Configurations
        if method in ["all", "properties"]:
            run_step(
                "set_usb_config_adb_only",
                ["adb", "-s", device_id, "shell", "setprop", "sys.usb.config", "adb"],
                "alternative",
            )
            run_step(
                "set_usb_config_mass_storage_adb",
                [
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "setprop",
                    "persist.sys.usb.config",
                    "mass_storage,adb",
                ],
                "alternative",
            )
            run_step(
                "set_usb_config_rndis_adb",
                ["adb", "-s", device_id, "shell", "setprop", "persist.sys.usb.config", "rndis,adb"],
                "alternative",
            )

        # Verification
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "get", "global", "adb_enabled"]
        )
        adb_enabled = code == 0 and stdout.strip() == "1"

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "persist.sys.usb.config"]
        )
        usb_config = stdout.strip() if code == 0 and stdout.strip() else None

        # Check if running as root
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "su", "-c", "id"])
        has_root = code == 0 and "uid=0" in stdout

        return {
            "success": adb_enabled or any(step["success"] for step in steps),
            "adb_enabled": adb_enabled,
            "usb_config": usb_config,
            "has_root": has_root,
            "steps": steps,
            "methods_attempted": method,
            "total_steps": len(steps),
            "successful_steps": sum(1 for s in steps if s["success"]),
        }

    @staticmethod
    def get_usb_debugging_methods() -> dict:
        """
        Get comprehensive information about all USB debugging force-enable methods.

        Returns:
            dict: Detailed information about each method with requirements and risks
        """
        return {
            "methods": [
                {
                    "id": "standard",
                    "name": "Standard Settings Commands",
                    "description": "Enable USB debugging via Android settings database commands",
                    "requirements": ["ADB already enabled (partial)", "Device unlocked"],
                    "risk_level": "Low",
                    "success_rate": "High (if ADB connected)",
                    "steps": [
                        "Enable developer options",
                        "Enable USB debugging setting",
                        "Configure stay awake while charging",
                    ],
                },
                {
                    "id": "properties",
                    "name": "System Properties Modification",
                    "description": "Modify persist.sys.usb.config and related properties",
                    "requirements": ["ADB access", "Some devices require root"],
                    "risk_level": "Low-Medium",
                    "success_rate": "Medium-High",
                    "steps": [
                        "Set persist.sys.usb.config to mtp,adb",
                        "Enable ADB service properties",
                        "Set debuggable properties",
                        "Restart ADB daemon",
                    ],
                },
                {
                    "id": "settings_db",
                    "name": "Settings Database (SQLite) Manipulation",
                    "description": "Directly modify settings.db to enable USB debugging",
                    "requirements": ["Root access (su)", "ADB access"],
                    "risk_level": "Medium",
                    "success_rate": "High (if rooted)",
                    "steps": [
                        "Execute SQLite UPDATE on settings database",
                        "Set adb_enabled=1 in global settings",
                        "Set development_settings_enabled=1",
                    ],
                },
                {
                    "id": "build_prop",
                    "name": "Build.prop File Modification",
                    "description": "Add USB debugging properties to /system/build.prop",
                    "requirements": [
                        "Root access",
                        "System remount capability",
                        "Bootloader unlocked (usually)",
                    ],
                    "risk_level": "Medium-High",
                    "success_rate": "High (if rooted + system writable)",
                    "steps": [
                        "Remount /system as read-write",
                        "Append persist.service.adb.enable=1",
                        "Append persist.service.debuggable=1",
                        "Append persist.sys.usb.config=mtp,adb",
                        "Remount /system as read-only",
                        "Reboot device",
                    ],
                },
                {
                    "id": "adb_keys",
                    "name": "ADB Keys Authentication Bypass",
                    "description": "Add PC's public key to device's authorized keys",
                    "requirements": ["Root access", "PC's adbkey.pub file", "ADB access"],
                    "risk_level": "Medium",
                    "success_rate": "High (if rooted)",
                    "steps": [
                        "Obtain PC's ~/.android/adbkey.pub",
                        "Append to /data/misc/adb/adb_keys on device",
                        "Set proper permissions (644)",
                        "Restart ADB daemon",
                    ],
                },
                {
                    "id": "recovery",
                    "name": "Recovery Mode (TWRP/Custom Recovery)",
                    "description": "Enable USB debugging from custom recovery environment",
                    "requirements": [
                        "Custom recovery (TWRP)",
                        "Bootloader unlocked",
                        "ADB in recovery",
                    ],
                    "risk_level": "Medium-High",
                    "success_rate": "Medium (device dependent)",
                    "steps": [
                        "Boot into TWRP/custom recovery",
                        "Mount system and data partitions",
                        "Edit build.prop or settings.db",
                        "Add adbkey.pub to adb_keys",
                        "Reboot to system",
                    ],
                    "notes": "Changes may revert on some ROMs after reboot",
                },
                {
                    "id": "otg_adapter",
                    "name": "OTG Adapter with Mouse/Keyboard",
                    "description": "Use physical input device to manually enable USB debugging",
                    "requirements": [
                        "OTG adapter",
                        "USB mouse or keyboard",
                        "Broken screen but display works",
                        "Device unlocked",
                    ],
                    "risk_level": "None",
                    "success_rate": "Very High (if conditions met)",
                    "steps": [
                        "Connect USB mouse via OTG adapter",
                        "Navigate to Settings > About Phone",
                        "Tap Build Number 7 times",
                        "Go to Developer Options",
                        "Enable USB Debugging",
                        "Authorize PC when prompted",
                    ],
                    "notes": "Best method for broken touchscreens",
                },
                {
                    "id": "fastboot",
                    "name": "Fastboot/Bootloader Commands",
                    "description": "Enable debugging via fastboot mode (device specific)",
                    "requirements": [
                        "Fastboot mode access",
                        "Bootloader unlocked",
                        "OEM specific support",
                    ],
                    "risk_level": "Low-Medium",
                    "success_rate": "Low (rarely supported)",
                    "steps": [
                        "Boot to fastboot/bootloader mode",
                        "Check fastboot getvar all for debug options",
                        "Use OEM-specific fastboot commands",
                        "Flash custom recovery for better access",
                    ],
                    "notes": "Very device/OEM specific, not universal",
                },
                {
                    "id": "magisk",
                    "name": "Magisk Module (ADB Root Enabler)",
                    "description": "Install Magisk module to enable unauthenticated ADB root",
                    "requirements": [
                        "Magisk installed",
                        "Root access",
                        "Custom recovery or Magisk app",
                    ],
                    "risk_level": "Medium",
                    "success_rate": "Very High (if Magisk present)",
                    "steps": [
                        "Download Adb-Root-Enabler Magisk module",
                        "Install via Magisk Manager or recovery",
                        "Reboot device",
                        "ADB root access without authorization",
                    ],
                    "notes": "Security risk - removes ADB authentication",
                },
            ],
            "recommendations": {
                "broken_screen": "otg_adapter > recovery > adb_keys",
                "rooted_device": "settings_db > properties > build_prop",
                "locked_device": "otg_adapter (only option without unlock)",
                "bootloop": "recovery > fastboot",
                "engineering_firmware": "standard > properties",
                "custom_rom": "magisk > build_prop > settings_db",
            },
            "warnings": [
                "Most methods require root access or unlocked bootloader",
                "Modifying system files can brick device if done incorrectly",
                "Enabling unauthenticated ADB is a serious security risk",
                "Always backup before making system changes",
                "Some changes may not persist after reboot on newer Android versions",
                "SELinux may prevent some modifications even with root",
                "Factory reset may be required if system becomes unstable",
            ],
        }

    @staticmethod
    def set_screen_timeout(device_id: str, seconds: int) -> bool:
        """Set screen timeout"""
        ms = seconds * 1000
        code, _, _ = SafeSubprocess.run(
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "settings",
                "put",
                "system",
                "screen_off_timeout",
                str(ms),
            ]
        )
        return code == 0

    @staticmethod
    def reboot(device_id: str, mode: str = "system") -> bool:
        """Reboot device to specified mode

        Args:
            device_id: Device identifier
            mode: One of 'system', 'recovery', 'bootloader', 'edl', 'safe'

        Returns:
            bool: True if command succeeded
        """
        mode_map = {
            "system": [],
            "recovery": ["recovery"],
            "bootloader": ["bootloader"],
            "edl": ["edl"],
            "safe": ["safe-mode"],
        }

        args = ["adb", "-s", device_id, "reboot"] + mode_map.get(mode, [])
        code, _, _ = SafeSubprocess.run(args)
        return code == 0

    @staticmethod
    def shutdown(device_id: str) -> bool:
        """Shutdown device"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "reboot", "-p"])
        return code == 0

    @staticmethod
    def get_adb_tcpip_status(device_id: str) -> dict:
        """Get ADB over TCP/IP status"""
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "service.adb.tcp.port"]
        )
        port = stdout.strip() if code == 0 else ""

        # Get device IP
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "ip", "addr", "show", "wlan0"]
        )
        ip = ""
        if code == 0:
            for line in stdout.split("\n"):
                if "inet " in line:
                    ip = line.strip().split()[1].split("/")[0]
                    break

        return {
            "enabled": port and port != "-1" and port != "",
            "port": port if port and port != "-1" else None,
            "ip": ip if ip else None,
        }

    @staticmethod
    def enable_adb_tcpip(device_id: str, port: int = 5555) -> bool:
        """Enable ADB over TCP/IP"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "tcpip", str(port)])
        return code == 0

    @staticmethod
    def disable_adb_tcpip(device_id: str) -> bool:
        """Disable ADB over TCP/IP (return to USB)"""
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "usb"])
        return code == 0

    @staticmethod
    def set_font_scale(device_id: str, scale: float) -> bool:
        """Change system font scale"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "put", "system", "font_scale", str(scale)]
        )
        return code == 0

    @staticmethod
    def toggle_battery_saver(device_id: str, enable: bool) -> bool:
        """Toggle battery saver mode"""
        value = "1" if enable else "0"
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "put", "global", "low_power", value]
        )
        return code == 0

    @staticmethod
    def toggle_stay_awake(device_id: str, enable: bool) -> bool:
        """Toggle stay awake while charging"""
        value = "7" if enable else "0"  # Bit flags: USB=2, AC=4, Wireless=1
        code, _, _ = SafeSubprocess.run(
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "settings",
                "put",
                "global",
                "stay_on_while_plugged_in",
                value,
            ]
        )
        return code == 0

    @staticmethod
    def get_oem_unlock_status(device_id: str) -> dict:
        """Check OEM unlock status"""
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "get", "global", "oem_unlock_enabled"]
        )
        enabled = code == 0 and stdout.strip() == "1"

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "sys.oem_unlock_allowed"]
        )
        allowed = code == 0 and stdout.strip() == "1"

        return {"enabled": enabled, "allowed": allowed}

    @staticmethod
    def get_encryption_status(device_id: str) -> dict:
        """Check device encryption status"""
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "ro.crypto.state"]
        )
        state = stdout.strip() if code == 0 else ""

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "ro.crypto.type"]
        )
        crypto_type = stdout.strip() if code == 0 else ""

        return {"encrypted": state == "encrypted", "state": state, "type": crypto_type}

    @staticmethod
    def start_screen_recording(device_id: str, output_path: str, time_limit: int = 180) -> bool:
        """Start screen recording

        Args:
            device_id: Device identifier
            output_path: Output path on device (e.g., '/sdcard/screenrecord.mp4')
            time_limit: Recording time limit in seconds (max 180)
        """
        time_limit = min(time_limit, 180)  # Android limit
        code, _, _ = SafeSubprocess.run(
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "screenrecord",
                "--time-limit",
                str(time_limit),
                output_path,
            ]
        )
        return code == 0

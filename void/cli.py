"""
VOID CLI

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import csv
import difflib
import json
import platform
import shutil
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import getpass
from typing import Any, Dict, List, Optional

from .config import Config
from .core.apps import AppManager
from .core.backup import AutoBackup
from .core.data_recovery import DataRecovery
from .core.database import db
from .core.device import DeviceDetector
from .core.display import DisplayAnalyzer
from .core.edl import edl_dump, edl_flash
from .core.edl_toolkit import (
    ToolkitResult,
    backup_partition,
    capture_edl_log,
    compatibility_matrix,
    convert_sparse_image,
    delete_profile,
    detect_edl_devices,
    device_notes,
    edl_unbrick_plan,
    extract_boot_image,
    flash_recovery,
    list_firehose_programmers,
    list_partitions_via_adb,
    load_profiles,
    pull_magisk_patched,
    read_partition_table,
    reboot_device,
    restore_partition,
    rollback_flash,
    safety_check,
    save_profile,
    stage_magisk_patch,
    verify_hash,
    verify_root,
    verify_twrp_image,
)
from .core.files import FileManager
from .core.frp import FRPEngine
from .core.launcher import install_start_menu, launcher_status, uninstall_start_menu
from .core.logcat import LogcatViewer
from .core.monitor import PSUTIL_AVAILABLE, monitor
from .core.network import NetworkTools
from .core.performance import PerformanceAnalyzer
from .core.report import ReportGenerator
from .core.screen import ScreenCapture
from .core.smart import SmartAdvisor
from .core.system import SystemTweaker
from .core.tools import (
    check_android_tools,
    check_mediatek_tools,
    check_qualcomm_tools,
    install_android_platform_tools,
)
from .core.utils import SafeSubprocess
from .logging import get_logger, log_edl_event
from .core.chipsets.dispatcher import detect_chipset_for_device, enter_chipset_mode
from .plugins import PluginContext, discover_plugins, get_registry

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass(frozen=True)
class CommandInfo:
    name: str
    summary: str
    usage: str
    category: str
    examples: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)


class CLI:
    """Enhanced CLI with all features."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.engine = FRPEngine()
        self.logcat = LogcatViewer()
        self.last_device_id: Optional[str] = None
        self.logger = get_logger(__name__)
        discover_plugins()
        self.plugin_registry = get_registry()
        self.command_catalog = self._build_command_catalog()
        self.command_aliases = self._build_command_aliases()

        # Start monitoring
        monitor.start()

    def run(self) -> None:
        """Run CLI."""
        self._print_banner()
        self._smart_startup()

        while True:
            try:
                cmd = input("\nvoid> ").strip()
                if not cmd:
                    continue
                if len(cmd) > Config.MAX_INPUT_LENGTH:
                    self.logger.warning(
                        f"Command too long (max {Config.MAX_INPUT_LENGTH} characters)",
                        extra={"category": "cli", "device_id": "-", "method": "-"},
                    )
                    continue

                parts = cmd.split()
                command = parts[0].lower()
                args = parts[1:]

                # Route commands
                commands = {
                    'devices': self._cmd_devices,
                    'info': lambda: self._cmd_info(args),
                    'summary': self._cmd_summary,
                    'backup': lambda: self._cmd_backup(args),
                    'screenshot': lambda: self._cmd_screenshot(args),
                    'apps': lambda: self._cmd_apps(args),
                    'files': lambda: self._cmd_files(args),
                    'analyze': lambda: self._cmd_analyze(args),
                    'display-diagnostics': lambda: self._cmd_display_diagnostics(args),
                    'recover': lambda: self._cmd_recover(args),
                    'tweak': lambda: self._cmd_tweak(args),
                    'usb-debug': lambda: self._cmd_usb_debug(args),
                    'report': lambda: self._cmd_report(args),
                    'stats': self._cmd_stats,
                    'monitor': self._cmd_monitor,
                    'logcat': lambda: self._cmd_logcat(args),
                    'execute': lambda: self._cmd_execute(args),
                    'menu': self._cmd_menu,
                    'version': self._cmd_version,
                    'paths': self._cmd_paths,
                    'netcheck': self._cmd_netcheck,
                    'adb': self._cmd_adb,
                    'edl-status': lambda: self._cmd_edl_status(args),
                    'edl-enter': lambda: self._cmd_edl_enter(args),
                    'edl-flash': lambda: self._cmd_edl_flash(args),
                    'edl-dump': lambda: self._cmd_edl_dump(args),
                    'edl-detect': self._cmd_edl_detect,
                    'edl-programmers': self._cmd_edl_programmers,
                    'edl-partitions': lambda: self._cmd_edl_partitions(args),
                    'edl-backup': lambda: self._cmd_edl_backup(args),
                    'edl-restore': lambda: self._cmd_edl_restore(args),
                    'edl-sparse': lambda: self._cmd_edl_sparse(args),
                    'edl-profile': lambda: self._cmd_edl_profile(args),
                    'edl-verify': lambda: self._cmd_edl_verify(args),
                    'edl-unbrick': lambda: self._cmd_edl_unbrick(args),
                    'edl-notes': lambda: self._cmd_edl_notes(args),
                    'edl-reboot': lambda: self._cmd_edl_reboot(args),
                    'edl-log': self._cmd_edl_log,
                    'boot-extract': lambda: self._cmd_boot_extract(args),
                    'magisk-patch': lambda: self._cmd_magisk_patch(args),
                    'magisk-pull': lambda: self._cmd_magisk_pull(args),
                    'twrp-verify': lambda: self._cmd_twrp_verify(args),
                    'twrp-flash': lambda: self._cmd_twrp_flash(args),
                    'root-verify': lambda: self._cmd_root_verify(args),
                    'safety-check': lambda: self._cmd_safety_check(args),
                    'rollback': lambda: self._cmd_rollback(args),
                    'compat-matrix': self._cmd_compat_matrix,
                    'testpoint-guide': lambda: self._cmd_testpoint_guide(args),
                    'clear-cache': self._cmd_clear_cache,
                    'doctor': self._cmd_doctor,
                    'logs': self._cmd_logs,
                    'backups': self._cmd_backups,
                    'reports': self._cmd_reports,
                    'exports': self._cmd_exports,
                    'devices-json': self._cmd_devices_json,
                    'stats-json': self._cmd_stats_json,
                    'logtail': lambda: self._cmd_logtail(args),
                    'cleanup-exports': self._cmd_cleanup_exports,
                    'cleanup-backups': self._cmd_cleanup_backups,
                    'cleanup-reports': self._cmd_cleanup_reports,
                    'env': self._cmd_env,
                    'recent-logs': lambda: self._cmd_recent_logs(args),
                    'recent-backups': lambda: self._cmd_recent_backups(args),
                    'recent-reports': lambda: self._cmd_recent_reports(args),
                    'logs-json': self._cmd_logs_json,
                    'logs-export': lambda: self._cmd_logs_export(args),
                    'backups-json': self._cmd_backups_json,
                    'latest-report': self._cmd_latest_report,
                    'recent-devices': lambda: self._cmd_recent_devices(args),
                    'methods': lambda: self._cmd_methods(args),
                    'methods-json': self._cmd_methods_json,
                    'db-health': self._cmd_db_health,
                    'stats-plus': self._cmd_stats_plus,
                    'reports-json': self._cmd_reports_json,
                    'reports-open': self._cmd_reports_open,
                    'recent-reports-json': self._cmd_recent_reports_json,
                    'config': self._cmd_config,
                    'config-json': self._cmd_config_json,
                    'exports-open': self._cmd_exports_open,
                    'db-backup': self._cmd_db_backup,
                    'plugins': self._cmd_plugins,
                    'plugin': lambda: self._cmd_plugin(args),
                    'smart': lambda: self._cmd_smart(args),
                    'launcher': lambda: self._cmd_launcher(args),
                    'start-menu': lambda: self._cmd_launcher(args),
                    'advanced': self._cmd_advanced,
                    'bootstrap': lambda: self._cmd_bootstrap(args),
                    'search': lambda: self._cmd_search(args),
                    'help': lambda: self._cmd_help(args),
                    'exit': lambda: exit(0),
                    'quit': lambda: exit(0),
                    'q': lambda: exit(0),
                    '?': lambda: self._cmd_help([]),
                }

                commands = self._add_alias_commands(commands)
                command_key = self.command_aliases.get(command, command)

                if command_key in commands:
                    commands[command_key]()
                else:
                    suggestions = self._suggest_commands(command, list(commands.keys()))
                    self.logger.warning(
                        f"Unknown command: {command}",
                        extra={"category": "cli", "device_id": "-", "method": "-"},
                    )
                    if suggestions:
                        print(f"Did you mean: {', '.join(suggestions)}?")
                    print("Tip: use 'search <keyword>' or 'help <command>' for guidance.")

            except KeyboardInterrupt:
                self.logger.info(
                    "Use 'exit' to quit",
                    extra={"category": "cli", "device_id": "-", "method": "-"},
                )
            except Exception as exc:
                self.logger.exception(
                    f"Error: {exc}",
                    extra={"category": "cli", "device_id": "-", "method": "-"},
                )

    def _suggest_commands(self, command: str, options: List[str]) -> List[str]:
        """Suggest similar commands for typos or partial input."""
        if not command:
            return []

        prefix_matches = [option for option in options if option.startswith(command)]
        if prefix_matches:
            return self._format_suggestions(sorted(prefix_matches)[:5])

        return self._format_suggestions(difflib.get_close_matches(command, options, n=5, cutoff=0.5))

    def _format_suggestions(self, suggestions: List[str]) -> List[str]:
        """Prefer primary command names in suggestions."""
        resolved = []
        for suggestion in suggestions:
            resolved.append(self.command_aliases.get(suggestion, suggestion))
        return sorted(set(resolved), key=resolved.index)

    def _add_alias_commands(self, commands: Dict[str, Any]) -> Dict[str, Any]:
        for alias, target in self.command_aliases.items():
            if alias not in commands and target in commands:
                commands[alias] = commands[target]
        return commands

    def _build_command_aliases(self) -> Dict[str, str]:
        aliases: Dict[str, str] = {}
        for command in self.command_catalog.values():
            for alias in command.aliases:
                aliases[alias] = command.name
        return aliases

    def _build_command_catalog(self) -> Dict[str, CommandInfo]:
        catalog = [
            CommandInfo(
                name="advanced",
                summary="Show advanced Android tooling overview.",
                usage="advanced",
                category="Advanced Toolbox",
                examples=["advanced"],
                aliases=["toolbox"],
            ),
            CommandInfo(
                name="bootstrap",
                summary="Install bundled Android platform tools.",
                usage="bootstrap [force]",
                category="System & Diagnostics",
                examples=["bootstrap", "bootstrap force"],
            ),
            CommandInfo(
                name="devices",
                summary="List all connected devices.",
                usage="devices",
                category="Device Management",
                examples=["devices"],
                aliases=["list", "ls", "device"],
            ),
            CommandInfo(
                name="info",
                summary="Show detailed device info.",
                usage="info <device_id|smart>",
                category="Device Management",
                examples=["info emulator-5554", "info smart"],
            ),
            CommandInfo(
                name="summary",
                summary="Show a short summary for all devices.",
                usage="summary",
                category="Device Management",
                examples=["summary"],
            ),
            CommandInfo(
                name="backup",
                summary="Create an automated backup.",
                usage="backup <device_id|smart>",
                category="Backup & Data",
                examples=["backup emulator-5554", "backup smart"],
            ),
            CommandInfo(
                name="recover",
                summary="Recover contacts or SMS.",
                usage="recover <device_id|smart> <contacts|sms>",
                category="Backup & Data",
                examples=["recover emulator-5554 contacts", "recover smart sms"],
            ),
            CommandInfo(
                name="screenshot",
                summary="Capture a device screenshot.",
                usage="screenshot <device_id|smart>",
                category="Backup & Data",
                examples=["screenshot emulator-5554"],
            ),
            CommandInfo(
                name="apps",
                summary="List installed apps.",
                usage="apps <device_id|smart> [system|user|all]",
                category="Apps & Files",
                examples=["apps smart", "apps emulator-5554 user"],
            ),
            CommandInfo(
                name="files",
                summary="Manage files on the device.",
                usage="files <device_id|smart> <list|pull|push|delete> [path]",
                category="Apps & Files",
                examples=["files smart list /sdcard", "files emulator-5554 pull /sdcard/test.txt"],
            ),
            CommandInfo(
                name="analyze",
                summary="Run performance analysis.",
                usage="analyze <device_id|smart>",
                category="Analysis & Reports",
                examples=["analyze smart"],
            ),
            CommandInfo(
                name="display-diagnostics",
                summary="Run display and framebuffer diagnostics.",
                usage="display-diagnostics <device_id|smart>",
                category="Analysis & Reports",
                examples=["display-diagnostics emulator-5554"],
            ),
            CommandInfo(
                name="report",
                summary="Generate a full device report.",
                usage="report <device_id|smart>",
                category="Analysis & Reports",
                examples=["report smart"],
            ),
            CommandInfo(
                name="logcat",
                summary="View real-time logcat output.",
                usage="logcat <device_id|smart> [filter_tag]",
                category="Analysis & Reports",
                examples=["logcat emulator-5554", "logcat smart ActivityManager"],
            ),
            CommandInfo(
                name="tweak",
                summary="Apply system tweaks (dpi/animation/timeout).",
                usage="tweak <device_id|smart> <dpi|animation|timeout> <value>",
                category="System & Diagnostics",
                examples=["tweak smart dpi 320", "tweak emulator-5554 timeout 600000"],
            ),
            CommandInfo(
                name="usb-debug",
                summary="Enable or force USB debugging.",
                usage="usb-debug <device_id|smart> [force]",
                category="System & Diagnostics",
                examples=["usb-debug smart", "usb-debug emulator-5554 force"],
            ),
            CommandInfo(
                name="execute",
                summary="Execute an FRP method.",
                usage="execute <method> <device_id|smart>",
                category="FRP Bypass",
                examples=["execute adb_shell_reset smart"],
            ),
            CommandInfo(
                name="edl-status",
                summary="Show EDL mode status and USB IDs.",
                usage="edl-status <device_id|smart>",
                category="EDL & Test-point",
                examples=["edl-status usb-05c6:9008"],
            ),
            CommandInfo(
                name="edl-enter",
                summary="Enter EDL mode (if supported).",
                usage="edl-enter <device_id|smart>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-flash",
                summary="Flash an image via EDL.",
                usage="edl-flash <device_id|smart> <loader> <image>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-dump",
                summary="Dump a partition via EDL.",
                usage="edl-dump <device_id|smart> <partition>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-detect",
                summary="Scan USB for EDL devices.",
                usage="edl-detect",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-programmers",
                summary="List available firehose programmers.",
                usage="edl-programmers",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-partitions",
                summary="Show partition map via ADB or EDL.",
                usage="edl-partitions <device_id|smart> [loader]",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-backup",
                summary="Backup a partition via EDL.",
                usage="edl-backup <device_id|smart> <partition>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-restore",
                summary="Restore a partition via EDL.",
                usage="edl-restore <device_id|smart> <loader> <image>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-sparse",
                summary="Convert sparse images.",
                usage="edl-sparse <to-raw|to-sparse> <source> <dest>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-profile",
                summary="Manage EDL profiles.",
                usage="edl-profile <list|add|delete> [name] [json]",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-verify",
                summary="Verify image hash.",
                usage="edl-verify <file> [sha256]",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-unbrick",
                summary="Show an unbrick checklist.",
                usage="edl-unbrick [loader]",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-notes",
                summary="Show device-specific notes.",
                usage="edl-notes [vendor]",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-reboot",
                summary="Reboot to a target mode.",
                usage="edl-reboot <device_id|smart> <edl|fastboot|recovery|bootloader|system>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="edl-log",
                summary="Capture EDL workflow logs.",
                usage="edl-log",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="boot-extract",
                summary="Extract boot image contents.",
                usage="boot-extract <boot.img>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="magisk-patch",
                summary="Stage a Magisk patch workflow.",
                usage="magisk-patch <device_id|smart> <boot.img>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="magisk-pull",
                summary="Pull Magisk patched image.",
                usage="magisk-pull <device_id|smart> [output_dir]",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="twrp-verify",
                summary="Verify a TWRP image matches device codename.",
                usage="twrp-verify <device_id|smart> <twrp.img>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="twrp-flash",
                summary="Flash or boot TWRP recovery via fastboot.",
                usage="twrp-flash <device_id|smart> <twrp.img> [boot]",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="root-verify",
                summary="Verify root access via ADB.",
                usage="root-verify <device_id|smart>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="safety-check",
                summary="Run safety checklist for device operations.",
                usage="safety-check <device_id|smart>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="rollback",
                summary="Rollback a partition flash.",
                usage="rollback <device_id|smart> <partition> <image>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="compat-matrix",
                summary="Show EDL compatibility matrix.",
                usage="compat-matrix",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="testpoint-guide",
                summary="Show test-point references.",
                usage="testpoint-guide <device_id|smart>",
                category="EDL & Test-point",
            ),
            CommandInfo(
                name="stats",
                summary="Show suite statistics.",
                usage="stats",
                category="System",
            ),
            CommandInfo(
                name="monitor",
                summary="Show system resource usage.",
                usage="monitor",
                category="System",
            ),
            CommandInfo(
                name="version",
                summary="Show suite version details.",
                usage="version",
                category="System",
            ),
            CommandInfo(
                name="paths",
                summary="Show local data directories.",
                usage="paths",
                category="System",
            ),
            CommandInfo(
                name="menu",
                summary="Launch interactive menu.",
                usage="menu",
                category="System",
            ),
            CommandInfo(
                name="netcheck",
                summary="Check internet connectivity.",
                usage="netcheck",
                category="System",
            ),
            CommandInfo(
                name="adb",
                summary="Check ADB availability.",
                usage="adb",
                category="System",
            ),
            CommandInfo(
                name="clear-cache",
                summary="Clear local cache directory.",
                usage="clear-cache",
                category="System",
            ),
            CommandInfo(
                name="doctor",
                summary="Run quick system checks.",
                usage="doctor",
                category="System",
            ),
            CommandInfo(
                name="logs",
                summary="List recent log files.",
                usage="logs",
                category="System",
            ),
            CommandInfo(
                name="backups",
                summary="List recent backups.",
                usage="backups",
                category="System",
            ),
            CommandInfo(
                name="reports",
                summary="List recent reports.",
                usage="reports",
                category="System",
            ),
            CommandInfo(
                name="exports",
                summary="List recent exports.",
                usage="exports",
                category="System",
            ),
            CommandInfo(
                name="devices-json",
                summary="Export devices to JSON.",
                usage="devices-json",
                category="System",
            ),
            CommandInfo(
                name="stats-json",
                summary="Export stats to JSON.",
                usage="stats-json",
                category="System",
            ),
            CommandInfo(
                name="logtail",
                summary="Tail recent log lines.",
                usage="logtail [lines]",
                category="System",
            ),
            CommandInfo(
                name="cleanup-exports",
                summary="Remove old exports.",
                usage="cleanup-exports",
                category="System",
            ),
            CommandInfo(
                name="cleanup-backups",
                summary="Remove old backups.",
                usage="cleanup-backups",
                category="System",
            ),
            CommandInfo(
                name="cleanup-reports",
                summary="Remove old reports.",
                usage="cleanup-reports",
                category="System",
            ),
            CommandInfo(
                name="env",
                summary="Show environment info.",
                usage="env",
                category="System",
            ),
            CommandInfo(
                name="recent-logs",
                summary="Show recent log entries.",
                usage="recent-logs [count]",
                category="System",
            ),
            CommandInfo(
                name="recent-backups",
                summary="Show recent backup records.",
                usage="recent-backups [count]",
                category="System",
            ),
            CommandInfo(
                name="recent-reports",
                summary="Show recent report records.",
                usage="recent-reports [count]",
                category="System",
            ),
            CommandInfo(
                name="logs-json",
                summary="Export logs to JSON.",
                usage="logs-json",
                category="System",
            ),
            CommandInfo(
                name="logs-export",
                summary="Export filtered logs to JSON or CSV.",
                usage="logs-export <json|csv> [filters]",
                category="System",
            ),
            CommandInfo(
                name="backups-json",
                summary="Export backups to JSON.",
                usage="backups-json",
                category="System",
            ),
            CommandInfo(
                name="latest-report",
                summary="Show latest report paths.",
                usage="latest-report",
                category="System",
            ),
            CommandInfo(
                name="recent-devices",
                summary="Show recent devices.",
                usage="recent-devices [count]",
                category="System",
            ),
            CommandInfo(
                name="methods",
                summary="Show top methods.",
                usage="methods [count]",
                category="System",
            ),
            CommandInfo(
                name="methods-json",
                summary="Export methods to JSON.",
                usage="methods-json",
                category="System",
            ),
            CommandInfo(
                name="db-health",
                summary="Show database health summary.",
                usage="db-health",
                category="System",
            ),
            CommandInfo(
                name="stats-plus",
                summary="Show extended stats.",
                usage="stats-plus",
                category="System",
            ),
            CommandInfo(
                name="reports-json",
                summary="Export reports to JSON.",
                usage="reports-json",
                category="System",
            ),
            CommandInfo(
                name="smart",
                summary="Show or toggle smart features.",
                usage="smart [status|on|off|auto-device|prefer-last|auto-doctor|suggest|safety] [on|off]",
                category="System",
                aliases=["assist", "suggest"],
            ),
            CommandInfo(
                name="launcher",
                summary="Manage start menu launchers.",
                usage="launcher <install|uninstall|status>",
                category="System",
            ),
            CommandInfo(
                name="reports-open",
                summary="Open reports directory.",
                usage="reports-open",
                category="System",
            ),
            CommandInfo(
                name="recent-reports-json",
                summary="Export recent reports to JSON.",
                usage="recent-reports-json",
                category="System",
            ),
            CommandInfo(
                name="config",
                summary="Show configuration values.",
                usage="config",
                category="System",
            ),
            CommandInfo(
                name="config-json",
                summary="Export configuration to JSON.",
                usage="config-json",
                category="System",
            ),
            CommandInfo(
                name="exports-open",
                summary="Open exports directory.",
                usage="exports-open",
                category="System",
            ),
            CommandInfo(
                name="db-backup",
                summary="Backup database to exports.",
                usage="db-backup",
                category="System",
            ),
            CommandInfo(
                name="plugins",
                summary="List available plugins.",
                usage="plugins",
                category="Plugins",
            ),
            CommandInfo(
                name="plugin",
                summary="Run a plugin by id.",
                usage="plugin <id> [args]",
                category="Plugins",
            ),
            CommandInfo(
                name="search",
                summary="Search commands by keyword.",
                usage="search <keyword>",
                category="Help",
                aliases=["find", "lookup"],
            ),
            CommandInfo(
                name="help",
                summary="Show help or command details.",
                usage="help [command]",
                category="Help",
                aliases=["h", "man"],
            ),
            CommandInfo(
                name="exit",
                summary="Exit the suite.",
                usage="exit",
                category="Help",
                aliases=["quit", "q"],
            ),
        ]
        return {command.name: command for command in catalog}

    def _print_toolkit_result(self, result: ToolkitResult) -> None:
        icon = "✅" if result.success else "⚠️"
        print(f"{icon} {result.message}")
        if result.data:
            print(json.dumps(result.data, indent=2))

    def _print_banner(self) -> None:
        """Print banner."""
        features_count = 200  # Total automated features

        box_width = 62

        def pad(text: str) -> str:
            return text.ljust(box_width)

        slogan_lines = Config.THEME_SLOGANS[:2]
        banner = (
            f"╔{'═' * box_width}╗\n"
            f"║ {pad(f'VOID v{Config.VERSION} - {Config.CODENAME}')} ║\n"
            f"║ {pad(Config.THEME_TAGLINE)} ║\n"
            f"║ {pad(f'{features_count}+ automated features • {Config.THEME_NAME}')} ║\n"
            f"╚{'═' * box_width}╝\n\n"
            f"✨ {slogan_lines[0]}\n"
            f"✨ {slogan_lines[1]}\n\n"
            "Type 'help' to see all available commands.\n"
            "Type 'help <command>' for detailed usage.\n"
            "Type 'search <keyword>' to find commands.\n"
            "Type 'menu' to launch the interactive menu.\n"
        )
        print(banner)

    def _cmd_devices(self) -> None:
        """List devices."""
        devices, _ = DeviceDetector.detect_all()

        if not devices:
            print("❌ No devices detected")
            return

        if self.console:
            table = Table(title="Connected Devices")
            table.add_column("ID", style="cyan")
            table.add_column("Modes", style="green")
            table.add_column("Status", style="white")
            table.add_column("Manufacturer", style="yellow")
            table.add_column("Model", style="blue")
            table.add_column("Android", style="magenta")

            for device in devices:
                modes = device.get("modes") or [device.get("mode", "Unknown")]
                mode_label = ", ".join(modes) if isinstance(modes, list) else str(modes)
                table.add_row(
                    device.get('id', 'Unknown'),
                    mode_label,
                    device.get('status', 'Unknown'),
                    device.get('manufacturer', 'Unknown'),
                    device.get('model', 'Unknown'),
                    device.get('android_version', 'Unknown')
                )

            self.console.print(table)
        else:
            print("\n📱 Connected Devices:")
            for device in devices:
                status = device.get('status', 'Unknown')
                modes = device.get("modes") or [device.get("mode", "Unknown")]
                mode_label = ", ".join(modes) if isinstance(modes, list) else str(modes)
                print(
                    f"  • {device.get('id')} - {device.get('manufacturer')} "
                    f"{device.get('model')} ({status}) [{mode_label}]"
                )

    def _cmd_backup(self, args: List[str]) -> None:
        """Create backup."""
        device_id = self._resolve_device_id(args, "backup <device_id|smart>")
        if not device_id:
            return

        result = AutoBackup.create_backup(device_id)
        if result['success']:
            print(f"✅ Backup created: {result['backup_name']}")
            print(f"   Items: {', '.join(result['items'])}")
            print(f"   Size: {result['size']:,} bytes")
        else:
            print("❌ Backup failed")

    def _cmd_screenshot(self, args: List[str]) -> None:
        """Take screenshot."""
        device_id = self._resolve_device_id(args, "screenshot <device_id|smart>")
        if not device_id:
            return

        result = ScreenCapture.take_screenshot(device_id)
        if result['success']:
            print(f"✅ Screenshot saved: {result['path']}")
        else:
            print("❌ Screenshot failed")

    def _cmd_apps(self, args: List[str]) -> None:
        """List apps."""
        device_id = self._resolve_device_id(args, "apps <device_id|smart> [system|user|all]")
        if not device_id:
            return

        filter_type = args[1] if len(args) > 1 else 'all'
        apps = AppManager.list_apps(device_id, filter_type)

        print(f"\n📦 {filter_type.title()} Apps ({len(apps)}):")
        for app in apps[:20]:
            print(f"  • {app['package']}")

        if len(apps) > 20:
            print(f"  ... and {len(apps) - 20} more")

    def _cmd_display_diagnostics(self, args: List[str]) -> None:
        """Run display diagnostics."""
        device_id = self._resolve_device_id(args, "display-diagnostics <device_id|smart>")
        if not device_id:
            return

        diagnostics = DisplayAnalyzer.analyze(device_id)
        print(json.dumps(diagnostics, indent=2))

    def _cmd_info(self, args: List[str]) -> None:
        """Show device info."""
        device_id = self._resolve_device_id(args, "info <device_id|smart>")
        if not device_id:
            return

        devices, _ = DeviceDetector.detect_all()
        device = next((d for d in devices if d['id'] == device_id), None)

        if device:
            print(f"\n📱 Device Information: {device_id}\n")
            for key, value in device.items():
                if not isinstance(value, dict):
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        else:
            print("❌ Device not found")

    def _cmd_summary(self) -> None:
        """Show a short device summary."""
        devices, _ = DeviceDetector.detect_all()
        if not devices:
            print("❌ No devices detected")
            return

        print("\n📋 Device Summary\n")
        for device in devices:
            device_id = device.get('id', 'Unknown')
            model = device.get('model', 'Unknown')
            brand = device.get('brand', 'Unknown')
            android = device.get('android_version', 'Unknown')
            security = device.get('security_patch', 'Unknown')
            reachable = "Yes" if device.get("reachable") else "No"
            status = device.get('status', 'Unknown')
            modes = device.get("modes") or [device.get("mode", "Unknown")]
            mode_label = ", ".join(modes) if isinstance(modes, list) else str(modes)
            print(
                f"• {device_id} — {brand} {model} | Android {android} | Patch {security} "
                f"| Status: {status} | Modes: {mode_label} | Reachable: {reachable}"
            )

    def _cmd_menu(self) -> None:
        """Launch interactive menu."""
        self._run_menu()

    def _run_menu(self) -> None:
        """Interactive menu navigation."""
        menu_stack = [("Main Menu", self._menu_main())]

        while menu_stack:
            title, items = menu_stack[-1]
            self._render_menu(title, items, menu_stack)

            choice = self._prompt("Select an option (number or shortcut)").lower()
            if not choice:
                continue
            if choice in {"q", "quit", "exit"}:
                return
            if choice in {"h", "help", "?"}:
                self._print_menu_help()
                continue
            if choice in {"b", "back", "0"}:
                if len(menu_stack) > 1:
                    menu_stack.pop()
                else:
                    return
                continue

            matched = self._match_menu_choice(choice, items)
            if not matched:
                print("❌ Invalid selection")
                continue

            if "submenu" in matched:
                menu_stack.append((matched["label"], matched["submenu"]))
                continue
            action = matched.get("action")
            if action:
                action()
            if matched.get("exit"):
                return

    def _render_menu(self, title: str, items: List[Dict[str, Any]], stack: List[Any]) -> None:
        """Render a menu with optional rich formatting."""
        breadcrumb = " > ".join(level[0] for level in stack)
        subtitle = f"Path: {breadcrumb}"
        if self.last_device_id:
            subtitle = f"{subtitle} | Last device: {self.last_device_id}"

        if self.console:
            table = Table(title=f"📋 {title}", show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4, justify="right")
            table.add_column("Action", style="bold")
            table.add_column("Description", style="white")
            table.add_column("Shortcut", style="magenta", width=8, justify="center")
            for index, item in enumerate(items, start=1):
                table.add_row(
                    str(index),
                    item["label"],
                    item.get("desc", ""),
                    item.get("shortcut", "")
                )
            self.console.print(Panel.fit(subtitle, style="dim"))
            self.console.print(table)
            self.console.print("[dim]b[/dim]=Back  [dim]h[/dim]=Help  [dim]q[/dim]=Quit  [dim]0[/dim]=Back  [?]=Help")
        else:
            print(f"\n📋 {title}")
            print(f"   {subtitle}\n")
            for index, item in enumerate(items, start=1):
                desc = f" — {item.get('desc', '')}" if item.get("desc") else ""
                shortcut = f"[{item.get('shortcut')}]" if item.get("shortcut") else ""
                print(f"  {index}. {item['label']} {shortcut}{desc}")
            print("\n  b. Back   h. Help   q. Quit   0. Back   ?. Help")

    def _print_menu_help(self) -> None:
        """Print menu usage help."""
        print("\nTip: Use numbers or shortcuts to navigate.")
        print("Type 'b' or '0' to go back, 'q' to quit.\n")

    def _match_menu_choice(self, choice: str, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Match menu choice to an item."""
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(items):
                return items[index]
            return None
        for item in items:
            if item.get("shortcut") == choice:
                return item
        return None

    def _menu_main(self) -> List[Dict[str, Any]]:
        """Main menu items."""
        return [
            {"label": "Devices", "desc": "Detect and inspect connected devices", "shortcut": "d", "submenu": self._menu_devices()},
            {"label": "Backup & Recovery", "desc": "Backups and data recovery tools", "shortcut": "b", "submenu": self._menu_backup()},
            {"label": "Apps & Files", "desc": "App listing and file operations", "shortcut": "a", "submenu": self._menu_apps_files()},
            {"label": "Analysis & Reports", "desc": "Performance analysis and reports", "shortcut": "r", "submenu": self._menu_analysis()},
            {"label": "System & Diagnostics", "desc": "Health checks and system tools", "shortcut": "s", "submenu": self._menu_system()},
            {"label": "Advanced Toolbox", "desc": "EDL, recovery, and expert workflows", "shortcut": "x", "action": self._cmd_advanced},
            {"label": "Exit Menu", "desc": "Return to CLI prompt", "shortcut": "q", "exit": True},
        ]

    def _menu_devices(self) -> List[Dict[str, Any]]:
        """Device menu items."""
        return [
            {"label": "List devices", "desc": "Show all connected devices", "shortcut": "l", "action": self._cmd_devices},
            {"label": "Device summary", "desc": "Quick overview of all devices", "shortcut": "s", "action": self._cmd_summary},
            {"label": "Device info", "desc": "Inspect a single device", "shortcut": "i", "action": self._menu_device_info},
            {"label": "Screenshot", "desc": "Capture device screen", "shortcut": "c", "action": self._menu_screenshot},
        ]

    def _menu_backup(self) -> List[Dict[str, Any]]:
        """Backup menu items."""
        return [
            {"label": "Create backup", "desc": "Automated device backup", "shortcut": "b", "action": self._menu_backup_create},
            {"label": "Recover contacts", "desc": "Restore contacts data", "shortcut": "c", "action": lambda: self._menu_recover("contacts")},
            {"label": "Recover SMS", "desc": "Restore SMS messages", "shortcut": "s", "action": lambda: self._menu_recover("sms")},
            {"label": "Recent backups (DB)", "desc": "Show recent backup records", "shortcut": "r", "action": lambda: self._cmd_recent_backups([])},
        ]

    def _menu_apps_files(self) -> List[Dict[str, Any]]:
        """Apps and files menu items."""
        return [
            {"label": "List apps", "desc": "List installed apps", "shortcut": "a", "action": self._menu_apps},
            {"label": "List files", "desc": "Browse device storage", "shortcut": "l", "action": lambda: self._menu_files("list")},
            {"label": "Pull file", "desc": "Copy file from device", "shortcut": "p", "action": lambda: self._menu_files("pull")},
            {"label": "Push file", "desc": "Copy file to device", "shortcut": "u", "action": lambda: self._menu_files("push")},
            {"label": "Delete file", "desc": "Remove file from device", "shortcut": "d", "action": lambda: self._menu_files("delete")},
        ]

    def _menu_analysis(self) -> List[Dict[str, Any]]:
        """Analysis menu items."""
        return [
            {"label": "Analyze device", "desc": "Performance analysis", "shortcut": "a", "action": self._menu_analyze},
            {"label": "Generate report", "desc": "Create full device report", "shortcut": "g", "action": self._menu_report},
            {"label": "Latest report paths", "desc": "Show latest report files", "shortcut": "l", "action": self._cmd_latest_report},
            {"label": "Recent reports (DB)", "desc": "Show recent report records", "shortcut": "r", "action": lambda: self._cmd_recent_reports([])},
        ]

    def _menu_system(self) -> List[Dict[str, Any]]:
        """System menu items."""
        return [
            {"label": "Suite stats", "desc": "Usage statistics", "shortcut": "s", "action": self._cmd_stats},
            {"label": "Version info", "desc": "Suite version details", "shortcut": "v", "action": self._cmd_version},
            {"label": "System monitor", "desc": "CPU/Memory/Disk usage", "shortcut": "m", "action": self._cmd_monitor},
            {"label": "Show paths", "desc": "Local data directories", "shortcut": "p", "action": self._cmd_paths},
            {"label": "Install platform tools", "desc": "Bundle ADB/Fastboot locally", "shortcut": "z", "action": lambda: self._cmd_bootstrap([])},
            {"label": "System checks", "desc": "Connectivity and health checks", "shortcut": "d", "action": self._cmd_doctor},
            {"label": "Network check", "desc": "Internet reachability", "shortcut": "n", "action": self._cmd_netcheck},
            {"label": "ADB availability", "desc": "ADB version check", "shortcut": "a", "action": self._cmd_adb},
            {"label": "DB health", "desc": "Database size and totals", "shortcut": "h", "action": self._cmd_db_health},
            {"label": "Recent logs (DB)", "desc": "Latest log entries", "shortcut": "l", "action": lambda: self._cmd_recent_logs([])},
            {"label": "Tail log file", "desc": "Show last 50 lines", "shortcut": "t", "action": lambda: self._cmd_logtail(["50"])},
            {"label": "Clear cache", "desc": "Clear cached files", "shortcut": "c", "action": self._cmd_clear_cache},
            {"label": "Log files", "desc": "List recent log files", "shortcut": "g", "action": self._cmd_logs},
            {"label": "Backups", "desc": "List recent backups", "shortcut": "b", "action": self._cmd_backups},
            {"label": "Reports", "desc": "List recent reports", "shortcut": "r", "action": self._cmd_reports},
            {"label": "Exports", "desc": "List recent exports", "shortcut": "e", "action": self._cmd_exports},
            {"label": "Environment", "desc": "Runtime environment info", "shortcut": "i", "action": self._cmd_env},
            {"label": "Smart mode", "desc": "Smart suggestions and toggles", "shortcut": "x", "action": lambda: self._cmd_smart([])},
            {"label": "Start menu launcher", "desc": "Install or remove launchers", "shortcut": "y", "action": lambda: self._cmd_launcher([])},
        ]

    def _prompt(self, label: str) -> str:
        """Prompt with input length guard."""
        value = input(f"{label}: ").strip()
        if len(value) > Config.MAX_INPUT_LENGTH:
            print(f"❌ Input too long (max {Config.MAX_INPUT_LENGTH} characters)")
            return ""
        return value

    def _smart_startup(self) -> None:
        """Provide smart startup diagnostics and suggestions."""
        if not Config.SMART_ENABLED:
            return

        devices, errors = SmartAdvisor.snapshot()
        if Config.SMART_AUTO_DOCTOR and (errors or not devices):
            print("\n🤖 Smart check: running system diagnostics...")
            self._cmd_doctor()

        if Config.SMART_SUGGESTIONS:
            suggestions = SmartAdvisor.recommend_actions(devices, errors)
            if suggestions:
                print("\n🤖 Smart suggestions:")
                for suggestion in suggestions:
                    print(f"  • {suggestion}")

        if errors:
            print("\n⚠️  Detection issues:")
            for error in SmartAdvisor.format_errors(errors):
                print(f"  • {error}")

    def _smart_select_device(self) -> Optional[str]:
        if not (Config.SMART_ENABLED and Config.SMART_AUTO_DEVICE):
            return None

        choice = SmartAdvisor.pick_device(
            last_device_id=self.last_device_id,
            prefer_last=Config.SMART_PREFER_LAST_DEVICE,
        )
        if not choice:
            return None

        self.last_device_id = choice.device_id
        print(f"🤖 Smart-selected device: {SmartAdvisor.summarize_choice(choice)}")
        return choice.device_id

    def _resolve_device_id(self, args: List[str], usage: str) -> Optional[str]:
        """Resolve device id, honoring smart defaults."""
        if args:
            candidate = args[0]
            if candidate.lower() in {"smart", "auto"}:
                device_id = self._smart_select_device()
                if device_id:
                    return device_id
                print("❌ Smart selection failed. Provide a device ID.")
                return None
            return candidate

        if Config.SMART_ENABLED and Config.SMART_AUTO_DEVICE:
            device_id = self._smart_select_device()
            if device_id:
                return device_id

        print(f"Usage: {usage}")
        return None

    def _smart_confirm(self, prompt: str) -> bool:
        """Confirm risky actions when smart safeguards are enabled."""
        if not (Config.SMART_ENABLED and Config.SMART_SAFE_GUARDS):
            return True
        response = self._prompt(f"{prompt} (y/N)").lower()
        return response in {"y", "yes"}

    def _prompt_device(self) -> Optional[str]:
        """Prompt for device id, defaulting to last device."""
        smart_device = self._smart_select_device()
        if smart_device:
            return smart_device

        prompt = "Device ID"
        if self.last_device_id:
            prompt = f"Device ID (Enter for {self.last_device_id})"
        device_id = self._prompt(prompt)
        if not device_id and self.last_device_id:
            device_id = self.last_device_id
        if device_id:
            self.last_device_id = device_id
        return device_id

    def _menu_device_info(self) -> None:
        """Prompt for device info."""
        device_id = self._prompt_device()
        if not device_id:
            return
        self._cmd_info([device_id])

    def _menu_backup_create(self) -> None:
        """Prompt for backup create."""
        device_id = self._prompt_device()
        if not device_id:
            return
        self._cmd_backup([device_id])

    def _menu_recover(self, data_type: str) -> None:
        """Prompt for data recovery."""
        device_id = self._prompt_device()
        if not device_id:
            return
        self._cmd_recover([device_id, data_type])

    def _menu_screenshot(self) -> None:
        """Prompt for screenshot."""
        device_id = self._prompt_device()
        if not device_id:
            return
        self._cmd_screenshot([device_id])

    def _menu_apps(self) -> None:
        """Prompt for apps listing."""
        device_id = self._prompt_device()
        if not device_id:
            return
        filter_type = self._prompt("Filter (system/user/all)") or "all"
        self._cmd_apps([device_id, filter_type])

    def _menu_files(self, operation: str) -> None:
        """Prompt for file operations."""
        device_id = self._prompt_device()
        if not device_id:
            return
        if operation == "list":
            path = self._prompt("Remote path (/sdcard)") or "/sdcard"
            self._cmd_files([device_id, "list", path])
            return
        if operation == "pull":
            remote_path = self._prompt("Remote path")
            if not remote_path:
                return
            local_path = self._prompt("Local path (optional)")
            args = [device_id, "pull", remote_path]
            if local_path:
                args.append(local_path)
            self._cmd_files(args)
            return
        if operation == "push":
            local_path = self._prompt("Local path")
            remote_path = self._prompt("Remote path")
            if not local_path or not remote_path:
                return
            self._cmd_files([device_id, "push", local_path, remote_path])
            return
        if operation == "delete":
            remote_path = self._prompt("Remote path")
            if not remote_path:
                return
            self._cmd_files([device_id, "delete", remote_path])

    def _menu_analyze(self) -> None:
        """Prompt for analysis."""
        device_id = self._prompt_device()
        if not device_id:
            return
        self._cmd_analyze([device_id])

    def _menu_report(self) -> None:
        """Prompt for report generation."""
        device_id = self._prompt_device()
        if not device_id:
            return
        self._cmd_report([device_id])

    def _cmd_version(self) -> None:
        """Show suite version."""
        print(f"Void v{Config.VERSION} - {Config.CODENAME}")

    def _cmd_paths(self) -> None:
        """Show local data paths."""
        print("\n📂 Local Data Paths\n")
        print(f"  Base: {Config.BASE_DIR}")
        print(f"  Logs: {Config.LOG_DIR}")
        print(f"  Backups: {Config.BACKUP_DIR}")
        print(f"  Exports: {Config.EXPORTS_DIR}")
        print(f"  Cache: {Config.CACHE_DIR}")
        print(f"  Reports: {Config.REPORTS_DIR}")
        print(f"  Monitoring: {Config.MONITOR_DIR}")
        print(f"  Scripts: {Config.SCRIPTS_DIR}")

    def _cmd_netcheck(self) -> None:
        """Check internet connectivity."""
        status = "Online" if NetworkTools.check_internet() else "Offline"
        print(f"🌐 Internet: {status}")

    def _cmd_adb(self) -> None:
        """Check ADB availability."""
        code, stdout, stderr = SafeSubprocess.run(['adb', 'version'])
        if code == 0:
            first_line = stdout.strip().splitlines()[0] if stdout else "ADB available"
            print(f"✅ {first_line}")
        else:
            message = stderr.strip() or "ADB not available"
            print(f"❌ {message}")

    def _cmd_clear_cache(self) -> None:
        """Clear cache directory."""
        if Config.CACHE_DIR.exists():
            shutil.rmtree(Config.CACHE_DIR)
        Config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Cache cleared: {Config.CACHE_DIR}")

    def _cmd_doctor(self) -> None:
        """Run quick system checks."""
        print("\n🧪 System Checks\n")
        internet_status = "Online" if NetworkTools.check_internet() else "Offline"
        print(f"  Internet: {internet_status}")

        android_tools = check_android_tools()
        adb_result = next((tool for tool in android_tools if tool.name == "adb"), None)
        if adb_result and adb_result.available:
            version = adb_result.version or "ADB available"
            if adb_result.error:
                version = f"{version} (version unknown)"
            print(f"  ADB: {version}")
        else:
            message = (adb_result.error.get("message") if adb_result else "ADB not available")
            print(f"  ADB: {message}")

        print(f"  Monitoring: {'Available' if PSUTIL_AVAILABLE else 'Unavailable (install psutil)'}")
        print(f"  DB Path: {Config.DB_PATH}")

        print("\n🧰 Tooling\n")
        tool_groups = [
            ("Android", android_tools),
            ("Qualcomm", check_qualcomm_tools()),
            ("MediaTek", check_mediatek_tools()),
        ]
        for label, tools in tool_groups:
            print(f"  {label}:")
            for tool in tools:
                if tool.available:
                    version = tool.version or "available"
                    if tool.error:
                        version = f"{version} (version unknown)"
                    print(f"    - {tool.name}: {version}")
                else:
                    message = tool.error.get("message", "missing")
                    print(f"    - {tool.name}: {message}")

    def _cmd_bootstrap(self, args: List[str]) -> None:
        """Install bundled Android platform tools."""
        force = bool(args and args[0].lower() == "force")
        print("\n📦 Installing Android platform tools\n")
        result = install_android_platform_tools(force=force)
        status = result.get("status", "fail")
        message = result.get("message", "Install failed.")
        detail = result.get("detail", "")
        icon = "✅" if status == "pass" else "⚠️" if status == "warn" else "❌"
        print(f"{icon} {message}")
        if detail:
            print(f"   {detail}")

        links = result.get("links") or []
        if links:
            print("\nLinks:")
            for link in links:
                print(f"  - {link.get('label')}: {link.get('url')}")

        print("\nNote: Qualcomm (edl/qdl/emmcdl) and MediaTek (mtkclient/SP Flash Tool)")
        print("tools are not bundled automatically. Install them if you need chipset recovery.")

    def _cmd_advanced(self) -> None:
        """Show advanced Android tooling overview."""
        print("\n🧰 Advanced Android Toolbox\n")
        print("Use these expert workflows with care. Always back up data first.\n")

        sections = {
            "EDL & Test-point": [
                "edl-status <device_id|smart>           - Detect EDL mode + USB VID/PID",
                "edl-enter <device_id|smart>            - Enter EDL mode (if supported)",
                "edl-flash <device_id|smart> <loader> <image> - Flash via EDL",
                "edl-dump <device_id|smart> <partition> - Dump a partition via EDL",
                "edl-detect                            - Scan USB for EDL devices",
                "edl-partitions <device_id|smart> [loader] - Show partition map",
                "edl-backup <device_id|smart> <partition> - Backup partition via EDL",
                "edl-restore <device_id|smart> <loader> <image> - Restore partition via EDL",
                "edl-sparse <to-raw|to-sparse> <source> <dest> - Convert sparse images",
                "edl-verify <file> [sha256]             - Verify image hash",
                "edl-unbrick [loader]                   - Show unbrick checklist",
                "edl-notes [vendor]                     - Show device-specific notes",
                "edl-reboot <device_id|smart> <target>  - Reboot to target mode",
                "edl-log                               - Capture EDL workflow logs",
                "compat-matrix                          - Show EDL compatibility matrix",
                "testpoint-guide <device_id|smart>      - Show test-point references",
            ],
            "Recovery & Root": [
                "boot-extract <boot.img>                - Extract boot image contents",
                "magisk-patch <device_id|smart> <boot.img> - Stage Magisk patch workflow",
                "magisk-pull <device_id|smart> [output_dir] - Pull Magisk patched image",
                "twrp-verify <device_id|smart> <twrp.img> - Validate TWRP image",
                "twrp-flash <device_id|smart> <twrp.img> [boot] - Flash/boot TWRP",
                "root-verify <device_id|smart>          - Verify root access",
                "safety-check <device_id|smart>         - Run safety checklist",
                "rollback <device_id|smart> <partition> <image> - Roll back a flash",
            ],
            "FRP & Security": [
                "execute <method> <device_id|smart>     - Execute bypass method",
                "methods [count]                        - Show top methods",
            ],
            "Chipset & Recovery Utilities": [
                "edl-programmers                       - List available firehose programmers",
                "edl-profile <list|add|delete>          - Manage EDL profiles",
                "edl-notes [vendor]                     - Device-specific chipset notes",
            ],
            "Discoverability": [
                "search <keyword>                       - Find commands quickly",
                "help <command>                         - Show detailed usage",
                "bootstrap [force]                      - Install bundled platform tools",
                "menu                                  - Launch interactive menu",
            ],
        }

        for title, entries in sections.items():
            print(f"{title}:")
            for entry in entries:
                print(f"  {entry}")
            print("")

        print("🧰 Tooling Status")
        tool_groups = [
            ("Android", check_android_tools()),
            ("Qualcomm", check_qualcomm_tools()),
            ("MediaTek", check_mediatek_tools()),
        ]
        for label, tools in tool_groups:
            print(f"  {label}:")
            for tool in tools:
                if tool.available:
                    version = tool.version or "available"
                    if tool.error:
                        version = f"{version} (version unknown)"
                    print(f"    - {tool.name}: {version}")
                else:
                    message = tool.error.get("message", "missing")
                    print(f"    - {tool.name}: {message}")
        print("")

    def _cmd_logs(self) -> None:
        """List recent log files."""
        print("\n🧾 Recent Logs\n")
        logs = sorted(Config.LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            print("  No log files found.")
            return
        for log in logs[:10]:
            size = log.stat().st_size
            print(f"  {log.name} ({size:,} bytes)")

    def _cmd_backups(self) -> None:
        """List recent backups."""
        print("\n💾 Recent Backups\n")
        items = sorted(Config.BACKUP_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not items:
            print("  No backups found.")
            return
        for item in items[:10]:
            size = item.stat().st_size if item.is_file() else 0
            label = "dir" if item.is_dir() else "file"
            print(f"  {item.name} ({label}, {size:,} bytes)")

    def _cmd_reports(self) -> None:
        """List recent reports."""
        print("\n📄 Recent Reports\n")
        items = sorted(Config.REPORTS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not items:
            print("  No reports found.")
            return
        for item in items[:10]:
            size = item.stat().st_size if item.is_file() else 0
            label = "dir" if item.is_dir() else "file"
            print(f"  {item.name} ({label}, {size:,} bytes)")

    def _cmd_exports(self) -> None:
        """List recent exports."""
        print("\n📦 Recent Exports\n")
        items = sorted(Config.EXPORTS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not items:
            print("  No exports found.")
            return
        for item in items[:10]:
            size = item.stat().st_size if item.is_file() else 0
            label = "dir" if item.is_dir() else "file"
            print(f"  {item.name} ({label}, {size:,} bytes)")

    def _cmd_devices_json(self) -> None:
        """Export connected devices to JSON."""
        devices, _ = DeviceDetector.detect_all()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"devices_{timestamp}.json"
        export_path.write_text(json.dumps(devices, indent=2))
        print(f"✅ Devices exported: {export_path}")

    def _cmd_stats_json(self) -> None:
        """Export database stats to JSON."""
        stats = db.get_statistics()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"stats_{timestamp}.json"
        export_path.write_text(json.dumps(stats, indent=2))
        print(f"✅ Stats exported: {export_path}")

    def _cmd_logtail(self, args: List[str]) -> None:
        """Show recent log lines."""
        line_count = 50
        if args:
            try:
                line_count = max(1, int(args[0]))
            except ValueError:
                print("Usage: logtail [lines]")
                return

        logs = sorted(Config.LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            print("❌ No log files found")
            return

        log_path = logs[0]
        print(f"\n🧾 Tail: {log_path.name} (last {line_count} lines)\n")
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            recent = deque(handle, maxlen=line_count)
        for line in recent:
            print(line.rstrip())

    def _cmd_cleanup_exports(self) -> None:
        """Remove old exports."""
        cutoff = datetime.now() - timedelta(days=7)
        removed = 0
        for item in Config.EXPORTS_DIR.glob("*"):
            if datetime.fromtimestamp(item.stat().st_mtime) < cutoff:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed += 1
        print(f"✅ Removed {removed} export(s) older than 7 days")

    def _cmd_cleanup_backups(self) -> None:
        """Remove old backups."""
        cutoff = datetime.now() - timedelta(days=30)
        removed = 0
        for item in Config.BACKUP_DIR.glob("*"):
            if datetime.fromtimestamp(item.stat().st_mtime) < cutoff:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed += 1
        print(f"✅ Removed {removed} backup(s) older than 30 days")

    def _cmd_cleanup_reports(self) -> None:
        """Remove old reports."""
        cutoff = datetime.now() - timedelta(days=30)
        removed = 0
        for item in Config.REPORTS_DIR.glob("*"):
            if datetime.fromtimestamp(item.stat().st_mtime) < cutoff:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed += 1
        print(f"✅ Removed {removed} report(s) older than 30 days")

    def _cmd_env(self) -> None:
        """Show environment info."""
        print("\n🧩 Environment\n")
        print(f"  User: {getpass.getuser()}")
        print(f"  Host: {platform.node()}")
        print(f"  OS: {platform.system()} {platform.release()}")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  CWD: {Path.cwd()}")

    def _cmd_recent_logs(self, args: List[str]) -> None:
        """Show recent log entries."""
        limit = 10
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                print("Usage: recent-logs [count]")
                return
        rows = db.get_recent_logs(limit=limit)
        if not rows:
            print("❌ No log entries found")
            return
        print("\n🧾 Recent Log Entries\n")
        for row in rows:
            timestamp = row.get("timestamp", "")
            level = row.get("level", "").upper()
            category = row.get("category", "")
            message = row.get("message", "")
            print(f"  [{timestamp}] {level} {category}: {message}")

    def _cmd_recent_backups(self, args: List[str]) -> None:
        """Show recent backup records."""
        limit = 10
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                print("Usage: recent-backups [count]")
                return
        rows = db.get_recent_backups(limit=limit)
        if not rows:
            print("❌ No backup records found")
            return
        print("\n💾 Recent Backup Records\n")
        for row in rows:
            name = row.get("backup_name", "Unknown")
            device_id = row.get("device_id", "Unknown")
            created = row.get("created", "")
            size = row.get("backup_size", 0)
            backup_type = row.get("backup_type", "Unknown")
            print(f"  {name} ({backup_type}) - {device_id} - {created} - {size:,} bytes")

    def _cmd_recent_reports(self, args: List[str]) -> None:
        """Show recent report records."""
        limit = 10
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                print("Usage: recent-reports [count]")
                return
        rows = db.get_recent_reports(limit=limit)
        if not rows:
            print("❌ No report records found")
            return
        print("\n📄 Recent Report Records\n")
        for row in rows:
            timestamp = row.get("timestamp", "")
            device_id = row.get("device_id", "Unknown")
            event_data = row.get("event_data", "{}")
            try:
                payload = json.loads(event_data)
            except json.JSONDecodeError:
                payload = {}
            report_name = payload.get("report_name", "Unknown")
            print(f"  {report_name} - {device_id} - {timestamp}")

    def _cmd_logs_json(self) -> None:
        """Export recent logs to JSON."""
        rows = db.get_recent_logs(limit=200)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"logs_{timestamp}.json"
        export_path.write_text(json.dumps(rows, indent=2))
        print(f"✅ Logs exported: {export_path}")

    def _cmd_logs_export(self, args: List[str]) -> None:
        """Export filtered logs to JSON or CSV."""
        if not args:
            print(
                "Usage: logs-export <json|csv> [level=info] [category=core] [device_id=...] "
                "[method=...] [since=YYYY-MM-DD] [until=YYYY-MM-DD] [limit=500]"
            )
            return

        export_format = args[0].lower()
        if export_format not in {"json", "csv"}:
            print("Usage: logs-export <json|csv> [filters...]")
            return

        filters: Dict[str, Optional[str] | int] = {
            "level": None,
            "category": None,
            "device_id": None,
            "method": None,
            "since": None,
            "until": None,
            "limit": 500,
        }

        for item in args[1:]:
            if "=" not in item:
                print("Usage: logs-export <json|csv> [filters...]")
                return
            key, value = item.split("=", 1)
            key = key.lstrip("-").lower()
            if key in {"device", "device_id"}:
                key = "device_id"
            if key == "limit":
                try:
                    filters["limit"] = max(1, int(value))
                except ValueError:
                    print("Usage: logs-export <json|csv> [filters...]")
                    return
                continue
            if key not in {"level", "category", "device_id", "method", "since", "until"}:
                print("Usage: logs-export <json|csv> [filters...]")
                return
            filters[key] = value

        rows = db.get_filtered_logs(
            level=filters["level"],
            category=filters["category"],
            device_id=filters["device_id"],
            method=filters["method"],
            since=filters["since"],
            until=filters["until"],
            limit=filters["limit"],
        )
        if not rows:
            print("❌ No log entries found")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"logs_filtered_{timestamp}.{export_format}"
        if export_format == "json":
            export_path.write_text(json.dumps(rows, indent=2))
        else:
            fieldnames = ["timestamp", "level", "category", "message", "device_id", "method"]
            with export_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        print(f"✅ Logs exported: {export_path}")

    def _cmd_backups_json(self) -> None:
        """Export recent backups to JSON."""
        rows = db.get_recent_backups(limit=200)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"backups_{timestamp}.json"
        export_path.write_text(json.dumps(rows, indent=2))
        print(f"✅ Backups exported: {export_path}")

    def _cmd_latest_report(self) -> None:
        """Show latest report paths."""
        reports = sorted(Config.REPORTS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not reports:
            print("❌ No reports found")
            return
        report_dir = reports[0]
        html_path = report_dir / "report.html"
        json_path = report_dir / "report.json"
        print(f"\n📄 Latest Report: {report_dir.name}\n")
        if html_path.exists():
            print(f"  HTML: {html_path}")
        if json_path.exists():
            print(f"  JSON: {json_path}")

    def _cmd_recent_devices(self, args: List[str]) -> None:
        """Show recent devices from database."""
        limit = 10
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                print("Usage: recent-devices [count]")
                return
        rows = db.get_recent_devices(limit=limit)
        if not rows:
            print("❌ No device records found")
            return
        print("\n📱 Recent Devices\n")
        for row in rows:
            device_id = row.get("id", "Unknown")
            manufacturer = row.get("manufacturer", "Unknown")
            model = row.get("model", "Unknown")
            android = row.get("android_version", "Unknown")
            last_seen = row.get("last_seen", "")
            count = row.get("connection_count", 0)
            print(f"  {device_id} - {manufacturer} {model} (Android {android}) - last seen {last_seen} ({count}x)")

    def _cmd_methods(self, args: List[str]) -> None:
        """Show top methods by success rate."""
        limit = 5
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                print("Usage: methods [count]")
                return
        rows = db.get_top_methods(limit=limit)
        if not rows:
            print("❌ No method records found")
            return
        print("\n🧪 Top Methods\n")
        for row in rows:
            name = row.get("name", "Unknown")
            success = row.get("success_count", 0)
            total = row.get("total_count", 0)
            avg = row.get("avg_duration", 0)
            last_success = row.get("last_success", "")
            rate = (success / total * 100) if total else 0
            print(f"  {name}: {rate:.1f}% ({success}/{total}) avg {avg:.2f}s last {last_success}")

    def _cmd_methods_json(self) -> None:
        """Export top methods to JSON."""
        rows = db.get_top_methods(limit=50)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"methods_{timestamp}.json"
        export_path.write_text(json.dumps(rows, indent=2))
        print(f"✅ Methods exported: {export_path}")

    def _cmd_db_health(self) -> None:
        """Show database health summary."""
        stats = db.get_statistics()
        db_size = Config.DB_PATH.stat().st_size if Config.DB_PATH.exists() else 0
        print("\n🗄️  Database Health\n")
        print(f"  Path: {Config.DB_PATH}")
        print(f"  Size: {db_size:,} bytes")
        print(f"  Devices: {stats.get('total_devices', 0)}")
        print(f"  Logs: {stats.get('total_logs', 0)}")
        print(f"  Backups: {stats.get('total_backups', 0)}")
        print(f"  Methods: {stats.get('total_methods', 0)}")
        print(f"  Reports: {stats.get('total_reports', 0)}")

    def _cmd_stats_plus(self) -> None:
        """Show extended statistics."""
        stats = db.get_statistics()
        print("\n📊 VOID EXTENDED STATS\n")
        print(f"  Devices: {stats.get('total_devices', 0)}")
        print(f"  Logs: {stats.get('total_logs', 0)}")
        print(f"  Backups: {stats.get('total_backups', 0)}")
        print(f"  Methods: {stats.get('total_methods', 0)}")
        print(f"  Reports: {stats.get('total_reports', 0)}")

    def _cmd_reports_json(self) -> None:
        """Export report records to JSON."""
        rows = db.get_recent_reports(limit=200)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"reports_{timestamp}.json"
        export_path.write_text(json.dumps(rows, indent=2))
        print(f"✅ Reports exported: {export_path}")

    def _cmd_reports_open(self) -> None:
        """Open reports directory."""
        target = str(Config.REPORTS_DIR)
        if platform.system() == "Darwin":
            SafeSubprocess.run(["open", target])
        elif platform.system() == "Windows":
            SafeSubprocess.run(["explorer", target])
        else:
            SafeSubprocess.run(["xdg-open", target])
        print(f"✅ Opened: {Config.REPORTS_DIR}")

    def _cmd_recent_reports_json(self) -> None:
        """Export recent report records to JSON."""
        rows = db.get_recent_reports(limit=50)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"recent_reports_{timestamp}.json"
        export_path.write_text(json.dumps(rows, indent=2))
        print(f"✅ Recent reports exported: {export_path}")

    def _cmd_config(self) -> None:
        """Show configuration values."""
        print("\n⚙️  Configuration\n")
        print(f"  Version: {Config.VERSION}")
        print(f"  Codename: {Config.CODENAME}")
        print(f"  App Name: {Config.APP_NAME}")
        print(f"  Timeouts: short={Config.TIMEOUT_SHORT}s medium={Config.TIMEOUT_MEDIUM}s long={Config.TIMEOUT_LONG}s")
        print(f"  Auto Backup: {Config.ENABLE_AUTO_BACKUP}")
        print(f"  Monitoring: {Config.ENABLE_MONITORING}")
        print(f"  Analytics: {Config.ENABLE_ANALYTICS}")
        print(f"  Smart Mode: {Config.SMART_ENABLED}")
        print(f"    Smart Auto Device: {Config.SMART_AUTO_DEVICE}")
        print(f"    Smart Prefer Last Device: {Config.SMART_PREFER_LAST_DEVICE}")
        print(f"    Smart Auto Doctor: {Config.SMART_AUTO_DOCTOR}")
        print(f"    Smart Suggestions: {Config.SMART_SUGGESTIONS}")
        print(f"    Smart Safe Guards: {Config.SMART_SAFE_GUARDS}")
        print(f"  Allow Insecure Crypto: {Config.ALLOW_INSECURE_CRYPTO}")

    def _cmd_config_json(self) -> None:
        """Export configuration to JSON."""
        payload = {
            "version": Config.VERSION,
            "codename": Config.CODENAME,
            "app_name": Config.APP_NAME,
            "timeouts": {
                "short": Config.TIMEOUT_SHORT,
                "medium": Config.TIMEOUT_MEDIUM,
                "long": Config.TIMEOUT_LONG,
            },
            "paths": {
                "base": str(Config.BASE_DIR),
                "db": str(Config.DB_PATH),
                "logs": str(Config.LOG_DIR),
                "backups": str(Config.BACKUP_DIR),
                "exports": str(Config.EXPORTS_DIR),
                "cache": str(Config.CACHE_DIR),
                "reports": str(Config.REPORTS_DIR),
                "monitor": str(Config.MONITOR_DIR),
                "scripts": str(Config.SCRIPTS_DIR),
            },
            "features": {
                "auto_backup": Config.ENABLE_AUTO_BACKUP,
                "monitoring": Config.ENABLE_MONITORING,
                "analytics": Config.ENABLE_ANALYTICS,
                "smart": {
                    "enabled": Config.SMART_ENABLED,
                    "auto_device": Config.SMART_AUTO_DEVICE,
                    "prefer_last_device": Config.SMART_PREFER_LAST_DEVICE,
                    "auto_doctor": Config.SMART_AUTO_DOCTOR,
                    "suggestions": Config.SMART_SUGGESTIONS,
                    "safe_guards": Config.SMART_SAFE_GUARDS,
                },
            },
            "security": {
                "max_input_length": Config.MAX_INPUT_LENGTH,
                "allow_insecure_crypto": Config.ALLOW_INSECURE_CRYPTO,
            },
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Config.EXPORTS_DIR / f"config_{timestamp}.json"
        export_path.write_text(json.dumps(payload, indent=2))
        print(f"✅ Config exported: {export_path}")

    def _cmd_smart(self, args: List[str]) -> None:
        """Manage smart features and show recommendations."""
        if not args or args[0] in {"status", "show"}:
            print("\n🤖 Smart Mode\n")
            print(f"  Enabled: {Config.SMART_ENABLED}")
            print(f"  Auto Device: {Config.SMART_AUTO_DEVICE}")
            print(f"  Prefer Last Device: {Config.SMART_PREFER_LAST_DEVICE}")
            print(f"  Auto Doctor: {Config.SMART_AUTO_DOCTOR}")
            print(f"  Suggestions: {Config.SMART_SUGGESTIONS}")
            print(f"  Safe Guards: {Config.SMART_SAFE_GUARDS}")

            devices, errors = SmartAdvisor.snapshot()
            if Config.SMART_SUGGESTIONS:
                suggestions = SmartAdvisor.recommend_actions(devices, errors)
                if suggestions:
                    print("\n  Suggestions:")
                    for suggestion in suggestions:
                        print(f"   • {suggestion}")
            if errors:
                print("\n  Detection issues:")
                for error in SmartAdvisor.format_errors(errors):
                    print(f"   • {error}")
            return

        if len(args) == 1 and args[0] in {"on", "off"}:
            option = "smart_enabled"
            enabled = args[0] == "on"
        elif len(args) >= 2:
            option = args[0].lower()
            value = args[1].lower()
            if value not in {"on", "off"}:
                print("Usage: smart <on|off|auto-device|prefer-last|auto-doctor|suggest|safety> <on|off>")
                return
            enabled = value == "on"
        else:
            print("Usage: smart <on|off|auto-device|prefer-last|auto-doctor|suggest|safety> <on|off>")
            return
        mapping = {
            "smart_enabled": "smart_enabled",
            "auto-device": "smart_auto_device",
            "prefer-last": "smart_prefer_last_device",
            "auto-doctor": "smart_auto_doctor",
            "suggest": "smart_suggestions",
            "safety": "smart_safe_guards",
        }
        if option in {"on", "off"}:
            option = "smart_enabled"
        setting_key = mapping.get(option)
        if not setting_key:
            print("Usage: smart <on|off|auto-device|prefer-last|auto-doctor|suggest|safety> <on|off>")
            return

        current = Config.read_config().get("settings", {})
        current[setting_key] = enabled
        Config.save_settings(current)
        print(f"✅ {setting_key} set to {enabled}")

    def _cmd_launcher(self, args: List[str]) -> None:
        """Install or remove start menu launchers."""
        action = args[0].lower() if args else "install"
        if action not in {"install", "uninstall", "status"}:
            print("Usage: launcher <install|uninstall|status>")
            return

        if action == "install":
            result = install_start_menu()
            for path in result.get("created", []):
                print(f"✅ Created launcher: {path}")
            for error in result.get("errors", []):
                print(f"❌ {error}")
            return

        if action == "uninstall":
            result = uninstall_start_menu()
            for path in result.get("removed", []):
                print(f"✅ Removed launcher: {path}")
            for error in result.get("errors", []):
                print(f"❌ {error}")
            return

        result = launcher_status()
        for path in result.get("present", []):
            print(f"✅ Present: {path}")
        for path in result.get("missing", []):
            print(f"⚠️ Missing: {path}")
        for error in result.get("errors", []):
            print(f"❌ {error}")

    def _cmd_exports_open(self) -> None:
        """Open exports directory."""
        target = str(Config.EXPORTS_DIR)
        if platform.system() == "Darwin":
            SafeSubprocess.run(["open", target])
        elif platform.system() == "Windows":
            SafeSubprocess.run(["explorer", target])
        else:
            SafeSubprocess.run(["xdg-open", target])
        print(f"✅ Opened: {Config.EXPORTS_DIR}")

    def _cmd_db_backup(self) -> None:
        """Backup database to exports."""
        if not Config.DB_PATH.exists():
            print("❌ Database file not found")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Config.EXPORTS_DIR / f"void_db_{timestamp}.db"
        shutil.copy2(Config.DB_PATH, backup_path)
        print(f"✅ Database backup created: {backup_path}")

    def _cmd_analyze(self, args: List[str]) -> None:
        """Analyze device."""
        device_id = self._resolve_device_id(args, "analyze <device_id|smart>")
        if not device_id:
            return

        print("🔍 Analyzing device...")
        result = PerformanceAnalyzer.analyze(device_id)

        print("\n📊 Performance Analysis:\n")
        for key, value in result.items():
            if not isinstance(value, (dict, list)):
                print(f"  {key.replace('_', ' ').title()}: {value}")

    def _cmd_recover(self, args: List[str]) -> None:
        """Recover data."""
        if len(args) < 2:
            if Config.SMART_ENABLED and Config.SMART_AUTO_DEVICE:
                device_id = self._smart_select_device()
                if not device_id or not args:
                    print("Usage: recover <device_id|smart> <contacts|sms>")
                    return
                data_type = args[0]
            else:
                print("Usage: recover <device_id|smart> <contacts|sms>")
                return
        else:
            device_id = self._resolve_device_id([args[0]], "recover <device_id|smart> <contacts|sms>")
            if not device_id:
                return
            data_type = args[1]

        print(f"💾 Recovering {data_type}...")

        if data_type == 'contacts':
            result = DataRecovery.recover_contacts(device_id)
        elif data_type == 'sms':
            result = DataRecovery.recover_sms(device_id)
        else:
            print("❌ Unknown data type")
            return

        if result['success']:
            print(f"✅ Recovered {result['count']} items")
            print(f"   Saved to: {result.get('json_path') or result.get('path')}")
        else:
            print("❌ Recovery failed")

    def _cmd_tweak(self, args: List[str]) -> None:
        """System tweaks."""
        if len(args) < 2:
            print("Usage: tweak <device_id|smart> <dpi|animation|timeout> <value>")
            return
        device_id = self._resolve_device_id([args[0]], "tweak <device_id|smart> <dpi|animation|timeout> <value>")
        if not device_id:
            return
        if len(args) < 3:
            print("Usage: tweak <device_id|smart> <dpi|animation|timeout> <value>")
            return
        tweak_type, value = args[1], args[2]

        if tweak_type == 'dpi':
            success = SystemTweaker.set_dpi(device_id, int(value))
        elif tweak_type == 'animation':
            success = SystemTweaker.set_animation_scale(device_id, float(value))
        elif tweak_type == 'timeout':
            success = SystemTweaker.set_screen_timeout(device_id, int(value))
        else:
            print("❌ Unknown tweak type")
            return

        if success:
            print(f"✅ {tweak_type.title()} updated")
        else:
            print("❌ Tweak failed")

    def _cmd_usb_debug(self, args: List[str]) -> None:
        """Enable or force USB debugging."""
        device_id = self._resolve_device_id(args, "usb-debug <device_id|smart> [force]")
        if not device_id:
            return
        force = len(args) > 1 and args[1].lower() in {"force", "--force", "-f"}

        if force and not self._smart_confirm(f"Force USB debugging on {device_id}?"):
            print("⚠️  Action cancelled.")
            return

        if force:
            result = SystemTweaker.force_usb_debugging(device_id)
        else:
            result = {
                "steps": [
                    {
                        "step": "enable_developer_options",
                        "success": SystemTweaker.enable_developer_options(device_id),
                        "detail": None,
                    },
                    {
                        "step": "enable_usb_debugging_setting",
                        "success": SystemTweaker.enable_usb_debugging(device_id),
                        "detail": None,
                    },
                ]
            }
            result["success"] = all(step["success"] for step in result["steps"])
            result["adb_enabled"] = result["success"]
            result["usb_config"] = None

        status = "✅" if result["success"] else "⚠️"
        print(f"{status} USB debugging {'forced' if force else 'enabled'} for {device_id}")
        for step in result["steps"]:
            icon = "✅" if step["success"] else "❌"
            detail = f" ({step['detail']})" if step.get("detail") else ""
            print(f"  {icon} {step['step']}{detail}")
        if result.get("usb_config"):
            print(f"  🔧 USB config: {result['usb_config']}")

    def _cmd_report(self, args: List[str]) -> None:
        """Generate report."""
        device_id = self._resolve_device_id(args, "report <device_id|smart>")
        if not device_id:
            return

        print("📄 Generating report...")
        result = ReportGenerator.generate_device_report(device_id)

        if result['success']:
            print(f"✅ Report generated: {result['report_name']}")
            print(f"   HTML: {result['html_path']}")
        else:
            print("❌ Report generation failed")

    def _cmd_stats(self) -> None:
        """Show statistics."""
        stats = db.get_statistics()

        print("\n📊 VOID STATISTICS\n")
        print(f"  Total Devices: {stats['total_devices']}")
        print(f"  Total Logs: {stats['total_logs']}")
        print(f"  Total Backups: {stats['total_backups']}")
        print(f"  Methods Tracked: {stats['total_methods']}")
        print(f"  Reports Tracked: {stats.get('total_reports', 0)}")

        if stats.get('top_methods'):
            print("\n  Top Methods:")
            for method in stats['top_methods']:
                rate = (method['success_count'] / method['total_count'] * 100) if method['total_count'] > 0 else 0
                print(f"    • {method['name']}: {rate:.1f}% ({method['success_count']}/{method['total_count']})")

    def _cmd_monitor(self) -> None:
        """Show system monitor."""
        stats = monitor.get_stats()

        if stats:
            print("\n🖥️  SYSTEM MONITOR\n")
            print(f"  CPU: {stats.get('cpu_percent', 0):.1f}%")
            print(f"  Memory: {stats.get('memory_percent', 0):.1f}%")
            print(f"  Disk: {stats.get('disk_usage', 0):.1f}%")
        else:
            print("❌ Monitoring not available (install psutil)")

    def _cmd_logcat(self, args: List[str]) -> None:
        """Start logcat."""
        device_id = self._resolve_device_id(args, "logcat <device_id|smart> [filter_tag]")
        if not device_id:
            return
        filter_tag = args[1] if len(args) > 1 else None

        print("📜 Starting logcat (Ctrl+C to stop)...")
        self.logcat.start(device_id, filter_tag)

        try:
            while True:
                line = self.logcat.read_line()
                if line:
                    print(line.strip())
        except KeyboardInterrupt:
            self.logcat.stop()
            print("\n📜 Logcat stopped")

    def _cmd_execute(self, args: List[str]) -> None:
        """Execute FRP method."""
        if len(args) < 2:
            print("Usage: execute <method> <device_id|smart>")
            return

        method_name = args[0]
        device_id = self._resolve_device_id([args[1]], "execute <method> <device_id|smart>")
        if not device_id:
            return
        if not self._smart_confirm(f"Run method '{method_name}' on {device_id}?"):
            print("⚠️  Action cancelled.")
            return

        print(f"⚡ Executing {method_name}...")

        if method_name not in self.engine.methods:
            print(f"❌ Unknown method: {method_name}")
            return

        result = self.engine.methods[method_name](device_id)

        if result['success']:
            print(f"✅ Success: {result['message']}")
        else:
            print(f"❌ Failed: {result.get('error', result['message'])}")

    def _cmd_files(self, args: List[str]) -> None:
        """File operations."""
        if len(args) < 2:
            print("Usage: files <device_id|smart> <list|pull|push|delete> [path]")
            return

        device_id = self._resolve_device_id([args[0]], "files <device_id|smart> <list|pull|push|delete> [path]")
        if not device_id:
            return
        operation = args[1]

        if operation == 'list':
            path = args[2] if len(args) > 2 else '/sdcard'
            files = FileManager.list_files(device_id, path)

            print(f"\n📁 Files in {path}:\n")
            for file in files[:20]:
                print(f"  {file['permissions']} {file['size']:>10} {file['date']:>20} {file['name']}")

            if len(files) > 20:
                print(f"\n  ... and {len(files) - 20} more")

        elif operation == 'pull':
            if len(args) < 3:
                print("Usage: files <device_id|smart> pull <remote_path> [local_path]")
                return

            local_path = Path(args[3]) if len(args) > 3 else None
            result = FileManager.pull_file(device_id, args[2], local_path)
            if result['success']:
                print(f"✅ File pulled: {result['path']}")
            else:
                print("❌ Pull failed")
        elif operation == 'push':
            if len(args) < 4:
                print("Usage: files <device_id|smart> push <local_path> <remote_path>")
                return

            result = FileManager.push_file(device_id, Path(args[2]), args[3])
            if result:
                print("✅ File pushed")
            else:
                print("❌ Push failed")
        elif operation == 'delete':
            if len(args) < 3:
                print("Usage: files <device_id|smart> delete <remote_path>")
                return

            if not self._smart_confirm(f"Delete remote file {args[2]} on {device_id}?"):
                print("⚠️  Action cancelled.")
                return
            result = FileManager.delete_file(device_id, args[2])
            if result:
                print("✅ File deleted")
            else:
                print("❌ Delete failed")

        else:
            print("❌ Unknown operation")

    def _resolve_device_context(self, device_id: str) -> tuple[dict[str, str], Dict[str, Any] | None]:
        devices, _ = DeviceDetector.detect_all()
        device = None
        for item in devices:
            if item.get("id") == device_id:
                device = item
                break
            if item.get("usb_id") == device_id:
                device = item
                break
            usb_id = str(item.get("id", ""))
            if usb_id.startswith("usb-") and usb_id.replace("usb-", "") == device_id:
                device = item
                break

        if device:
            context = {key: str(value) for key, value in device.items()}
        else:
            context = {"id": device_id, "mode": "unknown"}
        return context, device

    def _cmd_edl_status(self, args: List[str]) -> None:
        """Show EDL mode status and USB IDs."""
        device_id = self._resolve_device_id(args, "edl-status <device_id|smart>")
        if not device_id:
            return
        context, _ = self._resolve_device_context(device_id)
        detection = detect_chipset_for_device(context)

        mode = context.get("mode", "unknown")
        usb_vid = context.get("usb_vid", "-")
        usb_pid = context.get("usb_pid", "-")

        if detection:
            print(
                f"✅ Chipset: {detection.chipset} ({detection.vendor}) "
                f"mode={detection.mode} confidence={detection.confidence:.2f}"
            )
        else:
            print("⚠️ Chipset detection unavailable.")

        print(f"🔌 Device: {device_id} mode={mode} usb_vid={usb_vid} usb_pid={usb_pid}")

        log_edl_event(
            self.logger,
            "status",
            device_id,
            "EDL status checked.",
            success=True if detection else None,
            details={
                "mode": mode,
                "usb_vid": usb_vid,
                "usb_pid": usb_pid,
                "chipset": detection.chipset if detection else "unknown",
            },
        )

    def _cmd_edl_enter(self, args: List[str]) -> None:
        """Enter EDL mode when supported."""
        device_id = self._resolve_device_id(args, "edl-enter <device_id|smart>")
        if not device_id:
            return
        context, _ = self._resolve_device_context(device_id)
        result = enter_chipset_mode(context, "edl")

        if result.success:
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.message}")

        log_edl_event(
            self.logger,
            "enter",
            device_id,
            result.message,
            success=result.success,
            details=result.data,
        )

    def _cmd_edl_flash(self, args: List[str]) -> None:
        """Flash an image via EDL."""
        if len(args) < 3:
            print("Usage: edl-flash <device_id|smart> <loader> <image>")
            return

        device_id = self._resolve_device_id([args[0]], "edl-flash <device_id|smart> <loader> <image>")
        if not device_id:
            return
        loader, image = args[1], args[2]
        loader_path = Path(loader)
        image_path = Path(image)

        if not loader_path.exists():
            print(f"❌ Loader not found: {loader_path}")
            log_edl_event(
                self.logger,
                "flash",
                device_id,
                "Loader not found.",
                success=False,
                details={"loader": str(loader_path)},
            )
            return
        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            log_edl_event(
                self.logger,
                "flash",
                device_id,
                "Image not found.",
                success=False,
                details={"image": str(image_path)},
            )
            return

        if not self._smart_confirm(f"Flash {image_path.name} via EDL on {device_id}?"):
            print("⚠️  Action cancelled.")
            return

        context, _ = self._resolve_device_context(device_id)
        result = edl_flash(context, str(loader_path), str(image_path))

        if result.success:
            print(f"✅ {result.message}")
            if result.data.get("command"):
                print(f"   Command: {result.data['command']}")
        else:
            print(f"❌ {result.message}")

        log_edl_event(
            self.logger,
            "flash",
            device_id,
            result.message,
            success=result.success,
            details=result.data,
        )

    def _cmd_edl_dump(self, args: List[str]) -> None:
        """Dump a partition via EDL when supported."""
        if len(args) < 2:
            print("Usage: edl-dump <device_id|smart> <partition>")
            return

        device_id = self._resolve_device_id([args[0]], "edl-dump <device_id|smart> <partition>")
        if not device_id:
            return
        partition = args[1]
        context, _ = self._resolve_device_context(device_id)
        result = edl_dump(context, partition)

        if result.success:
            print(f"✅ {result.message}")
            if result.data.get("output"):
                print(f"   Output: {result.data['output']}")
        else:
            print(f"❌ {result.message}")

        log_edl_event(
            self.logger,
            "dump",
            device_id,
            result.message,
            success=result.success,
            details=result.data,
        )

    def _cmd_edl_detect(self) -> None:
        """Detect EDL devices using USB scanning."""
        result = detect_edl_devices()
        self._print_toolkit_result(result)

    def _cmd_edl_programmers(self) -> None:
        """List firehose programmers."""
        result = list_firehose_programmers()
        self._print_toolkit_result(result)

    def _cmd_edl_partitions(self, args: List[str]) -> None:
        """List partition map via ADB or EDL tooling."""
        if len(args) < 1:
            print("Usage: edl-partitions <device_id|smart> [loader]")
            return
        device_id = self._resolve_device_id([args[0]], "edl-partitions <device_id|smart> [loader]")
        if not device_id:
            return
        loader = args[1] if len(args) > 1 else None
        adb_result = list_partitions_via_adb(device_id)
        if adb_result.success:
            self._print_toolkit_result(adb_result)
            return
        edl_result = read_partition_table(loader)
        self._print_toolkit_result(edl_result)

    def _cmd_edl_backup(self, args: List[str]) -> None:
        """Backup a partition via EDL."""
        if len(args) < 2:
            print("Usage: edl-backup <device_id|smart> <partition>")
            return
        device_id = self._resolve_device_id([args[0]], "edl-backup <device_id|smart> <partition>")
        if not device_id:
            return
        partition = args[1]
        result = backup_partition({"id": device_id}, partition)
        self._print_toolkit_result(result)

    def _cmd_edl_restore(self, args: List[str]) -> None:
        """Restore a partition via EDL."""
        if len(args) < 3:
            print("Usage: edl-restore <device_id|smart> <loader> <image>")
            return
        device_id = self._resolve_device_id([args[0]], "edl-restore <device_id|smart> <loader> <image>")
        if not device_id:
            return
        loader = args[1]
        image = args[2]
        result = restore_partition({"id": device_id}, loader, image)
        self._print_toolkit_result(result)

    def _cmd_edl_sparse(self, args: List[str]) -> None:
        """Convert sparse images."""
        if len(args) < 3:
            print("Usage: edl-sparse <to-raw|to-sparse> <source> <dest>")
            return
        direction = args[0].lower()
        to_sparse = direction == "to-sparse"
        if direction not in {"to-raw", "to-sparse"}:
            print("Usage: edl-sparse <to-raw|to-sparse> <source> <dest>")
            return
        result = convert_sparse_image(Path(args[1]), Path(args[2]), to_sparse)
        self._print_toolkit_result(result)

    def _cmd_edl_profile(self, args: List[str]) -> None:
        """Manage EDL profiles."""
        if not args:
            print("Usage: edl-profile <list|add|delete> [name] [json]")
            return
        action = args[0].lower()
        if action == "list":
            profiles = load_profiles()
            result = ToolkitResult(
                success=True,
                message="EDL profiles loaded.",
                data={"profiles": profiles},
            )
            self._print_toolkit_result(result)
            return
        if action == "add" and len(args) >= 3:
            name = args[1]
            try:
                profile = json.loads(" ".join(args[2:]))
            except json.JSONDecodeError:
                print("Profile data must be valid JSON.")
                return
            result = save_profile(name, profile)
            self._print_toolkit_result(result)
            return
        if action == "delete" and len(args) == 2:
            result = delete_profile(args[1])
            self._print_toolkit_result(result)
            return
        print("Usage: edl-profile <list|add|delete> [name] [json]")

    def _cmd_edl_verify(self, args: List[str]) -> None:
        """Verify image hash."""
        if len(args) < 1:
            print("Usage: edl-verify <file> [sha256]")
            return
        expected = args[1] if len(args) > 1 else None
        result = verify_hash(Path(args[0]), expected)
        self._print_toolkit_result(result)

    def _cmd_edl_unbrick(self, args: List[str]) -> None:
        """Generate an unbrick checklist."""
        loader = args[0] if args else None
        result = edl_unbrick_plan(loader)
        self._print_toolkit_result(result)

    def _cmd_edl_notes(self, args: List[str]) -> None:
        """Show device-specific notes."""
        vendor = args[0] if args else None
        result = device_notes(vendor)
        self._print_toolkit_result(result)

    def _cmd_edl_reboot(self, args: List[str]) -> None:
        """Reboot to a target mode."""
        if len(args) < 2:
            print("Usage: edl-reboot <device_id|smart> <edl|fastboot|recovery|bootloader|system>")
            return
        device_id = self._resolve_device_id([args[0]], "edl-reboot <device_id|smart> <target>")
        if not device_id:
            return
        target = args[1]
        result = reboot_device(device_id, target)
        self._print_toolkit_result(result)

    def _cmd_edl_log(self) -> None:
        """Capture EDL log artifacts."""
        result = capture_edl_log()
        self._print_toolkit_result(result)

    def _cmd_boot_extract(self, args: List[str]) -> None:
        """Extract boot image contents."""
        if len(args) < 1:
            print("Usage: boot-extract <boot.img>")
            return
        result = extract_boot_image(Path(args[0]))
        self._print_toolkit_result(result)

    def _cmd_magisk_patch(self, args: List[str]) -> None:
        """Stage a Magisk patch workflow."""
        if len(args) < 2:
            print("Usage: magisk-patch <device_id|smart> <boot.img>")
            return
        device_id = self._resolve_device_id([args[0]], "magisk-patch <device_id|smart> <boot.img>")
        if not device_id:
            return
        result = stage_magisk_patch(device_id, Path(args[1]))
        self._print_toolkit_result(result)

    def _cmd_magisk_pull(self, args: List[str]) -> None:
        """Pull Magisk patched image."""
        if len(args) < 1:
            print("Usage: magisk-pull <device_id|smart> [output_dir]")
            return
        device_id = self._resolve_device_id([args[0]], "magisk-pull <device_id|smart> [output_dir]")
        if not device_id:
            return
        output_dir = Path(args[1]) if len(args) > 1 else Config.EXPORTS_DIR
        result = pull_magisk_patched(device_id, output_dir)
        self._print_toolkit_result(result)

    def _cmd_twrp_verify(self, args: List[str]) -> None:
        """Verify a TWRP image matches device codename."""
        if len(args) < 2:
            print("Usage: twrp-verify <device_id|smart> <twrp.img>")
            return
        device_id = self._resolve_device_id([args[0]], "twrp-verify <device_id|smart> <twrp.img>")
        if not device_id:
            return
        result = verify_twrp_image(device_id, Path(args[1]))
        self._print_toolkit_result(result)

    def _cmd_twrp_flash(self, args: List[str]) -> None:
        """Flash or boot TWRP recovery via fastboot."""
        if len(args) < 2:
            print("Usage: twrp-flash <device_id|smart> <twrp.img> [boot]")
            return
        device_id = self._resolve_device_id([args[0]], "twrp-flash <device_id|smart> <twrp.img>")
        if not device_id:
            return
        boot_only = len(args) > 2 and args[2].lower() == "boot"
        result = flash_recovery(device_id, Path(args[1]), boot_only=boot_only)
        self._print_toolkit_result(result)

    def _cmd_root_verify(self, args: List[str]) -> None:
        """Verify root access via ADB."""
        if len(args) < 1:
            print("Usage: root-verify <device_id|smart>")
            return
        device_id = self._resolve_device_id([args[0]], "root-verify <device_id|smart>")
        if not device_id:
            return
        result = verify_root(device_id)
        self._print_toolkit_result(result)

    def _cmd_safety_check(self, args: List[str]) -> None:
        """Run safety checklist for device operations."""
        if len(args) < 1:
            print("Usage: safety-check <device_id|smart>")
            return
        device_id = self._resolve_device_id([args[0]], "safety-check <device_id|smart>")
        if not device_id:
            return
        result = safety_check(device_id)
        self._print_toolkit_result(result)

    def _cmd_rollback(self, args: List[str]) -> None:
        """Rollback a partition flash."""
        if len(args) < 3:
            print("Usage: rollback <device_id|smart> <partition> <image>")
            return
        device_id = self._resolve_device_id([args[0]], "rollback <device_id|smart> <partition> <image>")
        if not device_id:
            return
        result = rollback_flash(device_id, args[1], Path(args[2]))
        self._print_toolkit_result(result)

    def _cmd_compat_matrix(self) -> None:
        """Show compatibility matrix."""
        result = compatibility_matrix()
        self._print_toolkit_result(result)

    def _cmd_testpoint_guide(self, args: List[str]) -> None:
        """Show test-point guidance references."""
        device_id = self._resolve_device_id(args, "testpoint-guide <device_id|smart>")
        if not device_id:
            return
        context, _ = self._resolve_device_context(device_id)
        detection = detect_chipset_for_device(context)
        chipset = detection.chipset if detection else "Unknown"

        guides = {
            "Qualcomm": {
                "summary": "Qualcomm devices can often enter EDL via test-point short.",
                "references": [
                    "https://github.com/bkerler/edl",
                    "https://forum.xda-developers.com/",
                ],
            },
            "MediaTek": {
                "summary": "MediaTek bootrom/preloader modes may require test-point access.",
                "references": [
                    "https://github.com/bkerler/mtkclient",
                    "https://forum.xda-developers.com/",
                ],
            },
            "Samsung Exynos": {
                "summary": "Samsung download mode access varies by model and requires OEM docs.",
                "references": [
                    "https://forum.xda-developers.com/",
                ],
            },
        }

        guide = guides.get(
            chipset,
            {"summary": "Use model-specific guides for test-point access.", "references": []},
        )

        print(f"📌 Test-point guidance for {chipset}:")
        print(f"   {guide['summary']}")
        print("   Suggested references:")
        if guide["references"]:
            for ref in guide["references"]:
                print(f"   - {ref}")
        else:
            print("   - Search for '<model> test point' on trusted forums.")

        log_edl_event(
            self.logger,
            "testpoint-guide",
            device_id,
            "Test-point guidance displayed.",
            success=True,
            details={"chipset": chipset},
        )

    def _cmd_search(self, args: List[str]) -> None:
        """Search commands by keyword."""
        if not args:
            print("Usage: search <keyword>")
            print("Example: search backup")
            return

        keyword = " ".join(args).strip().lower()
        matches = []
        for command in self.command_catalog.values():
            haystack = " ".join(
                [command.name, command.summary, command.usage, " ".join(command.aliases), command.category]
            ).lower()
            if keyword in haystack:
                matches.append(command)

        if not matches:
            print(f"❌ No commands matched '{keyword}'.")
            return

        print(f"\n🔎 Matches for '{keyword}':\n")
        for command in sorted(matches, key=lambda item: (item.category, item.name)):
            alias_text = f" (aliases: {', '.join(command.aliases)})" if command.aliases else ""
            print(f"  {command.name} — {command.summary}{alias_text}")

    def _cmd_help(self, args: Optional[List[str]] = None) -> None:
        """Show help."""
        args = args or []
        if args:
            query = args[0].lower()
            resolved = self.command_aliases.get(query, query)
            command = self.command_catalog.get(resolved)
            if not command:
                print(f"❌ Unknown command '{query}'.")
                print("Tip: use 'search <keyword>' to discover commands.")
                return

            print(f"\n📘 Help: {command.name}\n")
            print(f"Summary: {command.summary}")
            print(f"Usage:   {command.usage}")
            if command.aliases:
                print(f"Aliases: {', '.join(command.aliases)}")
            if command.examples:
                print("\nExamples:")
                for example in command.examples:
                    print(f"  {example}")
            return

        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                   VOID - HELP                                ║
╚══════════════════════════════════════════════════════════════╝

📋 AVAILABLE COMMANDS:

Tip: Use 'help <command>' for detailed usage or 'search <keyword>' to find commands.

DEVICE MANAGEMENT:
  devices                          - List all connected devices
  info <device_id|smart>           - Show detailed device info
  summary                          - Show a short device summary
  
BACKUP & DATA:
  backup <device_id|smart>         - Create automated backup
  recover <device_id|smart> <type> - Recover data (contacts/sms)
  screenshot <device_id|smart>     - Take screenshot
  
APP MANAGEMENT:
  apps <device_id|smart> [filter]  - List apps (system/user/all)
  
FILE OPERATIONS:
  files <device_id|smart> list [path]    - List files
  files <device_id|smart> pull <path> [local] - Pull file from device
  files <device_id|smart> push <local> <remote> - Push file to device
  files <device_id|smart> delete <path>  - Delete file on device
  
ANALYSIS:
  analyze <device_id|smart>        - Performance analysis
  display-diagnostics <device_id|smart>  - Display + framebuffer diagnostics
  report <device_id|smart>         - Generate full report
  logcat <device_id|smart> [tag]   - View real-time logs
  
TWEAKS:
  tweak <device_id|smart> <type> <value> - System tweaks
    Types: dpi, animation, timeout
  usb-debug <device_id|smart> [force]    - Enable or force USB debugging

FRP BYPASS:
  execute <method> <device_id|smart>     - Execute bypass method
    Methods: adb_shell_reset, fastboot_erase, etc.

ADVANCED TOOLBOX:
  advanced                         - Show advanced Android tooling overview

EDL & TEST-POINT:
  edl-status <device_id|smart>           - Detect EDL mode + USB VID/PID
  edl-enter <device_id|smart>            - Enter EDL mode (if supported)
  edl-flash <device_id|smart> <loader> <image> - Flash via EDL (chipset-specific)
  edl-dump <device_id|smart> <partition> - Dump a partition via EDL
  edl-detect                            - Scan USB for EDL devices
  edl-programmers                       - List available firehose programmers
  edl-partitions <device_id|smart> [loader] - Show partition map
  edl-backup <device_id|smart> <partition> - Backup partition via EDL
  edl-restore <device_id|smart> <loader> <image> - Restore partition via EDL
  edl-sparse <to-raw|to-sparse> <source> <dest> - Convert sparse images
  edl-profile <list|add|delete>          - Manage EDL profiles
  edl-verify <file> [sha256]             - Verify image hash
  edl-unbrick [loader]                   - Show unbrick checklist
  edl-notes [vendor]                     - Show device-specific notes
  edl-reboot <device_id|smart> <target>  - Reboot to target mode
  edl-log                               - Capture EDL workflow logs
  boot-extract <boot.img>                - Extract boot image contents
  magisk-patch <device_id|smart> <boot.img> - Stage Magisk patch workflow
  magisk-pull <device_id|smart> [output_dir] - Pull Magisk patched image
  twrp-verify <device_id|smart> <twrp.img> - Validate TWRP image
  twrp-flash <device_id|smart> <twrp.img> [boot] - Flash/boot TWRP
  root-verify <device_id|smart>          - Verify root access
  safety-check <device_id|smart>         - Run safety checklist
  rollback <device_id|smart> <partition> <image> - Roll back a flash
  compat-matrix                          - Show EDL compatibility matrix
  testpoint-guide <device_id|smart>      - Show test-point references
  
SYSTEM:
  stats                            - Show suite statistics
  monitor                          - Show system monitor
  version                          - Show suite version
  paths                            - Show local data paths
  menu                             - Launch interactive menu
  netcheck                         - Check internet connectivity
  bootstrap [force]                - Install bundled platform tools
  adb                              - Check ADB availability
  clear-cache                      - Clear local cache
  doctor                           - Run quick system checks
  logs                             - List recent log files
  backups                          - List recent backups
  reports                          - List recent reports
  exports                          - List recent exports
  devices-json                     - Export devices to JSON
  stats-json                       - Export stats to JSON
  logtail [lines]                  - Tail recent log lines
  cleanup-exports                  - Remove old exports
  cleanup-backups                  - Remove old backups
  cleanup-reports                  - Remove old reports
  env                              - Show environment info
  recent-logs [count]              - Show recent log entries
  recent-backups [count]           - Show recent backup records
  recent-reports [count]           - Show recent report records
  logs-json                        - Export logs to JSON
  logs-export <json|csv> [filters] - Export filtered logs to JSON/CSV
  backups-json                     - Export backups to JSON
  latest-report                    - Show latest report paths
  recent-devices [count]           - Show recent devices
  methods [count]                  - Show top methods
  methods-json                     - Export top methods to JSON
  db-health                        - Show database health summary
  stats-plus                       - Show extended stats
  reports-json                     - Export reports to JSON
  smart [status|on|off]            - Show or toggle smart features
  launcher <install|uninstall|status> - Manage start menu launchers
  reports-open                     - Open reports directory
  recent-reports-json              - Export recent reports to JSON
  config                           - Show configuration values
  config-json                      - Export configuration to JSON
  exports-open                     - Open exports directory
  db-backup                        - Backup database to exports
  plugins                          - List available plugins
  plugin <id> [args]               - Run a plugin by id
  search <keyword>                 - Search commands by keyword
  help                             - Show this help
  exit                             - Exit suite

🎯 EXAMPLES:

  void> devices
  void> info emulator-5554
  void> summary
  void> backup emulator-5554
  void> screenshot emulator-5554
  void> apps emulator-5554 user
  void> analyze emulator-5554
  void> display-diagnostics emulator-5554
  void> recover emulator-5554 contacts
  void> tweak emulator-5554 dpi 320
  void> usb-debug emulator-5554 force
  void> report emulator-5554
  void> execute adb_shell_reset emulator-5554
  void> edl-status usb-05c6:9008
  void> edl-enter emulator-5554
  void> edl-flash usb-05c6:9008 firehose.mbn boot.img
  void> edl-dump usb-05c6:9008 userdata
  void> edl-detect
  void> edl-programmers
  void> edl-partitions emulator-5554
  void> edl-backup usb-05c6:9008 modem
  void> edl-restore usb-05c6:9008 firehose.mbn boot.img
  void> edl-sparse to-raw system.img system.raw.img
  void> edl-profile list
  void> edl-verify boot.img
  void> edl-unbrick firehose.mbn
  void> edl-notes qualcomm
  void> edl-reboot emulator-5554 edl
  void> edl-log
  void> boot-extract boot.img
  void> magisk-patch emulator-5554 boot.img
  void> magisk-pull emulator-5554
  void> twrp-verify emulator-5554 twrp.img
  void> twrp-flash emulator-5554 twrp.img
  void> root-verify emulator-5554
  void> safety-check emulator-5554
  void> rollback emulator-5554 boot boot_backup.img
  void> compat-matrix
  void> testpoint-guide usb-05c6:9008
  void> menu
  void> version
  void> paths
  void> netcheck
  void> adb
  void> doctor
  void> logtail 100
  void> recent-logs 25
  void> logs-export json level=error since=2024-01-01
  void> recent-backups 10
  void> recent-reports 10
  void> methods 5
  void> reports-open
  void> config-json
  void> plugins
  void> plugin system-info
  void> search backup
  void> help devices

💡 TIP: All commands work automatically with no setup required!

╚══════════════════════════════════════════════════════════════╝
"""
        print(help_text)

    def _cmd_plugins(self) -> None:
        """List available plugins."""
        plugins = self.plugin_registry.list_metadata()

        if not plugins:
            print("No plugins registered.")
            return

        if self.console:
            table = Table(title="Available Plugins")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Version", style="magenta")
            table.add_column("Tags", style="blue")
            for plugin in plugins:
                table.add_row(
                    plugin.id,
                    plugin.name,
                    plugin.description,
                    plugin.version,
                    ", ".join(plugin.tags) if plugin.tags else "-",
                )
            self.console.print(table)
            return

        print("\n🔌 Available Plugins:")
        for plugin in plugins:
            tags = ", ".join(plugin.tags) if plugin.tags else "-"
            print(f"  • {plugin.id} - {plugin.name} ({plugin.version}) [{tags}]")
            print(f"      {plugin.description}")

    def _cmd_plugin(self, args: List[str]) -> None:
        """Run a plugin by id."""
        if not args:
            print("Usage: plugin <id> [args]")
            return

        plugin_id = args[0]
        plugin_args = args[1:]
        context = PluginContext(mode="cli", emit=print)

        try:
            result = self.plugin_registry.run(plugin_id, context, plugin_args)
        except KeyError as exc:
            print(f"❌ {exc}")
            return
        except Exception as exc:
            print(f"❌ Plugin failed: {exc}")
            return

        print(f"✅ {result.message}")
        if result.data:
            print(json.dumps(result.data, indent=2))


__all__ = ["CLI", "RICH_AVAILABLE"]

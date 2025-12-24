"""Command line interface."""
from __future__ import annotations

import sys
from typing import List

from .apps import AppManager
from .backup import AutoBackup
from .database import db
from .device import DeviceDetector
from .files import FileManager
from .frp import FRPEngine
from .logcat import LogcatViewer
from .monitor import monitor
from .performance import PerformanceAnalyzer
from .recovery import DataRecovery
from .report import ReportGenerator
from .screen import ScreenCapture
from .tweaks import SystemTweaker
from .ui import Console, HELP_TEXT, RICH_AVAILABLE, Table, build_banner
from .config import Config


class CLI:
    """Enhanced CLI with all features"""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.engine = FRPEngine()
        self.logcat = LogcatViewer()

        # Start monitoring
        monitor.start()

    def run(self) -> None:
        """Run CLI"""
        self._print_banner()

        while True:
            try:
                cmd = input("\nvoid> ").strip()
                if not cmd:
                    continue

                parts = cmd.split()
                command = parts[0].lower()
                args = parts[1:]

                # Route commands
                commands = {
                    "devices": self._cmd_devices,
                    "info": lambda: self._cmd_info(args),
                    "backup": lambda: self._cmd_backup(args),
                    "screenshot": lambda: self._cmd_screenshot(args),
                    "apps": lambda: self._cmd_apps(args),
                    "files": lambda: self._cmd_files(args),
                    "analyze": lambda: self._cmd_analyze(args),
                    "recover": lambda: self._cmd_recover(args),
                    "tweak": lambda: self._cmd_tweak(args),
                    "report": lambda: self._cmd_report(args),
                    "stats": self._cmd_stats,
                    "monitor": self._cmd_monitor,
                    "logcat": lambda: self._cmd_logcat(args),
                    "execute": lambda: self._cmd_execute(args),
                    "help": self._cmd_help,
                    "exit": lambda: sys.exit(0),
                }

                if command in commands:
                    commands[command]()
                else:
                    print(f"Unknown command: {command}")

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as exc:
                print(f"Error: {exc}")

    def _print_banner(self) -> None:
        """Print banner"""
        features_count = 200  # Total automated features

        print(build_banner(Config.VERSION, Config.CODENAME, features_count))

    def _cmd_devices(self) -> None:
        """List devices"""
        devices = DeviceDetector.detect_all()

        if not devices:
            print("❌ No devices detected")
            return

        if self.console:
            table = Table(title="Connected Devices")
            table.add_column("ID", style="cyan")
            table.add_column("Mode", style="green")
            table.add_column("Manufacturer", style="yellow")
            table.add_column("Model", style="blue")
            table.add_column("Android", style="magenta")

            for device in devices:
                table.add_row(
                    device.get("id", "Unknown"),
                    device.get("mode", "Unknown"),
                    device.get("manufacturer", "Unknown"),
                    device.get("model", "Unknown"),
                    device.get("android_version", "Unknown"),
                )

            self.console.print(table)
        else:
            print("\n📱 Connected Devices:")
            for device in devices:
                print(f"  • {device.get('id')} - {device.get('manufacturer')} {device.get('model')}")

    def _cmd_backup(self, args: List[str]) -> None:
        """Create backup"""
        if len(args) < 1:
            print("Usage: backup <device_id>")
            return

        result = AutoBackup.create_backup(args[0])
        if result["success"]:
            print(f"✅ Backup created: {result['backup_name']}")
            print(f"   Items: {', '.join(result['items'])}")
            print(f"   Size: {result['size']:,} bytes")
        else:
            print("❌ Backup failed")

    def _cmd_screenshot(self, args: List[str]) -> None:
        """Take screenshot"""
        if len(args) < 1:
            print("Usage: screenshot <device_id>")
            return

        result = ScreenCapture.take_screenshot(args[0])
        if result["success"]:
            print(f"✅ Screenshot saved: {result['path']}")
        else:
            print("❌ Screenshot failed")

    def _cmd_apps(self, args: List[str]) -> None:
        """List apps"""
        if len(args) < 1:
            print("Usage: apps <device_id> [system|user|all]")
            return

        filter_type = args[1] if len(args) > 1 else "all"
        apps = AppManager.list_apps(args[0], filter_type)

        print(f"\n📦 {filter_type.title()} Apps ({len(apps)}):")
        for app in apps[:20]:
            print(f"  • {app['package']}")

        if len(apps) > 20:
            print(f"  ... and {len(apps) - 20} more")

    def _cmd_info(self, args: List[str]) -> None:
        """Show device info"""
        if len(args) < 1:
            print("Usage: info <device_id>")
            return

        devices = DeviceDetector.detect_all()
        device = next((d for d in devices if d["id"] == args[0]), None)

        if device:
            print(f"\n📱 Device Information: {args[0]}\n")
            for key, value in device.items():
                if not isinstance(value, dict):
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        else:
            print("❌ Device not found")

    def _cmd_analyze(self, args: List[str]) -> None:
        """Analyze device"""
        if len(args) < 1:
            print("Usage: analyze <device_id>")
            return

        print("🔍 Analyzing device...")
        result = PerformanceAnalyzer.analyze(args[0])

        print("\n📊 Performance Analysis:\n")
        for key, value in result.items():
            if not isinstance(value, (dict, list)):
                print(f"  {key.replace('_', ' ').title()}: {value}")

    def _cmd_recover(self, args: List[str]) -> None:
        """Recover data"""
        if len(args) < 2:
            print("Usage: recover <device_id> <contacts|sms>")
            return

        device_id, data_type = args[0], args[1]

        print(f"💾 Recovering {data_type}...")

        if data_type == "contacts":
            result = DataRecovery.recover_contacts(device_id)
        elif data_type == "sms":
            result = DataRecovery.recover_sms(device_id)
        else:
            print("❌ Unknown data type")
            return

        if result["success"]:
            print(f"✅ Recovered {result['count']} items")
            print(f"   Saved to: {result.get('json_path') or result.get('path')}")
        else:
            print("❌ Recovery failed")

    def _cmd_tweak(self, args: List[str]) -> None:
        """System tweaks"""
        if len(args) < 3:
            print("Usage: tweak <device_id> <dpi|animation|timeout> <value>")
            return

        device_id, tweak_type, value = args[0], args[1], args[2]

        if tweak_type == "dpi":
            success = SystemTweaker.set_dpi(device_id, int(value))
        elif tweak_type == "animation":
            success = SystemTweaker.set_animation_scale(device_id, float(value))
        elif tweak_type == "timeout":
            success = SystemTweaker.set_screen_timeout(device_id, int(value))
        else:
            print("❌ Unknown tweak type")
            return

        if success:
            print(f"✅ {tweak_type.title()} updated")
        else:
            print("❌ Tweak failed")

    def _cmd_report(self, args: List[str]) -> None:
        """Generate report"""
        if len(args) < 1:
            print("Usage: report <device_id>")
            return

        print("📄 Generating report...")
        result = ReportGenerator.generate_device_report(args[0])

        if result["success"]:
            print(f"✅ Report generated: {result['report_name']}")
            print(f"   HTML: {result['html_path']}")
        else:
            print("❌ Report generation failed")

    def _cmd_stats(self) -> None:
        """Show statistics"""
        stats = db.get_statistics()

        print("\n📊 VOID SUITE STATISTICS\n")
        print(f"  Total Devices: {stats['total_devices']}")
        print(f"  Total Logs: {stats['total_logs']}")
        print(f"  Total Backups: {stats['total_backups']}")
        print(f"  Methods Tracked: {stats['total_methods']}")

        if stats.get("top_methods"):
            print("\n  Top Methods:")
            for method in stats["top_methods"]:
                rate = (method["success_count"] / method["total_count"] * 100) if method["total_count"] > 0 else 0
                print(
                    f"    • {method['name']}: {rate:.1f}% ({method['success_count']}/{method['total_count']})"
                )

    def _cmd_monitor(self) -> None:
        """Show system monitor"""
        stats = monitor.get_stats()

        if stats:
            print("\n🖥️  SYSTEM MONITOR\n")
            print(f"  CPU: {stats.get('cpu_percent', 0):.1f}%")
            print(f"  Memory: {stats.get('memory_percent', 0):.1f}%")
            print(f"  Disk: {stats.get('disk_usage', 0):.1f}%")
        else:
            print("❌ Monitoring not available (install psutil)")

    def _cmd_logcat(self, args: List[str]) -> None:
        """Start logcat"""
        if len(args) < 1:
            print("Usage: logcat <device_id> [filter_tag]")
            return

        device_id = args[0]
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
        """Execute FRP method"""
        if len(args) < 2:
            print("Usage: execute <method> <device_id>")
            return

        method_name, device_id = args[0], args[1]

        print(f"⚡ Executing {method_name}...")

        if method_name not in self.engine.methods:
            print(f"❌ Unknown method: {method_name}")
            return

        result = self.engine.methods[method_name](device_id)

        if result["success"]:
            print(f"✅ Success: {result['message']}")
        else:
            print(f"❌ Failed: {result.get('error', result['message'])}")

    def _cmd_files(self, args: List[str]) -> None:
        """File operations"""
        if len(args) < 2:
            print("Usage: files <device_id> <list|pull|push> [path]")
            return

        device_id, operation = args[0], args[1]

        if operation == "list":
            path = args[2] if len(args) > 2 else "/sdcard"
            files = FileManager.list_files(device_id, path)

            print(f"\n📁 Files in {path}:\n")
            for file in files[:20]:
                print(f"  {file['permissions']} {file['size']:>10} {file['date']:>20} {file['name']}")

            if len(files) > 20:
                print(f"\n  ... and {len(files) - 20} more")

        elif operation == "pull":
            if len(args) < 3:
                print("Usage: files <device_id> pull <remote_path>")
                return

            result = FileManager.pull_file(device_id, args[2])
            if result["success"]:
                print(f"✅ File pulled: {result['path']}")
            else:
                print("❌ Pull failed")

        else:
            print("❌ Unknown operation")

    def _cmd_help(self) -> None:
        """Show help"""
        print(HELP_TEXT)

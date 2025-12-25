"""
VOID ENTRY POINT

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import argparse
import json
import sys

from .cli import CLI
from .config import Config
from .core.backup import AutoBackup
from .core.device import DeviceDetector
from .core.monitor import monitor
from .core.performance import PerformanceAnalyzer
from .core.report import ReportGenerator
from .gui import run_gui
from .terms import ensure_terms_acceptance_cli


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=f"Void v{Config.VERSION} - Ultimate Android Toolkit"
    )

    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--gui', action='store_true', help='Launch GUI')
    parser.add_argument('--devices', action='store_true', help='List devices')
    parser.add_argument('--backup', type=str, help='Backup device')
    parser.add_argument('--analyze', type=str, help='Analyze device')
    parser.add_argument('--report', type=str, help='Generate report')

    args = parser.parse_args()

    if args.version:
        print(f"Void v{Config.VERSION} - {Config.CODENAME}")
        print("200+ Automated Features")
        return

    Config.setup()

    if not ensure_terms_acceptance_cli():
        return

    if args.gui:
        run_gui()
        return

    if args.devices:
        devices = DeviceDetector.detect_all()
        print("Connected Devices:")
        for device in devices:
            print(f"  • {device.get('id')} - {device.get('manufacturer')} {device.get('model')}")
        return

    if args.backup:
        result = AutoBackup.create_backup(args.backup)
        print(f"Backup: {'Success' if result['success'] else 'Failed'}")
        return

    if args.analyze:
        result = PerformanceAnalyzer.analyze(args.analyze)
        print(f"Analysis: {json.dumps(result, indent=2)}")
        return

    if args.report:
        result = ReportGenerator.generate_device_report(args.report)
        print(f"Report: {result.get('html_path', 'Failed')}")
        return

    cli = CLI()
    cli.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        monitor.stop()
        sys.exit(0)
    except Exception as exc:
        print(f"\n💀 Critical Error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

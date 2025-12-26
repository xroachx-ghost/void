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
from .logging import configure_logging, get_logger
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

    Config.setup()
    configure_logging()
    logger = get_logger(__name__)

    if args.version:
        logger.info(
            "Void version",
            extra={"category": "startup", "device_id": "-", "method": "-"},
        )
        logger.info(
            f"Void v{Config.VERSION} - {Config.CODENAME}",
            extra={"category": "startup", "device_id": "-", "method": "-"},
        )
        logger.info(
            "200+ Automated Features",
            extra={"category": "startup", "device_id": "-", "method": "-"},
        )
        return

    if not ensure_terms_acceptance_cli():
        return

    if args.gui:
        run_gui()
        return

    if args.devices:
    devices, _ = DeviceDetector.detect_all()
        logger.info(
            "Connected Devices:",
            extra={"category": "devices", "device_id": "-", "method": "-"},
        )
        for device in devices:
            logger.info(
                f"  • {device.get('id')} - {device.get('manufacturer')} {device.get('model')}",
                extra={"category": "devices", "device_id": device.get("id", "-"), "method": "-"},
            )
        return

    if args.backup:
        result = AutoBackup.create_backup(args.backup)
        logger.info(
            f"Backup: {'Success' if result['success'] else 'Failed'}",
            extra={"category": "backup", "device_id": args.backup, "method": "-"},
        )
        return

    if args.analyze:
        result = PerformanceAnalyzer.analyze(args.analyze)
        logger.info(
            f"Analysis: {json.dumps(result, indent=2)}",
            extra={"category": "analysis", "device_id": args.analyze, "method": "-"},
        )
        return

    if args.report:
        result = ReportGenerator.generate_device_report(args.report)
        logger.info(
            f"Report: {result.get('html_path', 'Failed')}",
            extra={"category": "report", "device_id": args.report, "method": "-"},
        )
        return

    cli = CLI()
    cli.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger = get_logger(__name__)
        logger.info("Goodbye!", extra={"category": "shutdown", "device_id": "-", "method": "-"})
        monitor.stop()
        sys.exit(0)
    except Exception as exc:
        logger = get_logger(__name__)
        logger.exception(
            f"Critical Error: {exc}",
            extra={"category": "crash", "device_id": "-", "method": "-"},
        )
        import traceback
        traceback.print_exc()
        sys.exit(1)

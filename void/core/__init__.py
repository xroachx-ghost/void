"""Core functionality for Void."""

"""
Core module initialization.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import socket
import subprocess
import urllib

from .apps import AppManager
from .authorized_debug_enable import (
    enable_debugging_settings,
    grant_debugging_authorization,
    restart_adbd,
)
from .authorized_device_auditor import AuthorizedDeviceAuditor
from .backup import AutoBackup
from .data_recovery import DataRecovery
from .database import Database, db
from .display import DisplayAnalyzer
from .device import DeviceDetector
from .firmware_integrity import (
    dump_partition_via_adb,
    flash_signed_firmware,
    hash_partition_via_adb,
)
from .frp import FRPEngine
from .logcat import LogcatViewer
from .logging import Logger, logger
from .monitor import PSUTIL_AVAILABLE, SystemMonitor, monitor
from .network import NetworkAnalyzer, NetworkTools
from .performance import PerformanceAnalyzer
from .recovery_control import (
    reboot_to_download_mode,
    reboot_to_edl,
    reboot_to_fastboot,
    reboot_to_recovery,
)
from .report import ReportGenerator
from .screen import ScreenCapture
from .system import SystemTweaker
from .utils import SafeSubprocess
from .files import FileManager

__all__ = [
    'AppManager',
    'AuthorizedDeviceAuditor',
    'AutoBackup',
    'DataRecovery',
    'Database',
    'DisplayAnalyzer',
    'DeviceDetector',
    'dump_partition_via_adb',
    'enable_debugging_settings',
    'FRPEngine',
    'FileManager',
    'flash_signed_firmware',
    'grant_debugging_authorization',
    'hash_partition_via_adb',
    'LogcatViewer',
    'Logger',
    'NetworkAnalyzer',
    'NetworkTools',
    'PSUTIL_AVAILABLE',
    'PerformanceAnalyzer',
    'reboot_to_download_mode',
    'reboot_to_edl',
    'reboot_to_fastboot',
    'reboot_to_recovery',
    'ReportGenerator',
    'restart_adbd',
    'SafeSubprocess',
    'ScreenCapture',
    'SystemMonitor',
    'SystemTweaker',
    'db',
    'logger',
    'monitor',
    'socket',
    'subprocess',
    'urllib',
]

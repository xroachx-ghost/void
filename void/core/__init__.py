"""Core functionality for Void."""

from __future__ import annotations

import socket
import subprocess
import urllib

from .apps import AppManager
from .backup import AutoBackup
from .data_recovery import DataRecovery
from .database import Database, db
from .device import DeviceDetector
from .frp import FRPEngine
from .logcat import LogcatViewer
from .logging import Logger, logger
from .monitor import PSUTIL_AVAILABLE, SystemMonitor, monitor
from .network import NetworkAnalyzer, NetworkTools
from .performance import PerformanceAnalyzer
from .report import ReportGenerator
from .screen import ScreenCapture
from .system import SystemTweaker
from .utils import SafeSubprocess
from .files import FileManager
from .partitions import PartitionManager
from .recovery import RecoveryWorkflow
from .rom_validation import RomValidator

__all__ = [
    'AppManager',
    'AutoBackup',
    'DataRecovery',
    'Database',
    'DeviceDetector',
    'FRPEngine',
    'FileManager',
    'PartitionManager',
    'RecoveryWorkflow',
    'RomValidator',
    'LogcatViewer',
    'Logger',
    'NetworkAnalyzer',
    'NetworkTools',
    'PSUTIL_AVAILABLE',
    'PerformanceAnalyzer',
    'ReportGenerator',
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

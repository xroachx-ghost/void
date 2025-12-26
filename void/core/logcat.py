from __future__ import annotations

import subprocess
from typing import Callable, Optional

from .logging import logger


class LogcatViewer:
    """Real-time logcat viewing"""

    def __init__(self):
        self.process = None
        self.running = False

    def start(
        self,
        device_id: str,
        filter_tag: str = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ):
        """Start logcat"""
        if progress_callback:
            progress_callback("Starting logcat stream...")
        cmd = ['adb', '-s', device_id, 'logcat']
        if filter_tag:
            cmd.extend(['-s', filter_tag])

        self.running = True
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        logger.log('info', 'logcat', 'Logcat started')
        if progress_callback:
            progress_callback("Logcat streaming.")

    def stop(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Stop logcat"""
        if self.process:
            self.process.terminate()
            self.running = False
            logger.log('info', 'logcat', 'Logcat stopped')
            if progress_callback:
                progress_callback("Logcat stopped.")

    def read_line(self) -> Optional[str]:
        """Read one line"""
        if self.process and self.running:
            try:
                return self.process.stdout.readline()
            except Exception:
                pass
        return None

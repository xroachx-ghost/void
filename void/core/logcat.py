from __future__ import annotations

import subprocess
from typing import Optional

from .logging import logger


class LogcatViewer:
    """Real-time logcat viewing"""

    def __init__(self):
        self.process = None
        self.running = False

    def start(self, device_id: str, filter_tag: str = None):
        """Start logcat"""
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

    def stop(self):
        """Stop logcat"""
        if self.process:
            self.process.terminate()
            self.running = False
            logger.log('info', 'logcat', 'Logcat stopped')

    def read_line(self) -> Optional[str]:
        """Read one line"""
        if self.process and self.running:
            try:
                return self.process.stdout.readline()
            except Exception:
                pass
        return None

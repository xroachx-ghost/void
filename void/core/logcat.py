"""
Logcat viewer and analysis.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

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

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except (FileNotFoundError, OSError) as exc:
            self.process = None
            self.running = False
            logger.log('error', 'logcat', f'Failed to start logcat: {exc}')
            if progress_callback:
                progress_callback("Logcat failed to start.")
            return

        self.running = True

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

    @staticmethod
    def capture_logcat(device_id: str, level: str = None, tag: str = None, lines: int = None) -> str:
        """Capture logcat output
        
        Args:
            device_id: Device identifier
            level: Log level filter (V/D/I/W/E/F)
            tag: Tag filter
            lines: Number of lines to capture
            
        Returns:
            Logcat output as string
        """
        from .utils import SafeSubprocess
        
        cmd = ['adb', '-s', device_id, 'logcat', '-d']
        
        if level:
            cmd.extend(['-v', 'brief', f'*:{level}'])
        
        if tag:
            cmd.extend(['-s', tag])
        
        if lines:
            cmd.extend(['-t', str(lines)])
        
        code, stdout, _ = SafeSubprocess.run(cmd)
        
        return stdout if code == 0 else ''

    @staticmethod
    def export_logcat(device_id: str, output_path: str, level: str = None) -> bool:
        """Export logcat to file
        
        Args:
            device_id: Device identifier
            output_path: Local output file path
            level: Optional log level filter
        """
        from pathlib import Path
        
        output = LogcatViewer.capture_logcat(device_id, level=level)
        
        try:
            Path(output_path).write_text(output, encoding='utf-8')
            return True
        except Exception:
            return False

    @staticmethod
    def clear_logcat(device_id: str) -> bool:
        """Clear logcat buffer"""
        from .utils import SafeSubprocess
        
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'logcat', '-c'])
        return code == 0

    @staticmethod
    def get_kernel_log(device_id: str) -> str:
        """Get kernel log (dmesg)"""
        from .utils import SafeSubprocess
        
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dmesg'])
        return stdout if code == 0 else ''

    @staticmethod
    def get_crash_logs(device_id: str) -> list:
        """Get crash logs (tombstones)"""
        from .utils import SafeSubprocess
        
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'ls', '/data/tombstones/'])
        
        if code == 0 and stdout:
            return [line.strip() for line in stdout.strip().split('\n') if line.strip()]
        
        return []

    @staticmethod
    def get_anr_traces(device_id: str) -> str:
        """Get ANR (Application Not Responding) traces"""
        from .utils import SafeSubprocess
        
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'cat', '/data/anr/traces.txt'])
        return stdout if code == 0 else ''

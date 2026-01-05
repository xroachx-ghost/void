"""
Device monitoring and tracking.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import threading
import time
from typing import Dict

from .logging import logger

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemMonitor:
    """Real-time system monitoring"""

    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.stats = {
            "cpu": [],
            "memory": [],
            "network": [],
        }

    def start(self):
        """Start monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.log("info", "monitor", "System monitoring started")

    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.log("info", "monitor", "System monitoring stopped")

    def _monitor_loop(self):
        """Monitoring loop"""
        while self.monitoring:
            try:
                if PSUTIL_AVAILABLE:
                    self.stats["cpu"].append(psutil.cpu_percent())
                    self.stats["memory"].append(psutil.virtual_memory().percent)

                    # Keep only last 100 readings
                    for key in self.stats:
                        if len(self.stats[key]) > 100:
                            self.stats[key] = self.stats[key][-100:]

                time.sleep(1)
            except Exception:
                pass

    def get_stats(self) -> Dict:
        """Get current statistics"""
        if PSUTIL_AVAILABLE:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "cpu_history": self.stats["cpu"][-20:],
                "memory_history": self.stats["memory"][-20:],
            }
        return {}


monitor = SystemMonitor()

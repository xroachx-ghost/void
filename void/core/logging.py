from __future__ import annotations

import logging
from datetime import datetime

from ..config import Config
from .database import db

try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Logger:
    """Logging system"""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

        log_file = Config.LOG_DIR / f"void_{datetime.now().strftime('%Y%m')}.log"
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger('VoidSuite')

    def log(self, level: str, category: str, message: str, device_id: str = None, method: str = None):
        """Log message"""
        if self.console:
            style = {
                'debug': 'dim',
                'info': 'green',
                'warning': 'yellow',
                'error': 'red bold',
                'success': 'bold green',
            }.get(level, 'white')
            self.console.print(f"[{level.upper()}] {message}", style=style)
        else:
            print(f"[{level.upper()}] {message}")

        log_method = getattr(self.logger, level if level != 'success' else 'info', self.logger.info)
        log_method(message)

        try:
            db.log(level, category, message, device_id, method)
        except Exception:
            pass


logger = Logger()

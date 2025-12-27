from __future__ import annotations

import logging

from ..logging import configure_logging
from .database import db
from .privacy import redact_message


class Logger:
    """Logging system"""

    def __init__(self):
        configure_logging()
        self.logger = logging.getLogger("void")

    def log(self, level: str, category: str, message: str, device_id: str = None, method: str = None):
        """Log message"""
        sanitized_message = redact_message(message)
        log_method = getattr(self.logger, level if level != "success" else "info", self.logger.info)
        log_method(
            sanitized_message,
            extra={
                "category": category,
                "device_id": device_id or "-",
                "method": method or "-",
            },
        )

        try:
            db.log(level, category, sanitized_message, device_id, method)
        except Exception:
            pass


logger = Logger()

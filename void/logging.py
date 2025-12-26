from __future__ import annotations

import logging
from datetime import datetime

from .config import Config

_CONFIGURED = False


class StructuredFormatter(logging.Formatter):
    """Ensure structured fields are always present."""

    def format(self, record: logging.LogRecord) -> str:
        for field in ("category", "device_id", "method"):
            if not hasattr(record, field):
                setattr(record, field, "-")
        return super().format(record)


def configure_logging(level: int = logging.DEBUG) -> None:
    """Configure log handlers for file and console."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    Config.setup()
    log_file = Config.LOG_DIR / f"void_{datetime.now().strftime('%Y%m')}.log"

    formatter = StructuredFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "category=%(category)s device_id=%(device_id)s method=%(method)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger."""
    configure_logging()
    return logging.getLogger(name)

"""
VOID CONFIGURATION

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from pathlib import Path


class Config:
    """Configuration constants."""

    VERSION = "6.0.1"
    CODENAME = "AUTOMATION"
    APP_NAME = "Void"

    # Timeouts
    TIMEOUT_SHORT = 5
    TIMEOUT_MEDIUM = 30
    TIMEOUT_LONG = 300

    # Paths
    BASE_DIR = Path.home() / ".void"
    DB_PATH = BASE_DIR / "void.db"
    LOG_DIR = BASE_DIR / "logs"
    BACKUP_DIR = BASE_DIR / "backups"
    EXPORTS_DIR = BASE_DIR / "exports"
    CACHE_DIR = BASE_DIR / "cache"
    REPORTS_DIR = BASE_DIR / "reports"
    MONITOR_DIR = BASE_DIR / "monitoring"
    SCRIPTS_DIR = BASE_DIR / "scripts"

    # Security
    MAX_INPUT_LENGTH = 256

    # Features
    ENABLE_AUTO_BACKUP = True
    ENABLE_MONITORING = True
    ENABLE_ANALYTICS = True

    # Crypto
    ALLOW_INSECURE_CRYPTO = False

    @classmethod
    def setup(cls) -> None:
        """Create necessary directories."""
        for path in [
            cls.BASE_DIR,
            cls.LOG_DIR,
            cls.BACKUP_DIR,
            cls.EXPORTS_DIR,
            cls.CACHE_DIR,
            cls.REPORTS_DIR,
            cls.MONITOR_DIR,
            cls.SCRIPTS_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)


Config.setup()

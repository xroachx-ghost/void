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

    # Theme
    THEME_NAME = "Veilstorm Protocol"
    THEME_TAGLINE = "Anonymous ops console with zero-friction automation."
    THEME_SLOGANS = [
        "Kali dragon in motion. Anonymous mask on command.",
        "Operate silent. Execute fast. Leave no trace.",
        "Encrypted workflows. Shadow-grade automation.",
    ]
    GUI_THEME = {
        "bg": "#070b12",
        "panel": "#111a28",
        "panel_alt": "#0c1420",
        "accent": "#00f5d4",
        "accent_soft": "#7bffda",
        "accent_alt": "#7c3aed",
        "text": "#e6f1ff",
        "muted": "#9cb1cf",
        "shadow": "#03050a",
        "button_bg": "#0f1826",
        "button_active": "#1b2a3d",
        "button_text": "#00f5d4",
        "gradient_start": "#0a1220",
        "gradient_end": "#16243b",
        "splash_start": "#04060b",
        "splash_end": "#1a2540",
        "dragon": "#00f5d4",
        "mask": "#e6f1ff",
    }

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
            if path.exists():
                continue
            path.mkdir(parents=True, exist_ok=True)

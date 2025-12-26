"""
VOID CONFIGURATION

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from pathlib import Path
from typing import Any, Dict

import json


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
        "border": "#1b2a3d",
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
    CONFIG_PATH = BASE_DIR / "config.json"
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
    ENABLE_REPORTS = True
    ENABLE_MONITORING = True
    ENABLE_ANALYTICS = True

    # Crypto
    ALLOW_INSECURE_CRYPTO = False

    DEFAULT_SETTINGS: Dict[str, Any] = {
        "enable_auto_backup": ENABLE_AUTO_BACKUP,
        "enable_reports": ENABLE_REPORTS,
        "enable_analytics": ENABLE_ANALYTICS,
        "exports_dir": str(EXPORTS_DIR),
        "reports_dir": str(REPORTS_DIR),
    }

    @classmethod
    def setup(cls) -> None:
        """Create necessary directories."""
        cls.BASE_DIR.mkdir(parents=True, exist_ok=True)
        cls.load_settings()
        cls.ensure_directories()

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure configured directories exist."""
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

    @classmethod
    def read_config(cls) -> Dict[str, Any]:
        """Read the JSON config file."""
        try:
            with cls.CONFIG_PATH.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    @classmethod
    def write_config(cls, data: Dict[str, Any]) -> None:
        """Persist JSON config data."""
        cls.BASE_DIR.mkdir(parents=True, exist_ok=True)
        with cls.CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

    @classmethod
    def _normalize_settings(cls, settings: Dict[str, Any]) -> Dict[str, Any]:
        merged = {**cls.DEFAULT_SETTINGS, **(settings or {})}

        def _parse_dir(value: Any, fallback: Path) -> Path:
            if not value:
                return fallback
            try:
                return Path(value).expanduser()
            except (TypeError, ValueError):
                return fallback

        exports_dir = _parse_dir(merged.get("exports_dir"), cls.EXPORTS_DIR)
        reports_dir = _parse_dir(merged.get("reports_dir"), cls.REPORTS_DIR)

        normalized = {
            "enable_auto_backup": bool(merged.get("enable_auto_backup")),
            "enable_reports": bool(merged.get("enable_reports")),
            "enable_analytics": bool(merged.get("enable_analytics")),
            "exports_dir": str(exports_dir),
            "reports_dir": str(reports_dir),
        }

        cls.ENABLE_AUTO_BACKUP = normalized["enable_auto_backup"]
        cls.ENABLE_REPORTS = normalized["enable_reports"]
        cls.ENABLE_ANALYTICS = normalized["enable_analytics"]
        cls.EXPORTS_DIR = exports_dir
        cls.REPORTS_DIR = reports_dir

        return normalized

    @classmethod
    def load_settings(cls) -> Dict[str, Any]:
        """Load settings from the config file and apply them."""
        data = cls.read_config()
        settings = data.get("settings", {}) if isinstance(data, dict) else {}
        return cls._normalize_settings(settings)

    @classmethod
    def save_settings(cls, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Save settings to the config file."""
        normalized = cls._normalize_settings(settings)
        data = cls.read_config()
        data["settings"] = normalized
        cls.write_config(data)
        cls.ensure_directories()
        return normalized

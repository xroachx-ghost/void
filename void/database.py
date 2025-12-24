"""Database access."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Dict

from .config import Config


class Database:
    """Database management"""

    def __init__(self):
        self.db_path = Config.DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database"""
        with self._get_connection() as conn:
            # Devices table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    manufacturer TEXT,
                    model TEXT,
                    android_version TEXT,
                    serial TEXT,
                    imei TEXT,
                    chipset TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    connection_count INTEGER DEFAULT 1,
                    notes TEXT
                )
            """
            )

            # Methods table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS methods (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    category TEXT,
                    success_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    avg_duration REAL DEFAULT 0,
                    last_success TIMESTAMP
                )
            """
            )

            # Logs table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    category TEXT,
                    message TEXT,
                    device_id TEXT,
                    method TEXT
                )
            """
            )

            # Backups table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY,
                    device_id TEXT,
                    backup_name TEXT,
                    backup_path TEXT,
                    backup_size INTEGER,
                    backup_type TEXT,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT
                )
            """
            )

            # Analytics table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    event_data TEXT,
                    device_id TEXT
                )
            """
            )

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_device ON logs(device_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_backups_device ON backups(device_id)")

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def log(self, level: str, category: str, message: str, device_id: str = None, method: str = None) -> None:
        """Add log entry"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO logs (level, category, message, device_id, method) VALUES (?, ?, ?, ?, ?)",
                (level, category, message[:1000], device_id, method),
            )
            conn.commit()

    def track_event(self, event_type: str, event_data: Dict, device_id: str = None) -> None:
        """Track analytics event"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO analytics (event_type, event_data, device_id) VALUES (?, ?, ?)",
                (event_type, json.dumps(event_data), device_id),
            )
            conn.commit()

    def update_device(self, device_info: Dict) -> None:
        """Update or insert device"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO devices (id, manufacturer, model, android_version, serial, imei, chipset)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_seen = CURRENT_TIMESTAMP,
                    connection_count = connection_count + 1,
                    manufacturer = excluded.manufacturer,
                    model = excluded.model,
                    android_version = excluded.android_version
            """,
                (
                    device_info.get("id"),
                    device_info.get("manufacturer"),
                    device_info.get("model"),
                    device_info.get("android_version"),
                    device_info.get("serial"),
                    device_info.get("imei"),
                    device_info.get("chipset"),
                ),
            )
            conn.commit()

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
            stats: Dict[str, object] = {}
            stats["total_devices"] = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
            stats["total_logs"] = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
            stats["total_backups"] = conn.execute("SELECT COUNT(*) FROM backups").fetchone()[0]
            stats["total_methods"] = conn.execute("SELECT COUNT(*) FROM methods").fetchone()[0]

            # Method success rates
            methods = conn.execute(
                """
                SELECT name, success_count, total_count 
                FROM methods 
                WHERE total_count > 0 
                ORDER BY (success_count * 1.0 / total_count) DESC 
                LIMIT 5
            """
            ).fetchall()
            stats["top_methods"] = [dict(m) for m in methods]

            return stats


db = Database()

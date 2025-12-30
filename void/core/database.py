"""
Database management for Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List

from ..config import Config
from .privacy import redact_event_data, redact_message, should_store


class Database:
    """Database management"""

    def __init__(self):
        Config.setup()
        self.db_path = Config.DB_PATH
        self._init_db()

    def _init_db(self):
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

    def log(self, level: str, category: str, message: str, device_id: str = None, method: str = None):
        """Add log entry"""
        sanitized_message = redact_message(message)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO logs (level, category, message, device_id, method) VALUES (?, ?, ?, ?, ?)",
                (level, category, sanitized_message[:1000], device_id, method),
            )
            conn.commit()

    def track_event(self, event_type: str, event_data: Dict, device_id: str = None):
        """Track analytics event"""
        sanitized_event_data = redact_event_data(event_data)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO analytics (event_type, event_data, device_id) VALUES (?, ?, ?)",
                (event_type, json.dumps(sanitized_event_data), device_id),
            )
            conn.commit()

    def update_device(self, device_info: Dict):
        """Update or insert device"""
        serial_value = device_info.get("serial") if should_store("serial") else None
        imei_value = device_info.get("imei") if should_store("imei") else None
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
                    android_version = excluded.android_version,
                    serial = excluded.serial,
                    imei = excluded.imei
            """,
                (
                    device_info.get('id'),
                    device_info.get('manufacturer'),
                    device_info.get('model'),
                    device_info.get('android_version'),
                    serial_value,
                    imei_value,
                    device_info.get('chipset'),
                ),
            )
            conn.commit()

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
            stats = {}
            stats['total_devices'] = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
            stats['total_logs'] = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
            stats['total_backups'] = conn.execute("SELECT COUNT(*) FROM backups").fetchone()[0]
            stats['total_methods'] = conn.execute("SELECT COUNT(*) FROM methods").fetchone()[0]
            stats['total_reports'] = conn.execute(
                "SELECT COUNT(*) FROM analytics WHERE event_type = 'report'"
            ).fetchone()[0]

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
            stats['top_methods'] = [dict(m) for m in methods]

            return stats

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, level, category, message, device_id, method
                FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_filtered_logs(
        self,
        level: str | None = None,
        category: str | None = None,
        device_id: str | None = None,
        method: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Get filtered log entries."""
        query = (
            """
            SELECT timestamp, level, category, message, device_id, method
            FROM logs
            """
        )
        clauses = []
        params: List[Any] = []

        if level:
            clauses.append("level = ?")
            params.append(level)
        if category:
            clauses.append("category = ?")
            params.append(category)
        if device_id:
            clauses.append("device_id = ?")
            params.append(device_id)
        if method:
            clauses.append("method = ?")
            params.append(method)
        if since:
            clauses.append("timestamp >= ?")
            params.append(since)
        if until:
            clauses.append("timestamp <= ?")
            params.append(until)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(row) for row in rows]

    def get_recent_backups(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent backups."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT device_id, backup_name, backup_path, backup_size, backup_type, created
                FROM backups
                ORDER BY created DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reports."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, event_data, device_id
                FROM analytics
                WHERE event_type = 'report'
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_recent_devices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently seen devices."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, manufacturer, model, android_version, last_seen, connection_count
                FROM devices
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_top_methods(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top methods by success rate."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT name, success_count, total_count, avg_duration, last_success
                FROM methods
                WHERE total_count > 0
                ORDER BY (success_count * 1.0 / total_count) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]


db = Database()

"""
Authentication System for Void Suite

Provides user authentication, session management, and access control.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple
import secrets


class AuthenticationManager:
    """Manages user authentication and sessions"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".void" / "auth.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize authentication database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operator',
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TEXT
            )
        """
        )

        # Sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Audit log
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                success INTEGER NOT NULL,
                ip_address TEXT,
                timestamp TEXT NOT NULL,
                details TEXT
            )
        """
        )

        conn.commit()
        conn.close()

        # Create default admin user if none exists
        self._create_default_admin()

    def _create_default_admin(self):
        """Create default admin user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", ("admin",))
        if cursor.fetchone()[0] == 0:
            # Create default admin with password 'admin' (should be changed!)
            self.create_user("admin", "admin", "admin")

        conn.close()

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        ).hex()

    def create_user(self, username: str, password: str, role: str = "operator") -> bool:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Generate salt
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)

            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (username, password_hash, salt, role, datetime.now().isoformat()),
            )

            conn.commit()
            conn.close()

            self._audit_log(username, "user_created", True)
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate(
        self, username: str, password: str, ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Authenticate user and return session token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if user exists and is active
        cursor.execute(
            """
            SELECT id, password_hash, salt, is_active, failed_attempts, locked_until
            FROM users WHERE username = ?
        """,
            (username,),
        )

        result = cursor.fetchone()

        if not result:
            self._audit_log(username, "login_failed", False, ip_address, "User not found")
            conn.close()
            return False, None

        user_id, stored_hash, salt, is_active, failed_attempts, locked_until = result

        # Check if account is locked
        if locked_until:
            lock_time = datetime.fromisoformat(locked_until)
            if datetime.now() < lock_time:
                self._audit_log(username, "login_failed", False, ip_address, "Account locked")
                conn.close()
                return False, None

        # Check if active
        if not is_active:
            self._audit_log(username, "login_failed", False, ip_address, "Account inactive")
            conn.close()
            return False, None

        # Verify password
        password_hash = self._hash_password(password, salt)

        if password_hash != stored_hash:
            # Increment failed attempts
            failed_attempts += 1
            lock_until = None

            if failed_attempts >= 5:
                # Lock account for 15 minutes
                lock_until = (datetime.now() + timedelta(minutes=15)).isoformat()

            cursor.execute(
                """
                UPDATE users SET failed_attempts = ?, locked_until = ?
                WHERE id = ?
            """,
                (failed_attempts, lock_until, user_id),
            )
            conn.commit()

            self._audit_log(
                username,
                "login_failed",
                False,
                ip_address,
                f"Invalid password (attempt {failed_attempts})",
            )
            conn.close()
            return False, None

        # Reset failed attempts on successful login
        cursor.execute(
            """
            UPDATE users SET failed_attempts = 0, locked_until = NULL, last_login = ?
            WHERE id = ?
        """,
            (datetime.now().isoformat(), user_id),
        )

        # Create session
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=8)).isoformat()

        cursor.execute(
            """
            INSERT INTO sessions (user_id, session_token, created_at, expires_at, last_activity, ip_address, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
            (
                user_id,
                session_token,
                datetime.now().isoformat(),
                expires_at,
                datetime.now().isoformat(),
                ip_address,
            ),
        )

        conn.commit()
        conn.close()

        self._audit_log(username, "login_success", True, ip_address)
        return True, session_token

    def validate_session(self, session_token: str) -> Tuple[bool, Optional[Dict]]:
        """Validate session token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT s.user_id, s.expires_at, u.username, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ? AND s.is_active = 1
        """,
            (session_token,),
        )

        result = cursor.fetchone()

        if not result:
            conn.close()
            return False, None

        user_id, expires_at, username, role = result

        # Check if expired
        if datetime.now() > datetime.fromisoformat(expires_at):
            cursor.execute(
                "UPDATE sessions SET is_active = 0 WHERE session_token = ?", (session_token,)
            )
            conn.commit()
            conn.close()
            return False, None

        # Update last activity
        cursor.execute(
            """
            UPDATE sessions SET last_activity = ?
            WHERE session_token = ?
        """,
            (datetime.now().isoformat(), session_token),
        )

        conn.commit()
        conn.close()

        return True, {"user_id": user_id, "username": username, "role": role}

    def logout(self, session_token: str) -> bool:
        """Logout user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE sessions SET is_active = 0
            WHERE session_token = ?
        """,
            (session_token,),
        )

        conn.commit()
        conn.close()
        return True

    def _audit_log(
        self,
        username: str,
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """Log authentication events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO auth_audit (username, action, success, ip_address, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                username,
                action,
                1 if success else 0,
                ip_address,
                datetime.now().isoformat(),
                details,
            ),
        )

        conn.commit()
        conn.close()


# Global authentication manager instance
_auth_manager = None


def get_auth_manager() -> AuthenticationManager:
    """Get global authentication manager"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthenticationManager()
    return _auth_manager

"""
Tests for Authentication System

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
"""

import pytest
import tempfile
from pathlib import Path
from void.core.auth.authentication import AuthenticationManager


@pytest.fixture
def auth_manager():
    """Create temporary authentication manager"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_auth.db"
        manager = AuthenticationManager(db_path)
        yield manager


def test_create_user(auth_manager):
    """Test user creation"""
    result = auth_manager.create_user("testuser", "password123", "operator")
    assert result is True

    # Try creating duplicate
    result = auth_manager.create_user("testuser", "password123", "operator")
    assert result is False


def test_authenticate_success(auth_manager):
    """Test successful authentication"""
    auth_manager.create_user("testuser", "password123", "operator")

    success, token = auth_manager.authenticate("testuser", "password123")
    assert success is True
    assert token is not None


def test_authenticate_failure(auth_manager):
    """Test failed authentication"""
    auth_manager.create_user("testuser", "password123", "operator")

    success, token = auth_manager.authenticate("testuser", "wrongpassword")
    assert success is False
    assert token is None


def test_validate_session(auth_manager):
    """Test session validation"""
    auth_manager.create_user("testuser", "password123", "operator")
    success, token = auth_manager.authenticate("testuser", "password123")

    valid, user_info = auth_manager.validate_session(token)
    assert valid is True
    assert user_info["username"] == "testuser"
    assert user_info["role"] == "operator"


def test_logout(auth_manager):
    """Test logout"""
    auth_manager.create_user("testuser", "password123", "operator")
    success, token = auth_manager.authenticate("testuser", "password123")

    result = auth_manager.logout(token)
    assert result is True

    # Session should be invalid after logout
    valid, _ = auth_manager.validate_session(token)
    assert valid is False


def test_account_lockout(auth_manager):
    """Test account lockout after failed attempts"""
    auth_manager.create_user("testuser", "password123", "operator")

    # Try 5 failed logins
    for _ in range(5):
        auth_manager.authenticate("testuser", "wrongpassword")

    # Account should be locked
    success, token = auth_manager.authenticate("testuser", "password123")
    assert success is False


def test_default_admin_created(auth_manager):
    """Test that default admin is created"""
    success, token = auth_manager.authenticate("admin", "admin")
    assert success is True
    assert token is not None

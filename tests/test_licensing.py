"""
Tests for licensing module.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

import json
from datetime import datetime, timedelta

import pytest

from void.licensing import LicenseManager, LicenseStatus, LicenseType


@pytest.fixture
def temp_license_file(tmp_path, monkeypatch):
    """Create a temporary license file path"""
    license_file = tmp_path / ".void" / "license.key"
    license_file.parent.mkdir(parents=True, exist_ok=True)

    # Patch the LICENSE_FILE constant
    monkeypatch.setattr(LicenseManager, "LICENSE_FILE", license_file)

    return license_file


@pytest.fixture
def license_manager(temp_license_file):
    """Create a license manager instance"""
    return LicenseManager()


def test_license_manager_init(license_manager, temp_license_file):
    """Test license manager initialization"""
    assert license_manager.license_file == temp_license_file
    assert temp_license_file.parent.exists()


def test_get_hardware_fingerprint(license_manager):
    """Test hardware fingerprint generation"""
    fingerprint1 = license_manager.get_hardware_fingerprint()
    fingerprint2 = license_manager.get_hardware_fingerprint()

    # Should be consistent
    assert fingerprint1 == fingerprint2

    # Should be a valid hex string
    assert len(fingerprint1) == 64  # SHA256 hex
    assert all(c in "0123456789abcdef" for c in fingerprint1)


def test_activate_license(license_manager, temp_license_file):
    """Test license activation"""
    license_data = {
        "email": "test@example.com",
        "license_type": "personal",
        "created_at": datetime.now().isoformat(),
    }

    result = license_manager.activate_license(license_data)

    assert result is True
    assert temp_license_file.exists()

    # Verify saved data
    with open(temp_license_file, "r") as f:
        saved_data = json.load(f)

    assert saved_data["email"] == "test@example.com"
    assert saved_data["license_type"] == "personal"
    assert "activated_at" in saved_data
    assert "device_fingerprint" in saved_data
    assert saved_data["status"] == "active"


def test_deactivate_license(license_manager, temp_license_file):
    """Test license deactivation"""
    # First activate a license
    license_data = {
        "email": "test@example.com",
        "license_type": "personal",
    }
    license_manager.activate_license(license_data)

    # Deactivate
    result = license_manager.deactivate_license()

    assert result is True

    # Verify license is marked as deactivated
    with open(temp_license_file, "r") as f:
        saved_data = json.load(f)

    assert saved_data["status"] == "deactivated"
    assert "deactivated_at" in saved_data


def test_load_license(license_manager, temp_license_file):
    """Test loading license from file"""
    # Test when no license exists
    result = license_manager.load_license()
    assert result is None

    # Create a license
    license_data = {
        "email": "test@example.com",
        "license_type": "professional",
    }
    license_manager.activate_license(license_data)

    # Load it
    loaded = license_manager.load_license()
    assert loaded is not None
    assert loaded["email"] == "test@example.com"
    assert loaded["license_type"] == "professional"


def test_check_expiration(license_manager):
    """Test expiration checking"""
    # Future expiration
    future_data = {"expiration_date": (datetime.now() + timedelta(days=30)).isoformat()}
    assert license_manager.check_expiration(future_data) is False

    # Past expiration
    past_data = {"expiration_date": (datetime.now() - timedelta(days=1)).isoformat()}
    assert license_manager.check_expiration(past_data) is True

    # No expiration
    no_exp_data = {}
    assert license_manager.check_expiration(no_exp_data) is False


def test_validate_license_not_found(license_manager):
    """Test validation when no license exists"""
    status, data = license_manager.validate_license()

    assert status == LicenseStatus.NOT_FOUND
    assert data is None


def test_validate_license_deactivated(license_manager):
    """Test validation of deactivated license"""
    license_data = {
        "email": "test@example.com",
        "license_type": "personal",
    }
    license_manager.activate_license(license_data)
    license_manager.deactivate_license()

    status, data = license_manager.validate_license()

    assert status == LicenseStatus.DEACTIVATED
    assert data is not None


def test_validate_license_expired(license_manager):
    """Test validation of expired license"""
    license_data = {
        "email": "test@example.com",
        "license_type": "trial",
        "expiration_date": (datetime.now() - timedelta(days=1)).isoformat(),
    }
    license_manager.activate_license(license_data)

    status, data = license_manager.validate_license()

    assert status == LicenseStatus.EXPIRED
    assert data is not None


def test_validate_license_device_mismatch(license_manager):
    """Test validation with device mismatch"""
    license_data = {
        "email": "test@example.com",
        "license_type": "personal",
    }
    license_manager.activate_license(license_data)

    # Modify the device fingerprint
    saved_data = license_manager.load_license()
    saved_data["device_fingerprint"] = "different_fingerprint"
    with open(license_manager.license_file, "w") as f:
        json.dump(saved_data, f)

    status, data = license_manager.validate_license()

    assert status == LicenseStatus.DEVICE_MISMATCH
    assert data is not None


def test_validate_license_valid(license_manager):
    """Test validation of valid license"""
    license_data = {
        "email": "test@example.com",
        "license_type": "professional",
        "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
    }
    license_manager.activate_license(license_data)

    status, data = license_manager.validate_license()

    assert status == LicenseStatus.VALID
    assert data is not None


def test_get_license_info_no_license(license_manager):
    """Test getting license info when no license exists"""
    info = license_manager.get_license_info()

    assert info["status"] == "not_found"
    assert info["type"] == "none"
    assert "No license found" in info["message"]


def test_get_license_info_valid(license_manager):
    """Test getting license info for valid license"""
    license_data = {
        "email": "test@example.com",
        "license_type": "professional",
        "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
    }
    license_manager.activate_license(license_data)

    info = license_manager.get_license_info()

    assert info["status"] == "valid"
    assert info["type"] == "professional"
    assert info["email"] == "test@example.com"
    assert "days_remaining" in info
    assert info["days_remaining"] >= 29  # Should be around 30 days


def test_start_trial(license_manager):
    """Test starting a trial license"""
    result = license_manager.start_trial()

    assert result is True

    # Verify trial license was created
    status, data = license_manager.validate_license()

    assert status == LicenseStatus.VALID
    assert data["license_type"] == "trial"
    assert data["email"] == "trial@void-suite.local"

    # Check expiration is ~14 days
    info = license_manager.get_license_info()
    assert info["days_remaining"] >= 13
    assert info["days_remaining"] <= 14


def test_start_trial_already_licensed(license_manager):
    """Test starting trial when already licensed"""
    # First activate a valid license
    license_data = {
        "email": "test@example.com",
        "license_type": "personal",
        "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
    }
    license_manager.activate_license(license_data)

    # Try to start trial
    result = license_manager.start_trial()

    assert result is False

    # Verify original license is still valid
    status, data = license_manager.validate_license()
    assert status == LicenseStatus.VALID
    assert data["license_type"] == "personal"


def test_is_licensed(license_manager):
    """Test is_licensed check"""
    # No license
    assert license_manager.is_licensed() is False

    # Activate license
    license_data = {
        "email": "test@example.com",
        "license_type": "personal",
        "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
    }
    license_manager.activate_license(license_data)

    # Should be licensed now
    assert license_manager.is_licensed() is True

    # Deactivate
    license_manager.deactivate_license()

    # Should not be licensed
    assert license_manager.is_licensed() is False


def test_get_license_type(license_manager):
    """Test getting license type"""
    # No license
    assert license_manager.get_license_type() is None

    # Trial license
    license_manager.start_trial()
    assert license_manager.get_license_type() == LicenseType.TRIAL

    # Professional license
    license_data = {
        "email": "test@example.com",
        "license_type": "professional",
        "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
    }
    license_manager.activate_license(license_data)
    assert license_manager.get_license_type() == LicenseType.PROFESSIONAL


def test_perpetual_license(license_manager):
    """Test license without expiration (perpetual)"""
    license_data = {
        "email": "test@example.com",
        "license_type": "enterprise",
        # No expiration_date
    }
    license_manager.activate_license(license_data)

    status, data = license_manager.validate_license()

    assert status == LicenseStatus.VALID

    info = license_manager.get_license_info()
    assert info["expires_at"] == "Never"
    assert info["days_remaining"] is None

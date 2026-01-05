"""
Tests for USB Debugging Enhancement

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
"""

import pytest
from unittest.mock import patch
from void.core.system import SystemTweaker


@pytest.fixture
def mock_subprocess():
    """Mock SafeSubprocess"""
    with patch("void.core.system.SafeSubprocess") as mock:
        mock.run.return_value = (0, "success", "")
        yield mock


def test_force_usb_debugging_standard(mock_subprocess):
    """Test standard USB debugging method"""
    result = SystemTweaker.force_usb_debugging("test_device", "standard")

    assert result["success"] is True
    assert result["methods_attempted"] == "standard"
    assert len(result["steps"]) > 0


def test_force_usb_debugging_all_methods(mock_subprocess):
    """Test all USB debugging methods"""
    result = SystemTweaker.force_usb_debugging("test_device", "all")

    assert result["methods_attempted"] == "all"
    assert len(result["steps"]) > 10  # Multiple methods should be attempted


def test_force_usb_debugging_properties(mock_subprocess):
    """Test properties method"""
    result = SystemTweaker.force_usb_debugging("test_device", "properties")

    assert result["methods_attempted"] == "properties"
    # Should have steps for setting properties
    property_steps = [s for s in result["steps"] if s["category"] == "properties"]
    assert len(property_steps) > 0


def test_get_usb_debugging_methods():
    """Test getting USB debugging methods info"""
    methods_info = SystemTweaker.get_usb_debugging_methods()

    assert "methods" in methods_info
    assert "recommendations" in methods_info
    assert "warnings" in methods_info

    # Should have 9 methods
    assert len(methods_info["methods"]) >= 9

    # Check method structure
    method = methods_info["methods"][0]
    assert "id" in method
    assert "name" in method
    assert "description" in method
    assert "requirements" in method
    assert "risk_level" in method

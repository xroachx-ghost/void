"""
Tests for Problem Solver

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
"""

import pytest
from unittest.mock import patch
from void.core.problem_solver import AndroidProblemSolver, EmergencyRecovery


@pytest.fixture
def mock_subprocess():
    """Mock SafeSubprocess"""
    with patch("void.core.problem_solver.SafeSubprocess") as mock:
        mock.run.return_value = (0, "success", "")
        yield mock


def test_diagnose_problem_basic(mock_subprocess):
    """Test basic problem diagnosis"""
    result = AndroidProblemSolver.diagnose_problem("test_device")

    assert "device_id" in result
    assert "problems_found" in result
    assert "problems" in result
    assert "health_score" in result
    assert isinstance(result["problems"], list)


def test_fix_bootloop(mock_subprocess):
    """Test bootloop fixing"""
    result = AndroidProblemSolver.fix_bootloop("test_device")

    assert "success" in result
    assert "steps" in result
    assert len(result["steps"]) > 0


def test_fix_soft_brick(mock_subprocess):
    """Test soft brick fixing"""
    result = AndroidProblemSolver.fix_soft_brick("test_device")

    assert "success" in result
    assert "steps" in result


def test_fix_performance_issues(mock_subprocess):
    """Test performance issue fixing"""
    result = AndroidProblemSolver.fix_performance_issues("test_device")

    assert "success" in result
    assert "steps" in result


def test_fix_wifi_issues(mock_subprocess):
    """Test WiFi fixing"""
    result = AndroidProblemSolver.fix_wifi_issues("test_device")

    assert "success" in result
    assert "steps" in result


def test_identify_and_suggest_improvements(mock_subprocess):
    """Test identifying problems and suggesting improvements"""
    result = AndroidProblemSolver.identify_and_suggest_improvements("test_device")

    assert result["device_id"] == "test_device"
    assert isinstance(result.get("suggestions"), list)
    assert len(result["suggestions"]) > 0


def test_emergency_factory_reset(mock_subprocess):
    """Test emergency factory reset"""
    # Should not execute without confirmation
    result = EmergencyRecovery.factory_reset_adb("test_device", confirm=False)
    assert result is False

    # Should execute with confirmation
    result = EmergencyRecovery.factory_reset_adb("test_device", confirm=True)
    assert isinstance(result, bool)


def test_force_boot_recovery(mock_subprocess):
    """Test force boot to recovery"""
    result = EmergencyRecovery.force_boot_recovery("test_device")
    assert isinstance(result, bool)

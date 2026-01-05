"""
Tests for Embedded Tools Manager

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from void.tools.embedded import EmbeddedToolsManager


@pytest.fixture
def temp_tools_dir():
    """Create temporary tools directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def tools_manager(temp_tools_dir):
    """Create tools manager with temp directory"""
    manager = EmbeddedToolsManager()
    manager.tools_dir = temp_tools_dir
    return manager


def test_get_tool_path_not_found(tools_manager):
    """Test getting tool path when tool doesn't exist"""
    path = tools_manager.get_tool_path("nonexistent")
    assert path is None


def test_get_adb_command(tools_manager):
    """Test getting ADB command"""
    cmd = tools_manager.get_adb_command()
    assert cmd in ["adb", str(tools_manager.tools_dir / "platform-tools" / "adb")]


def test_get_fastboot_command(tools_manager):
    """Test getting Fastboot command"""
    cmd = tools_manager.get_fastboot_command()
    assert cmd in ["fastboot", str(tools_manager.tools_dir / "platform-tools" / "fastboot")]


def test_test_tools(tools_manager):
    """Test tool testing"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        results = tools_manager.test_tools()

        assert "adb" in results
        assert "fastboot" in results

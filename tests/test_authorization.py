"""
Tests for Authorization System

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
"""

import pytest
from void.core.auth.authorization import AuthorizationManager, Permission, Role


def test_viewer_permissions():
    """Test viewer role permissions"""
    assert AuthorizationManager.has_permission('viewer', Permission.DEVICE_VIEW) is True
    assert AuthorizationManager.has_permission('viewer', Permission.BACKUP_CREATE) is False
    assert AuthorizationManager.has_permission('viewer', Permission.FRP_BYPASS) is False


def test_operator_permissions():
    """Test operator role permissions"""
    assert AuthorizationManager.has_permission('operator', Permission.DEVICE_VIEW) is True
    assert AuthorizationManager.has_permission('operator', Permission.BACKUP_CREATE) is True
    assert AuthorizationManager.has_permission('operator', Permission.APP_INSTALL) is True
    assert AuthorizationManager.has_permission('operator', Permission.FRP_BYPASS) is False


def test_advanced_permissions():
    """Test advanced role permissions"""
    assert AuthorizationManager.has_permission('advanced', Permission.FRP_BYPASS) is True
    assert AuthorizationManager.has_permission('advanced', Permission.EDL_ACCESS) is True
    assert AuthorizationManager.has_permission('advanced', Permission.USER_MANAGE) is False


def test_admin_permissions():
    """Test admin role has all permissions"""
    for permission in Permission:
        assert AuthorizationManager.has_permission('admin', permission) is True


def test_can_perform_action():
    """Test action permission checking"""
    assert AuthorizationManager.can_perform_action('operator', 'backup_device') is True
    assert AuthorizationManager.can_perform_action('viewer', 'backup_device') is False
    assert AuthorizationManager.can_perform_action('advanced', 'frp_bypass') is True
    assert AuthorizationManager.can_perform_action('operator', 'frp_bypass') is False


def test_invalid_role():
    """Test invalid role"""
    assert AuthorizationManager.has_permission('invalid_role', Permission.DEVICE_VIEW) is False

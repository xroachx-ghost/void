"""
Role-Based Access Control (RBAC) for Void Suite

Provides authorization and permission management.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

from enum import Enum
from typing import Set, Dict


class Permission(Enum):
    """System permissions"""

    # Device operations
    DEVICE_VIEW = "device:view"
    DEVICE_CONNECT = "device:connect"
    DEVICE_REBOOT = "device:reboot"

    # Backup operations
    BACKUP_CREATE = "backup:create"
    BACKUP_RESTORE = "backup:restore"
    BACKUP_DELETE = "backup:delete"

    # App operations
    APP_LIST = "app:list"
    APP_INSTALL = "app:install"
    APP_UNINSTALL = "app:uninstall"

    # System operations
    SYSTEM_TWEAK = "system:tweak"
    SYSTEM_ROOT = "system:root"
    USB_DEBUG = "system:usb_debug"

    # Advanced operations
    EDL_ACCESS = "advanced:edl"
    FRP_BYPASS = "advanced:frp"
    RECOVERY_MODE = "advanced:recovery"

    # Admin operations
    USER_MANAGE = "admin:users"
    AUDIT_VIEW = "admin:audit"
    CONFIG_MANAGE = "admin:config"


class Role(Enum):
    """User roles"""

    VIEWER = "viewer"
    OPERATOR = "operator"
    ADVANCED = "advanced"
    ADMIN = "admin"


# Role permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.DEVICE_VIEW,
        Permission.APP_LIST,
    },
    Role.OPERATOR: {
        Permission.DEVICE_VIEW,
        Permission.DEVICE_CONNECT,
        Permission.DEVICE_REBOOT,
        Permission.BACKUP_CREATE,
        Permission.BACKUP_RESTORE,
        Permission.APP_LIST,
        Permission.APP_INSTALL,
        Permission.APP_UNINSTALL,
        Permission.SYSTEM_TWEAK,
        Permission.USB_DEBUG,
    },
    Role.ADVANCED: {
        Permission.DEVICE_VIEW,
        Permission.DEVICE_CONNECT,
        Permission.DEVICE_REBOOT,
        Permission.BACKUP_CREATE,
        Permission.BACKUP_RESTORE,
        Permission.BACKUP_DELETE,
        Permission.APP_LIST,
        Permission.APP_INSTALL,
        Permission.APP_UNINSTALL,
        Permission.SYSTEM_TWEAK,
        Permission.SYSTEM_ROOT,
        Permission.USB_DEBUG,
        Permission.EDL_ACCESS,
        Permission.FRP_BYPASS,
        Permission.RECOVERY_MODE,
    },
    Role.ADMIN: set(Permission),  # All permissions
}


class AuthorizationManager:
    """Manages authorization and permissions"""

    @staticmethod
    def has_permission(role: str, permission: Permission) -> bool:
        """Check if role has permission"""
        try:
            role_enum = Role(role)
            return permission in ROLE_PERMISSIONS.get(role_enum, set())
        except ValueError:
            return False

    @staticmethod
    def get_role_permissions(role: str) -> Set[Permission]:
        """Get all permissions for a role"""
        try:
            role_enum = Role(role)
            return ROLE_PERMISSIONS.get(role_enum, set())
        except ValueError:
            return set()

    @staticmethod
    def can_perform_action(role: str, action: str) -> bool:
        """Check if role can perform an action"""
        # Map actions to permissions
        action_permission_map = {
            "backup_device": Permission.BACKUP_CREATE,
            "restore_backup": Permission.BACKUP_RESTORE,
            "install_app": Permission.APP_INSTALL,
            "uninstall_app": Permission.APP_UNINSTALL,
            "reboot_device": Permission.DEVICE_REBOOT,
            "usb_debugging": Permission.USB_DEBUG,
            "edl_mode": Permission.EDL_ACCESS,
            "frp_bypass": Permission.FRP_BYPASS,
            "manage_users": Permission.USER_MANAGE,
        }

        permission = action_permission_map.get(action)
        if permission is None:
            return False

        return AuthorizationManager.has_permission(role, permission)


def require_permission(permission: Permission):
    """Decorator to require permission for function"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get user context (from session or argument)
            user_role = kwargs.get("user_role", "viewer")

            if not AuthorizationManager.has_permission(user_role, permission):
                raise PermissionError(f"Permission denied: {permission.value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator

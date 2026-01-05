"""
Authorized debug enable workflows.

For use only on organization-owned devices or with explicit, written legal authorization.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from typing import Dict, List

from .logging import logger
from .utils import SafeSubprocess

# Placeholder variables for authorization enforcement.
LEGAL_AUTHORIZATION_TOKEN = "REPLACE_WITH_LEGAL_AUTHORIZATION_TOKEN"
DEVICE_OWNERSHIP_VERIFICATION = "REPLACE_WITH_DEVICE_OWNERSHIP_VERIFICATION"


class AuthorizationError(PermissionError):
    """Raised when authorization checks fail."""


def _authorization_valid(token: str, ownership: str) -> bool:
    return (
        bool(token and ownership)
        and token != LEGAL_AUTHORIZATION_TOKEN
        and ownership != DEVICE_OWNERSHIP_VERIFICATION
    )


def _ensure_authorized(token: str, ownership: str, action: str) -> None:
    if not _authorization_valid(token, ownership):
        logger.log("error", "compliance", f"Authorization check failed for {action}.")
        raise AuthorizationError("Authorization required for authorized debugging actions.")


def _adb_state(device_id: str) -> str:
    code, stdout, stderr = SafeSubprocess.run(["adb", "-s", device_id, "get-state"])
    if code != 0:
        logger.log(
            "warning", "audit", f"adb get-state failed: {stderr.strip()}", device_id=device_id
        )
        return "unknown"
    return stdout.strip()


def enable_debugging_settings(
    device_id: str,
    authorization_token: str,
    ownership_verification: str,
) -> Dict[str, object]:
    """Enable debugging-related settings for company device recovery."""
    _ensure_authorized(authorization_token, ownership_verification, "enable_debugging_settings")
    if _adb_state(device_id) != "device":
        logger.log(
            "warning",
            "compliance",
            "ADB not authorized; manual approval required.",
            device_id=device_id,
        )
        return {"success": False, "reason": "adb_not_authorized"}

    steps: List[Dict[str, object]] = []
    commands = [
        (
            "enable_dev_settings",
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "settings",
                "put",
                "global",
                "development_settings_enabled",
                "1",
            ],
        ),
        (
            "enable_adb",
            ["adb", "-s", device_id, "shell", "settings", "put", "global", "adb_enabled", "1"],
        ),
        (
            "set_usb_config",
            ["adb", "-s", device_id, "shell", "setprop", "persist.sys.usb.config", "mtp,adb"],
        ),
    ]

    for name, cmd in commands:
        code, _, stderr = SafeSubprocess.run(cmd)
        success = code == 0
        steps.append({"step": name, "success": success, "error": stderr.strip()})
        if not success:
            logger.log(
                "warning", "audit", f"Step {name} failed: {stderr.strip()}", device_id=device_id
            )

    logger.log(
        "info",
        "compliance",
        "Debugging settings updated for authorized device recovery.",
        device_id=device_id,
    )
    return {"success": all(step["success"] for step in steps), "steps": steps}


def restart_adbd(
    device_id: str,
    authorization_token: str,
    ownership_verification: str,
) -> Dict[str, object]:
    """Restart adbd for authorized penetration test automation."""
    _ensure_authorized(authorization_token, ownership_verification, "restart_adbd")
    if _adb_state(device_id) != "device":
        logger.log(
            "warning",
            "compliance",
            "ADB not authorized; adbd restart skipped.",
            device_id=device_id,
        )
        return {"success": False, "reason": "adb_not_authorized"}

    steps = []
    for name, cmd in (
        ("stop_adbd", ["adb", "-s", device_id, "shell", "stop", "adbd"]),
        ("start_adbd", ["adb", "-s", device_id, "shell", "start", "adbd"]),
    ):
        code, _, stderr = SafeSubprocess.run(cmd)
        steps.append({"step": name, "success": code == 0, "error": stderr.strip()})

    logger.log(
        "info", "audit", "adbd restart attempted for authorized testing.", device_id=device_id
    )
    return {"success": all(step["success"] for step in steps), "steps": steps}


def grant_debugging_authorization(
    device_id: str,
    authorization_token: str,
    ownership_verification: str,
) -> Dict[str, object]:
    """Document the requirement for manual RSA authorization without bypassing controls."""
    _ensure_authorized(authorization_token, ownership_verification, "grant_debugging_authorization")
    if _adb_state(device_id) != "device":
        logger.log(
            "warning",
            "compliance",
            "RSA authorization cannot be granted without prior user or MDM approval.",
            device_id=device_id,
        )
        return {"success": False, "reason": "adb_not_authorized"}

    logger.log(
        "info",
        "compliance",
        "RSA authorization must be confirmed via approved enterprise provisioning (no bypass executed).",
        device_id=device_id,
    )
    return {"success": False, "reason": "manual_authorization_required"}

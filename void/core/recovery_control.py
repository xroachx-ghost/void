from __future__ import annotations

"""Authorized recovery-mode controls.

For use only on organization-owned devices or with explicit, written legal authorization.
"""

from typing import Dict

from .logging import logger
from .utils import SafeSubprocess

# Placeholder variables for authorization enforcement.
LEGAL_AUTHORIZATION_TOKEN = "REPLACE_WITH_LEGAL_AUTHORIZATION_TOKEN"
DEVICE_OWNERSHIP_VERIFICATION = "REPLACE_WITH_DEVICE_OWNERSHIP_VERIFICATION"


class AuthorizationError(PermissionError):
    """Raised when authorization checks fail."""


def _authorization_valid(token: str, ownership: str) -> bool:
    return bool(token and ownership) and token != LEGAL_AUTHORIZATION_TOKEN and ownership != DEVICE_OWNERSHIP_VERIFICATION


def _ensure_authorized(token: str, ownership: str, action: str) -> None:
    if not _authorization_valid(token, ownership):
        logger.log("error", "compliance", f"Authorization check failed for {action}.")
        raise AuthorizationError("Authorization required for recovery actions.")


def reboot_to_fastboot(device_id: str, authorization_token: str, ownership_verification: str) -> Dict[str, object]:
    """Reboot to Fastboot for company device recovery."""
    _ensure_authorized(authorization_token, ownership_verification, "reboot_to_fastboot")
    code, _, stderr = SafeSubprocess.run(["adb", "-s", device_id, "reboot", "bootloader"])
    success = code == 0
    logger.log(
        "info" if success else "warning",
        "compliance",
        "Fastboot reboot issued for authorized device recovery.",
        device_id=device_id,
    )
    return {"success": success, "error": stderr.strip()}


def reboot_to_recovery(device_id: str, authorization_token: str, ownership_verification: str) -> Dict[str, object]:
    """Reboot to Recovery for forensic data preservation."""
    _ensure_authorized(authorization_token, ownership_verification, "reboot_to_recovery")
    code, _, stderr = SafeSubprocess.run(["adb", "-s", device_id, "reboot", "recovery"])
    success = code == 0
    logger.log(
        "info" if success else "warning",
        "compliance",
        "Recovery reboot issued for authorized imaging or repair.",
        device_id=device_id,
    )
    return {"success": success, "error": stderr.strip()}


def reboot_to_edl(device_id: str, authorization_token: str, ownership_verification: str) -> Dict[str, object]:
    """Reboot to EDL (Emergency Download Mode) using documented procedures."""
    _ensure_authorized(authorization_token, ownership_verification, "reboot_to_edl")
    code, _, stderr = SafeSubprocess.run(["adb", "-s", device_id, "reboot", "edl"])
    success = code == 0
    logger.log(
        "info" if success else "warning",
        "compliance",
        "EDL reboot issued for authorized firmware restoration with official tooling.",
        device_id=device_id,
    )
    return {"success": success, "error": stderr.strip()}


def reboot_to_download_mode(device_id: str, authorization_token: str, ownership_verification: str) -> Dict[str, object]:
    """Reboot to Download Mode for OEM-sanctioned firmware repair."""
    _ensure_authorized(authorization_token, ownership_verification, "reboot_to_download_mode")
    code, _, stderr = SafeSubprocess.run(["adb", "-s", device_id, "reboot", "download"])
    success = code == 0
    logger.log(
        "info" if success else "warning",
        "compliance",
        "Download mode reboot issued for authorized restoration.",
        device_id=device_id,
    )
    return {"success": success, "error": stderr.strip()}

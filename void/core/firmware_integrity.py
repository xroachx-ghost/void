"""
Firmware integrity tools for authorized recovery and forensic workflows.

For use only on organization-owned devices or with explicit, written legal authorization.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
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
        raise AuthorizationError("Authorization required for firmware actions.")


def flash_signed_firmware(
    device_id: str,
    partition: str,
    image_path: str,
    authorization_token: str,
    ownership_verification: str,
) -> Dict[str, object]:
    """Flash signed official firmware images for authorized recovery."""
    _ensure_authorized(authorization_token, ownership_verification, "flash_signed_firmware")
    image = Path(image_path)
    if not image.exists():
        logger.log("error", "compliance", f"Firmware image not found: {image_path}")
        return {"success": False, "error": "image_not_found"}
    if not partition.replace("_", "").isalnum():
        logger.log("error", "compliance", f"Invalid partition name: {partition}")
        return {"success": False, "error": "invalid_partition"}

    code, _, stderr = SafeSubprocess.run(["fastboot", "-s", device_id, "flash", partition, str(image)])
    success = code == 0
    logger.log(
        "info" if success else "warning",
        "compliance",
        "Firmware flash command issued for authorized recovery.",
        device_id=device_id,
    )
    return {"success": success, "error": stderr.strip()}


def hash_partition_via_adb(
    device_id: str,
    partition: str,
    authorization_token: str,
    ownership_verification: str,
) -> Dict[str, object]:
    """Generate SHA-256 hash of a partition for forensic integrity verification."""
    _ensure_authorized(authorization_token, ownership_verification, "hash_partition_via_adb")
    if not partition.replace("_", "").isalnum():
        logger.log("error", "compliance", f"Invalid partition name: {partition}")
        return {"success": False, "error": "invalid_partition"}

    cmd = ["adb", "-s", device_id, "shell", "sha256sum", f"/dev/block/by-name/{partition}"]
    code, stdout, stderr = SafeSubprocess.run(cmd)
    if code != 0:
        logger.log("warning", "audit", f"Partition hash failed: {stderr.strip()}", device_id=device_id)
        return {"success": False, "error": stderr.strip()}

    digest = stdout.strip().split()[0] if stdout.strip() else ""
    logger.log(
        "info",
        "compliance",
        "Partition hash captured for authorized forensic analysis.",
        device_id=device_id,
    )
    return {"success": bool(digest), "sha256": digest}


def dump_partition_via_adb(
    device_id: str,
    partition: str,
    output_path: str,
    authorization_token: str,
    ownership_verification: str,
) -> Dict[str, object]:
    """Dump a system partition for authorized static malware analysis."""
    _ensure_authorized(authorization_token, ownership_verification, "dump_partition_via_adb")
    if not partition.replace("_", "").isalnum():
        logger.log("error", "compliance", f"Invalid partition name: {partition}")
        return {"success": False, "error": "invalid_partition"}

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    device_tmp = f"/sdcard/void_dump_{partition}.img"

    dd_cmd = [
        "adb",
        "-s",
        device_id,
        "shell",
        "dd",
        f"if=/dev/block/by-name/{partition}",
        f"of={device_tmp}",
    ]
    code, _, stderr = SafeSubprocess.run(dd_cmd)
    if code != 0:
        logger.log("warning", "audit", f"Partition dump failed: {stderr.strip()}", device_id=device_id)
        return {"success": False, "error": stderr.strip()}

    pull_cmd = ["adb", "-s", device_id, "pull", device_tmp, str(output)]
    code, _, stderr = SafeSubprocess.run(pull_cmd)
    if code != 0:
        logger.log("warning", "audit", f"Partition pull failed: {stderr.strip()}", device_id=device_id)
        return {"success": False, "error": stderr.strip()}

    SafeSubprocess.run(["adb", "-s", device_id, "shell", "rm", "-f", device_tmp])

    sha256 = hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else ""
    logger.log(
        "info",
        "compliance",
        "Partition dump completed for authorized forensic preservation.",
        device_id=device_id,
    )
    return {"success": output.exists(), "output_path": str(output), "sha256": sha256}

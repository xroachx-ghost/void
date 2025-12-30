"""
Authorized device auditing.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

"""Authorized device auditing utilities.

For use only on organization-owned devices or with explicit, written legal authorization.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .logging import logger
from .utils import SafeSubprocess, check_tool

# Placeholder variables for authorization enforcement.
LEGAL_AUTHORIZATION_TOKEN = "REPLACE_WITH_LEGAL_AUTHORIZATION_TOKEN"
DEVICE_OWNERSHIP_VERIFICATION = "REPLACE_WITH_DEVICE_OWNERSHIP_VERIFICATION"

ANDROID_USB_VENDORS = {
    "18d1": "Google",
    "0bb4": "HTC",
    "04e8": "Samsung",
    "12d1": "Huawei",
    "2a70": "OnePlus",
    "0fce": "Sony",
    "05c6": "Qualcomm",
    "22b8": "Motorola",
    "2717": "Xiaomi",
    "17ef": "Lenovo",
}


class AuthorizationError(PermissionError):
    """Raised when authorization checks fail."""


def _authorization_valid(token: str, ownership: str) -> bool:
    return bool(token and ownership) and token != LEGAL_AUTHORIZATION_TOKEN and ownership != DEVICE_OWNERSHIP_VERIFICATION


def _ensure_authorized(token: str, ownership: str, action: str) -> None:
    if not _authorization_valid(token, ownership):
        logger.log(
            "error",
            "compliance",
            f"Authorization check failed for {action}.",
        )
        raise AuthorizationError("Authorization required for authorized forensic actions.")


@dataclass
class UsbAsset:
    bus: str
    device: str
    vendor_id: str
    product_id: str
    description: str
    android_candidate: bool


class AuthorizedDeviceAuditor:
    """Authorized device auditor for thorough asset discovery."""

    def __init__(
        self,
        authorization_token: str,
        ownership_verification: str,
        allowed_device_ids: Optional[List[str]] = None,
    ) -> None:
        self.authorization_token = authorization_token
        self.ownership_verification = ownership_verification
        self.allowed_device_ids = allowed_device_ids or []

    def _device_allowed(self, device_id: str) -> bool:
        if not self.allowed_device_ids:
            return True
        return device_id in self.allowed_device_ids

    def enumerate_usb_assets(self) -> List[UsbAsset]:
        """Enumerate USB devices for compliance inventory (authorized use only)."""
        _ensure_authorized(self.authorization_token, self.ownership_verification, "usb_enumeration")
        tool_result = check_tool("lsusb")
        if not tool_result.available:
            logger.log("warning", "audit", "lsusb not available; skipping USB enumeration.")
            return []

        code, stdout, stderr = SafeSubprocess.run(["lsusb"])
        if code != 0:
            logger.log("error", "audit", f"lsusb failed: {stderr.strip()}")
            return []

        assets: List[UsbAsset] = []
        for line in stdout.strip().splitlines():
            parts = line.split()
            if "ID" not in parts:
                continue
            try:
                bus = parts[1]
                device = parts[3].rstrip(":")
                id_index = parts.index("ID")
                vendor_product = parts[id_index + 1]
                vendor_id, product_id = vendor_product.split(":", maxsplit=1)
                description = " ".join(parts[id_index + 2 :])
            except (ValueError, IndexError):
                continue
            vendor_label = ANDROID_USB_VENDORS.get(vendor_id.lower())
            android_candidate = bool(vendor_label or "android" in description.lower())
            assets.append(
                UsbAsset(
                    bus=bus,
                    device=device,
                    vendor_id=vendor_id,
                    product_id=product_id,
                    description=description,
                    android_candidate=android_candidate,
                )
            )

        logger.log(
            "info",
            "audit",
            f"USB inventory collected: {len(assets)} assets enumerated for compliance review.",
        )
        return assets

    def detect_adb_devices(self) -> List[Dict[str, str]]:
        """Detect ADB-connected devices for authorized device recovery."""
        _ensure_authorized(self.authorization_token, self.ownership_verification, "adb_inventory")
        code, stdout, stderr = SafeSubprocess.run(["adb", "devices", "-l"])
        if code != 0:
            logger.log("error", "audit", f"adb devices failed: {stderr.strip()}")
            return []

        devices: List[Dict[str, str]] = []
        for line in stdout.strip().splitlines():
            if not line or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            device_id = parts[0]
            if not self._device_allowed(device_id):
                logger.log("warning", "compliance", f"Device {device_id} not in authorized allowlist.")
                continue
            state = parts[1]
            metadata = {"device_id": device_id, "state": state, "mode": "adb"}
            for entry in parts[2:]:
                if ":" in entry:
                    key, value = entry.split(":", 1)
                    metadata[key] = value
            devices.append(metadata)

        logger.log(
            "info",
            "audit",
            f"ADB inventory collected: {len(devices)} device(s) detected for authorized audits.",
        )
        return devices

    def detect_fastboot_devices(self) -> List[Dict[str, str]]:
        """Detect Fastboot-connected devices for authorized recovery workflows."""
        _ensure_authorized(self.authorization_token, self.ownership_verification, "fastboot_inventory")
        code, stdout, stderr = SafeSubprocess.run(["fastboot", "devices"])
        if code != 0:
            logger.log("error", "audit", f"fastboot devices failed: {stderr.strip()}")
            return []

        devices: List[Dict[str, str]] = []
        for line in stdout.strip().splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            device_id, mode = parts[0], parts[1]
            if not self._device_allowed(device_id):
                logger.log("warning", "compliance", f"Device {device_id} not in authorized allowlist.")
                continue
            devices.append({"device_id": device_id, "state": mode, "mode": "fastboot"})

        logger.log(
            "info",
            "audit",
            f"Fastboot inventory collected: {len(devices)} device(s) detected.",
        )
        return devices

    def build_asset_inventory(self) -> Dict[str, object]:
        """Build a compliance-ready asset inventory for chain-of-custody records."""
        _ensure_authorized(self.authorization_token, self.ownership_verification, "asset_inventory")
        inventory = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "usb_assets": [asset.__dict__ for asset in self.enumerate_usb_assets()],
            "adb_devices": self.detect_adb_devices(),
            "fastboot_devices": self.detect_fastboot_devices(),
        }
        logger.log(
            "info",
            "compliance",
            "Asset inventory captured for authorized device recovery and forensic auditing.",
        )
        return inventory

    def log_inventory(self, inventory: Dict[str, object]) -> None:
        """Log inventory details for compliance and chain-of-custody."""
        _ensure_authorized(self.authorization_token, self.ownership_verification, "inventory_logging")
        adb_count = len(inventory.get("adb_devices", []))
        fastboot_count = len(inventory.get("fastboot_devices", []))
        usb_count = len(inventory.get("usb_assets", []))
        logger.log(
            "info",
            "compliance",
            f"Inventory logged: {adb_count} ADB, {fastboot_count} Fastboot, {usb_count} USB assets.",
        )
        for device in inventory.get("adb_devices", []):
            logger.log(
                "info",
                "compliance",
                f"ADB device recorded for authorized audit: {device.get('device_id')}",
                device_id=device.get("device_id"),
            )
        for device in inventory.get("fastboot_devices", []):
            logger.log(
                "info",
                "compliance",
                f"Fastboot device recorded for authorized audit: {device.get('device_id')}",
                device_id=device.get("device_id"),
            )

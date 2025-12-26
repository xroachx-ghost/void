from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .device import DeviceDetector


@dataclass(frozen=True)
class SmartDeviceChoice:
    device_id: str
    reason: str
    device: Dict[str, Any]


class SmartAdvisor:
    """Smart selection and recommendations for the CLI."""

    @staticmethod
    def pick_device(
        last_device_id: Optional[str],
        prefer_last: bool = True,
    ) -> Optional[SmartDeviceChoice]:
        devices, _ = DeviceDetector.detect_all()
        if not devices:
            return None

        if prefer_last and last_device_id:
            match = next((device for device in devices if device.get("id") == last_device_id), None)
            if match:
                return SmartDeviceChoice(
                    device_id=last_device_id,
                    reason="last-device",
                    device=match,
                )

        reachable = [
            device
            for device in devices
            if device.get("reachable") or device.get("status") == "device"
        ]
        if len(reachable) == 1:
            device = reachable[0]
            return SmartDeviceChoice(
                device_id=device.get("id", "unknown"),
                reason="single-reachable",
                device=device,
            )

        if len(devices) == 1:
            device = devices[0]
            return SmartDeviceChoice(
                device_id=device.get("id", "unknown"),
                reason="single-device",
                device=device,
            )

        return None

    @staticmethod
    def summarize_choice(choice: SmartDeviceChoice) -> str:
        device = choice.device
        model = device.get("model", "Unknown")
        brand = device.get("brand") or device.get("manufacturer") or "Unknown"
        mode = device.get("mode", "Unknown")
        return f"{choice.device_id} • {brand} {model} • {mode}"

    @staticmethod
    def recommend_actions(
        devices: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
    ) -> List[str]:
        suggestions: List[str] = []
        if errors:
            suggestions.append("Run `doctor` to review tool availability and errors.")
        if not devices:
            suggestions.extend(
                [
                    "Connect a device and run `devices` to verify detection.",
                    "Run `adb` to verify Android platform tools are on PATH.",
                ]
            )
            return suggestions

        adb_devices = [device for device in devices if device.get("mode") == "adb"]
        if adb_devices:
            suggestions.append("Run `summary` for a quick overview of connected devices.")
            suggestions.append("Run `info <device_id>` for detailed device metadata.")

        if any(device.get("mode") == "fastboot" for device in devices):
            suggestions.append("Run `edl-status <device_id>` to check low-level modes.")

        if len(devices) == 1:
            suggestions.append("Use `analyze` or `report` to generate a full device report.")

        return suggestions

    @staticmethod
    def format_errors(errors: List[Dict[str, Any]]) -> List[str]:
        formatted: List[str] = []
        for error in errors:
            source = error.get("source", "unknown")
            stderr = error.get("stderr", "").strip()
            message = error.get("message", "")
            detail = stderr or message or "unknown error"
            formatted.append(f"{source}: {detail}")
        return formatted

    @staticmethod
    def snapshot() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        return DeviceDetector.detect_all()

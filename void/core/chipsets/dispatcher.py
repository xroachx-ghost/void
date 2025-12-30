"""
Chipset dispatcher and detection.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from typing import Iterable

from .base import BaseChipsetProtocol, ChipsetActionResult, ChipsetDetection
from .generic import GenericChipset
from .mediatek import MediaTekChipset
from .qualcomm import QualcommChipset
from .samsung import SamsungExynosChipset
from .utils import normalize_text
from ..recovery_control import (
    AuthorizationError,
    reboot_to_download_mode,
    reboot_to_edl,
    reboot_to_fastboot,
    reboot_to_recovery,
)


_CHIPSET_IMPLEMENTATIONS: tuple[BaseChipsetProtocol, ...] = (
    QualcommChipset(),
    MediaTekChipset(),
    SamsungExynosChipset(),
    GenericChipset(),
)


def resolve_chipset(context: dict[str, str], override: str | None = None) -> BaseChipsetProtocol:
    """Resolve a chipset implementation for the given context."""
    if override:
        for chipset in _CHIPSET_IMPLEMENTATIONS:
            if chipset.name.lower() == override.lower():
                return chipset
        return GenericChipset()

    detection = detect_chipset_for_device(context)
    if detection:
        for chipset in _CHIPSET_IMPLEMENTATIONS:
            if chipset.name == detection.chipset:
                return chipset
    return GenericChipset()


def detect_chipset_for_device(context: dict[str, str]) -> ChipsetDetection | None:
    """Run chipset detection across known implementations."""
    best: ChipsetDetection | None = None
    for chipset in _CHIPSET_IMPLEMENTATIONS:
        detection = chipset.detect(context)
        if not detection:
            continue
        if not best or detection.confidence > best.confidence:
            best = detection
    return best


def enter_chipset_mode(
    context: dict[str, str],
    target_mode: str,
    override: str | None = None,
) -> ChipsetActionResult:
    """Dispatch an enter-mode request to the resolved chipset."""
    chipset = resolve_chipset(context, override=override)
    return chipset.enter_mode(context, target_mode)


def enter_device_mode(
    context: dict[str, str],
    target_mode: str,
    override: str | None = None,
    authorization_token: str | None = None,
    ownership_verification: str | None = None,
) -> ChipsetActionResult:
    """Enter a target mode with authorization gating and guided fallback steps."""
    detection = detect_chipset_for_device(context)
    chipset_name = detection.chipset if detection else "Unknown"
    current_mode = normalize_text(context.get("mode")) or "unknown"
    device_id = context.get("id")
    target_lower = normalize_text(target_mode)

    def manual_steps_for_target() -> list[str]:
        if target_lower in {"fastboot", "bootloader"}:
            return [
                "Power the device completely off.",
                "Hold Volume Down + Power until the bootloader/fastboot screen appears.",
                "Confirm the host sees the device with `fastboot devices`.",
            ]
        if target_lower == "recovery":
            return [
                "Power the device completely off.",
                "Hold Volume Up + Power (or Volume Up + Bixby/Side Key) until recovery appears.",
                "Use the hardware keys to navigate recovery if touch is unavailable.",
            ]
        if target_lower == "system":
            return [
                "Hold Power until the device reboots back to system.",
                "If the device is in a bootloop, disconnect USB and retry.",
            ]
        return []

    def resolve_manual_steps() -> list[str]:
        fallback = manual_steps_for_target()
        chipset_result = enter_chipset_mode(context, target_mode, override=override)
        if isinstance(chipset_result.data, dict):
            manual_steps = chipset_result.data.get("manual_steps")
            if isinstance(manual_steps, (list, tuple)):
                return [str(step) for step in manual_steps if str(step).strip()]
            if isinstance(manual_steps, str) and manual_steps.strip():
                return [step.strip() for step in manual_steps.splitlines() if step.strip()]
        return fallback

    adb_transitions = {
        "fastboot": (reboot_to_fastboot, "fastboot"),
        "bootloader": (reboot_to_fastboot, "bootloader"),
        "recovery": (reboot_to_recovery, "recovery"),
        "edl": (reboot_to_edl, "edl"),
        "download": (reboot_to_download_mode, "download mode"),
        "odin": (reboot_to_download_mode, "download/odin mode"),
    }

    if device_id and current_mode == "adb" and target_lower in adb_transitions:
        auth_token = authorization_token or context.get("authorization_token") or ""
        ownership = ownership_verification or context.get("ownership_verification") or ""
        action, label = adb_transitions[target_lower]
        try:
            result = action(device_id, auth_token, ownership)
        except AuthorizationError as exc:
            return ChipsetActionResult(
                success=False,
                message=str(exc),
                data={
                    "chipset": chipset_name,
                    "target_mode": target_lower,
                    "current_mode": current_mode,
                    "manual_steps": resolve_manual_steps(),
                },
            )

        if result.get("success"):
            return ChipsetActionResult(
                success=True,
                message=f"Authorized ADB reboot to {label} issued.",
                data={
                    "device_id": device_id,
                    "chipset": chipset_name,
                    "target_mode": target_lower,
                    "current_mode": current_mode,
                },
            )
        return ChipsetActionResult(
            success=False,
            message=f"Failed to issue ADB reboot to {label}.",
            data={
                "device_id": device_id,
                "chipset": chipset_name,
                "target_mode": target_lower,
                "current_mode": current_mode,
                "error": result.get("error"),
                "manual_steps": resolve_manual_steps(),
            },
        )

    result = enter_chipset_mode(context, target_mode, override=override)
    manual_steps = result.data.get("manual_steps") if isinstance(result.data, dict) else None
    fallback_steps = manual_steps_for_target() if not manual_steps else manual_steps
    if fallback_steps and not result.success:
        data = dict(result.data or {})
        data.setdefault("chipset", chipset_name)
        data.setdefault("target_mode", target_lower)
        data.setdefault("current_mode", current_mode)
        data.setdefault("manual_steps", fallback_steps)
        return ChipsetActionResult(success=result.success, message=result.message, data=data)
    return result


def recover_chipset_device(
    context: dict[str, str],
    override: str | None = None,
) -> ChipsetActionResult:
    """Dispatch a recovery request to the resolved chipset."""
    chipset = resolve_chipset(context, override=override)
    return chipset.recover(context)


def list_chipsets() -> Iterable[BaseChipsetProtocol]:
    """Return registered chipset implementations."""
    return _CHIPSET_IMPLEMENTATIONS

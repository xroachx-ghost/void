"""
Qualcomm chipset support.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .base import ChipsetActionResult, ChipsetDetection
from .utils import extract_usb_ids, match_any, normalize_text
from ..tools.qualcomm import resolve_qualcomm_recovery_tool


class QualcommChipset:
    """Qualcomm EDL/Sahara/Firehose workflows."""

    name = "Qualcomm"
    vendor = "Qualcomm"
    supported_modes = ("adb", "fastboot", "edl")

    _QUALCOMM_VIDS = {"05c6"}
    _QUALCOMM_PIDS = {"9008", "900e"}
    _PLATFORM_TOKENS = ("qcom", "qualcomm", "msm", "sdm", "sm", "kona")

    def detect(self, context: dict[str, str]) -> ChipsetDetection | None:
        usb_ids = extract_usb_ids(context)
        if usb_ids:
            vid, pid = usb_ids
            if vid in self._QUALCOMM_VIDS and pid in self._QUALCOMM_PIDS:
                return ChipsetDetection(
                    chipset=self.name,
                    vendor=self.vendor,
                    mode="edl",
                    confidence=0.95,
                    notes=("Qualcomm 9008 (EDL) USB ID detected.",),
                    metadata={"usb_vid": vid, "usb_pid": pid},
                )

        if match_any(
            context.get("usb_vendor") or context.get("chipset_vendor") or context.get("chipset_vendor_hint"),
            ("qualcomm", "qcom"),
        ):
            return ChipsetDetection(
                chipset=self.name,
                vendor=self.vendor,
                mode=normalize_text(context.get("mode")) or "usb-unknown",
                confidence=0.5,
                notes=("Matched Qualcomm USB vendor hint.",),
                metadata={"usb_vendor": normalize_text(context.get("usb_vendor"))},
            )

        for key in ("chipset", "hardware", "product", "device", "bootloader"):
            if match_any(context.get(key), self._PLATFORM_TOKENS):
                return ChipsetDetection(
                    chipset=self.name,
                    vendor=self.vendor,
                    mode=normalize_text(context.get("mode")) or "unknown",
                    confidence=0.65,
                    notes=(f"Matched Qualcomm platform token in {key}.",),
                    metadata={"matched_field": key},
                )

        return None

    def enter_mode(self, context: dict[str, str], target_mode: str) -> ChipsetActionResult:
        if target_mode.lower() != "edl":
            return ChipsetActionResult(
                success=False,
                message=f"Qualcomm workflow only supports EDL entry (requested {target_mode}).",
            )

        return ChipsetActionResult(
            success=False,
            message="EDL entry requires authorized ADB access or a manual test-point trigger.",
            data={
                "target_mode": "edl",
                "manual_steps": [
                    "Power the device completely off (hold Power for 10-15s).",
                    "Hold Volume Up + Volume Down while connecting USB, or use the model-specific test-point.",
                    "Keep the keys/test-point held until the device enumerates on USB.",
                    "USB detection check: look for VID:PID 05c6:9008 or 05c6:900e in Device Manager/lsusb.",
                    "If not detected, try a different USB port/cable and repeat the sequence.",
                ],
            },
        )

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        tool_name, metadata = resolve_qualcomm_recovery_tool()
        if tool_name:
            return ChipsetActionResult(
                success=True,
                message=f"Qualcomm recovery tool '{tool_name}' is available for Sahara/Firehose flows.",
                data={"tool": tool_name, **metadata},
            )

        error = metadata.get("error", {})
        message = error.get("message", "No Qualcomm recovery tools found (edl/qdl/emmcdl).")
        return ChipsetActionResult(
            success=False,
            message=message,
            data={"error": error, **metadata},
        )

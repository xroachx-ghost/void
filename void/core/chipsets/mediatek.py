"""
MediaTek chipset support.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .base import ChipsetActionResult, ChipsetDetection
from .utils import extract_usb_ids, match_any, normalize_text
from ..tools.mediatek import resolve_mediatek_recovery_tool


class MediaTekChipset:
    """MediaTek preloader/bootrom workflows."""

    name = "MediaTek"
    vendor = "MediaTek"
    supported_modes = ("adb", "fastboot", "preloader", "bootrom")

    _MTK_VIDS = {"0e8d"}
    _PRELOADER_PIDS = {"2000", "2001"}
    _BOOTROM_PIDS = {"0003"}
    _PLATFORM_TOKENS = ("mediatek", "mt", "mtk")

    def detect(self, context: dict[str, str]) -> ChipsetDetection | None:
        usb_ids = extract_usb_ids(context)
        if usb_ids:
            vid, pid = usb_ids
            if vid in self._MTK_VIDS and pid in self._PRELOADER_PIDS:
                return ChipsetDetection(
                    chipset=self.name,
                    vendor=self.vendor,
                    mode="preloader",
                    confidence=0.9,
                    notes=("MediaTek preloader USB ID detected.",),
                    metadata={"usb_vid": vid, "usb_pid": pid},
                )
            if vid in self._MTK_VIDS and pid in self._BOOTROM_PIDS:
                return ChipsetDetection(
                    chipset=self.name,
                    vendor=self.vendor,
                    mode="bootrom",
                    confidence=0.9,
                    notes=("MediaTek bootrom USB ID detected.",),
                    metadata={"usb_vid": vid, "usb_pid": pid},
                )

        if match_any(
            context.get("usb_vendor")
            or context.get("chipset_vendor")
            or context.get("chipset_vendor_hint"),
            ("mediatek", "mtk"),
        ):
            return ChipsetDetection(
                chipset=self.name,
                vendor=self.vendor,
                mode=normalize_text(context.get("mode")) or "usb-unknown",
                confidence=0.5,
                notes=("Matched MediaTek USB vendor hint.",),
                metadata={"usb_vendor": normalize_text(context.get("usb_vendor"))},
            )

        for key in ("chipset", "hardware", "product", "device", "bootloader"):
            if match_any(context.get(key), self._PLATFORM_TOKENS):
                return ChipsetDetection(
                    chipset=self.name,
                    vendor=self.vendor,
                    mode=normalize_text(context.get("mode")) or "unknown",
                    confidence=0.6,
                    notes=(f"Matched MediaTek platform token in {key}.",),
                    metadata={"matched_field": key},
                )

        return None

    def enter_mode(self, context: dict[str, str], target_mode: str) -> ChipsetActionResult:
        if target_mode.lower() not in {"preloader", "bootrom"}:
            return ChipsetActionResult(
                success=False,
                message=f"MediaTek workflows support preloader/bootrom entry (requested {target_mode}).",
            )

        target = target_mode.lower()
        usb_hint = "0e8d:2000/2001 (preloader) or 0e8d:0003 (bootrom)"
        if target == "preloader":
            mode_steps = [
                "Power the device completely off (hold Power for 10-15s).",
                "Hold Volume Up or Volume Down, then connect USB to trigger preloader.",
                "If the device disconnects quickly, repeat and keep the key held.",
            ]
        else:
            mode_steps = [
                "Power the device completely off (hold Power for 10-15s).",
                "Use the documented test-point to ground while connecting USB.",
                "Keep the test-point bridged until USB enumeration completes.",
            ]

        return ChipsetActionResult(
            success=False,
            message="MediaTek entry requires hardware key combos or a test-point trigger.",
            data={
                "target_mode": target,
                "manual_steps": [
                    *mode_steps,
                    "Confirm the USB device shows up as MediaTek in the host OS.",
                    f"USB detection check: look for VID:PID {usb_hint}.",
                    "If not detected, re-seat the cable and retry the key/test-point sequence.",
                ],
            },
        )

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        tool_name, metadata = resolve_mediatek_recovery_tool()
        if tool_name:
            return ChipsetActionResult(
                success=True,
                message=f"MediaTek recovery tool '{tool_name}' is available for preloader/bootrom flows.",
                data={"tool": tool_name, **metadata},
            )

        error = metadata.get("error", {})
        message = error.get(
            "message", "No MediaTek recovery tools found (mtkclient/SP Flash Tool)."
        )
        return ChipsetActionResult(
            success=False,
            message=message,
            data={"error": error, **metadata},
        )

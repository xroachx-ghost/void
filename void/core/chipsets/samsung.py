"""Samsung Exynos chipset workflows."""

"""
Samsung chipset support.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .base import ChipsetActionResult, ChipsetDetection
from .utils import extract_usb_ids, match_any, normalize_text


class SamsungExynosChipset:
    """Samsung Exynos download/odin workflows."""

    name = "Samsung Exynos"
    vendor = "Samsung"
    supported_modes = ("adb", "fastboot", "download", "odin")

    _SAMSUNG_VIDS = {"04e8"}
    _DOWNLOAD_PIDS = {"685d", "6860"}
    _PLATFORM_TOKENS = ("exynos", "samsung", "universal")

    def detect(self, context: dict[str, str]) -> ChipsetDetection | None:
        usb_ids = extract_usb_ids(context)
        if usb_ids:
            vid, pid = usb_ids
            if vid in self._SAMSUNG_VIDS and pid in self._DOWNLOAD_PIDS:
                return ChipsetDetection(
                    chipset=self.name,
                    vendor=self.vendor,
                    mode="download",
                    confidence=0.9,
                    notes=("Samsung download mode USB ID detected.",),
                    metadata={"usb_vid": vid, "usb_pid": pid},
                )

        if match_any(
            context.get("usb_vendor") or context.get("chipset_vendor") or context.get("chipset_vendor_hint"),
            ("samsung",),
        ):
            return ChipsetDetection(
                chipset=self.name,
                vendor=self.vendor,
                mode=normalize_text(context.get("mode")) or "usb-unknown",
                confidence=0.5,
                notes=("Matched Samsung USB vendor hint.",),
                metadata={"usb_vendor": normalize_text(context.get("usb_vendor"))},
            )

        for key in ("chipset", "hardware", "product", "device", "bootloader", "manufacturer"):
            if match_any(context.get(key), self._PLATFORM_TOKENS):
                return ChipsetDetection(
                    chipset=self.name,
                    vendor=self.vendor,
                    mode=normalize_text(context.get("mode")) or "unknown",
                    confidence=0.55,
                    notes=(f"Matched Samsung/Exynos platform token in {key}.",),
                    metadata={"matched_field": key},
                )

        return None

    def enter_mode(self, context: dict[str, str], target_mode: str) -> ChipsetActionResult:
        target = target_mode.lower()
        if target not in {"download", "odin"}:
            return ChipsetActionResult(
                success=False,
                message=f"Samsung workflows support download/odin entry (requested {target_mode}).",
            )

        return ChipsetActionResult(
            success=False,
            message="Samsung download/odin workflows require manual key combos or OEM tooling.",
            data={
                "target_mode": target,
                "manual_steps": [
                    "Power the device completely off.",
                    "Hold Volume Down + Power + Bixby/Home until the warning screen appears.",
                    "Press Volume Up to confirm Download/Odin mode.",
                    "Alternative (newer models): hold Volume Up + Volume Down and plug in USB.",
                    "USB detection check: look for VID:PID 04e8:685d or 04e8:6860.",
                ],
            },
        )

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        return ChipsetActionResult(
            success=False,
            message="Samsung Exynos recovery requires vendor-provided tooling.",
        )

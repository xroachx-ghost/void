"""Generic chipset placeholder."""

"""
Generic chipset support.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .base import ChipsetActionResult, ChipsetDetection
from .utils import normalize_text


class GenericChipset:
    """Fallback chipset with detection-only warnings."""

    name = "Generic"
    vendor = "Unknown"
    supported_modes = ("adb", "fastboot")

    def detect(self, context: dict[str, str]) -> ChipsetDetection | None:
        mode = normalize_text(context.get("mode")) or "unknown"
        return ChipsetDetection(
            chipset=self.name,
            vendor=self.vendor,
            mode=mode,
            confidence=0.1,
            notes=("Generic chipset placeholder. Vendor tooling may be required.",),
            metadata={},
        )

    def enter_mode(self, context: dict[str, str], target_mode: str) -> ChipsetActionResult:
        return ChipsetActionResult(
            success=False,
            message="Generic chipset cannot enter modes automatically. Vendor tooling required.",
        )

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        return ChipsetActionResult(
            success=False,
            message="Generic chipset recovery unavailable. Vendor tooling required.",
        )

"""Samsung Exynos chipset workflows."""

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
        return ChipsetActionResult(
            success=False,
            message="Samsung download/odin workflows require vendor tooling and user confirmation.",
        )

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        return ChipsetActionResult(
            success=False,
            message="Samsung Exynos recovery requires vendor-provided tooling.",
        )

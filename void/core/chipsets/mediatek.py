"""MediaTek chipset workflows."""

from __future__ import annotations

from .base import ChipsetActionResult, ChipsetDetection
from .utils import extract_usb_ids, match_any, normalize_text
from ..utils import SafeSubprocess


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

        return ChipsetActionResult(
            success=False,
            message="MediaTek entry requires hardware key combos or a test-point trigger.",
        )

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        for tool in ("mtkclient", "spflashtool"):
            code, stdout, stderr = SafeSubprocess.run(["which", tool])
            if code == 0 and stdout.strip():
                return ChipsetActionResult(
                    success=True,
                    message=f"MediaTek recovery tool '{tool}' is available for preloader/bootrom flows.",
                    data={"tool": tool},
                )

        return ChipsetActionResult(
            success=False,
            message="No MediaTek recovery tools found (mtkclient/spflashtool).",
        )

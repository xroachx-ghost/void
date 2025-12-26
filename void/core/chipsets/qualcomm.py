"""Qualcomm chipset workflows."""

from __future__ import annotations

from .base import ChipsetActionResult, ChipsetDetection
from .utils import extract_usb_ids, match_any, normalize_text
from ..utils import SafeSubprocess


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

        device_id = context.get("id")
        mode = normalize_text(context.get("mode"))
        if device_id and mode == "adb":
            code, _, stderr = SafeSubprocess.run(["adb", "-s", device_id, "reboot", "edl"])
            if code == 0:
                return ChipsetActionResult(
                    success=True,
                    message="ADB reboot to EDL issued.",
                    data={"device_id": device_id},
                )
            return ChipsetActionResult(
                success=False,
                message="Failed to issue ADB reboot to EDL.",
                data={"error": stderr or "unknown"},
            )

        return ChipsetActionResult(
            success=False,
            message="EDL entry requires ADB access or a manual test-point trigger.",
        )

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        for tool in ("edl", "qdl", "emmcdl"):
            code, stdout, stderr = SafeSubprocess.run(["which", tool])
            if code == 0 and stdout.strip():
                return ChipsetActionResult(
                    success=True,
                    message=f"Qualcomm recovery tool '{tool}' is available for Sahara/Firehose flows.",
                    data={"tool": tool},
                )

        return ChipsetActionResult(
            success=False,
            message="No Qualcomm recovery tools found (edl/qdl/emmcdl). Install a tool to proceed.",
        )

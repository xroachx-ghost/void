"""
EDL tool wrappers for chipset-aware workflows.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .chipsets.base import ChipsetActionResult
from .chipsets.dispatcher import detect_chipset_for_device
from ..config import Config
from .utils import SafeSubprocess


_QUALCOMM_TOOLS = ("qdl", "edl", "emmcdl")


def _find_tool(candidates: tuple[str, ...]) -> str | None:
    for tool in candidates:
        code, stdout, _ = SafeSubprocess.run(["which", tool])
        if code == 0 and stdout.strip():
            return tool
    return None


def _build_flash_command(tool: str, loader: str, image: str) -> list[str] | None:
    if tool == "qdl":
        return [tool, "--loader", loader, "--storage", "emmc", image]
    if tool == "edl":
        return [tool, "--loader", loader, "--flash", image]
    if tool == "emmcdl":
        return [tool, "-f", loader, "-i", image]
    return None


def _build_dump_command(tool: str, partition: str, output: Path) -> list[str] | None:
    if tool == "edl":
        return [tool, "--read", partition, "--output", str(output)]
    if tool == "emmcdl":
        return [tool, "-d", partition, "-o", str(output)]
    return None


def edl_flash(context: dict[str, str], loader: str, image: str) -> ChipsetActionResult:
    """Attempt an EDL flash using chipset-specific tooling."""
    detection = detect_chipset_for_device(context)
    if not detection or detection.chipset != "Qualcomm":
        chipset = detection.chipset if detection else "Unknown"
        return ChipsetActionResult(
            success=False,
            message=f"EDL flash is only supported for Qualcomm devices (detected {chipset}).",
        )

    tool = _find_tool(_QUALCOMM_TOOLS)
    if not tool:
        return ChipsetActionResult(
            success=False,
            message="No Qualcomm EDL tooling found (qdl/edl/emmcdl). Install one to proceed.",
        )

    command = _build_flash_command(tool, loader, image)
    if not command:
        return ChipsetActionResult(
            success=False,
            message=f"Tool '{tool}' does not support flash operations in this wrapper.",
        )

    code, _, stderr = SafeSubprocess.run(command)
    if code == 0:
        return ChipsetActionResult(
            success=True,
            message=f"EDL flash issued via {tool}.",
            data={"tool": tool, "command": " ".join(command)},
        )
    return ChipsetActionResult(
        success=False,
        message="EDL flash failed.",
        data={"tool": tool, "error": stderr or "unknown", "command": " ".join(command)},
    )


def edl_dump(context: dict[str, str], partition: str) -> ChipsetActionResult:
    """Attempt an EDL partition dump using chipset-specific tooling."""
    detection = detect_chipset_for_device(context)
    if not detection or detection.chipset != "Qualcomm":
        chipset = detection.chipset if detection else "Unknown"
        return ChipsetActionResult(
            success=False,
            message=f"EDL dump is only supported for Qualcomm devices (detected {chipset}).",
        )

    tool = _find_tool(_QUALCOMM_TOOLS)
    if not tool:
        return ChipsetActionResult(
            success=False,
            message="No Qualcomm EDL tooling found (qdl/edl/emmcdl). Install one to proceed.",
        )

    Config.setup()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_partition = partition.replace("/", "_")
    output = Config.EXPORTS_DIR / f"edl_dump_{safe_partition}_{timestamp}.bin"

    command = _build_dump_command(tool, partition, output)
    if not command:
        return ChipsetActionResult(
            success=False,
            message=f"Tool '{tool}' does not support dump operations in this wrapper.",
        )

    code, _, stderr = SafeSubprocess.run(command)
    if code == 0:
        return ChipsetActionResult(
            success=True,
            message=f"EDL dump issued via {tool}.",
            data={"tool": tool, "command": " ".join(command), "output": str(output)},
        )
    return ChipsetActionResult(
        success=False,
        message="EDL dump failed.",
        data={"tool": tool, "error": stderr or "unknown", "command": " ".join(command)},
    )

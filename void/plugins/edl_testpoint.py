"""
EDL/Test-Point workflow plugin.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from typing import Sequence

from void.core.chipsets.dispatcher import (
    detect_chipset_for_device,
    enter_chipset_mode,
    recover_chipset_device,
)

from .base import PluginContext, PluginFeature, PluginMetadata, PluginResult
from .registry import register_plugin


@register_plugin
class EDLTestPointPlugin(PluginFeature):
    """Plugin entry point for EDL/Test-Point workflows."""

    metadata = PluginMetadata(
        id="edl-testpoint",
        name="EDL/Test-Point",
        description="Chipset-aware entry and recovery flows for EDL/Test-Point.",
        version="1.0.0",
        author="Void",
        tags=("chipset", "edl", "recovery", "cli", "gui"),
    )

    def run(self, context: PluginContext, args: Sequence[str]) -> PluginResult:
        request = "detect"
        target_mode = "edl"
        override = None
        device_id = None
        mode = context.mode

        for arg in args:
            if arg.startswith("--mode="):
                target_mode = arg.split("=", 1)[1]
            elif arg.startswith("--override="):
                override = arg.split("=", 1)[1]
            elif arg.startswith("--device="):
                device_id = arg.split("=", 1)[1]
            elif arg in {"detect", "enter", "recover"}:
                request = arg

        device_context = {
            "id": device_id or "",
            "mode": mode,
        }

        if request == "detect":
            detection = detect_chipset_for_device(device_context)
            if not detection:
                return PluginResult(success=False, message="No chipset detected.")
            if context.emit:
                context.emit(
                    f"Detected chipset: {detection.chipset} "
                    f"({detection.vendor}) mode={detection.mode}"
                )
            return PluginResult(
                success=True,
                message="Chipset detection complete.",
                data={
                    "chipset": detection.chipset,
                    "vendor": detection.vendor,
                    "mode": detection.mode,
                    "confidence": str(detection.confidence),
                },
            )

        if request == "enter":
            result = enter_chipset_mode(device_context, target_mode, override=override)
        else:
            result = recover_chipset_device(device_context, override=override)

        if context.emit:
            context.emit(result.message)

        return PluginResult(success=result.success, message=result.message, data=result.data)

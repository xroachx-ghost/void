"""
MediaTek tool wrappers.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from pathlib import Path

from .android import resolve_android_fallback
from .base import ToolSpec, check_tool_specs, first_available
from ..utils import ToolCheckResult


MTKCLIENT_SPEC = ToolSpec(name="mtkclient", version_args=("--version",), label="mtkclient")
SP_FLASH_SPECS = (
    ToolSpec(name="spflashtool", version_args=("--version",), label="SP Flash Tool"),
    ToolSpec(name="flash_tool", version_args=("--version",), label="SP Flash Tool"),
)


def check_mediatek_tools() -> list[ToolCheckResult]:
    """Return validation results for MediaTek tooling."""
    return check_tool_specs((MTKCLIENT_SPEC, *SP_FLASH_SPECS))


def resolve_mediatek_recovery_tool() -> tuple[str | None, dict]:
    """Pick a MediaTek recovery tool with structured error info."""
    results = check_mediatek_tools()
    selected = first_available(results)
    if selected:
        return selected.name, {"results": results}

    fallback_name, fallback_results = resolve_android_fallback()
    error = {
        "code": "tool_missing",
        "message": "No MediaTek recovery tools found (mtkclient/SP Flash Tool).",
        "candidates": [MTKCLIENT_SPEC.name, *(spec.name for spec in SP_FLASH_SPECS)],
    }
    if fallback_name:
        error["fallback"] = fallback_name

    return None, {"error": error, "results": results, "fallback_results": fallback_results}


def build_sp_flash_script_command(script_path: Path) -> list[str] | None:
    """Build a SP Flash Tool command for script-based flashing when available."""
    results = check_tool_specs(SP_FLASH_SPECS)
    selected = first_available(results)
    if not selected:
        return None
    return [selected.name, "--script", str(script_path)]

"""
Qualcomm tool wrappers.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .android import resolve_android_fallback
from .base import ToolSpec, check_tool_specs, first_available
from ..utils import ToolCheckResult


QUALCOMM_SPECS = (
    ToolSpec(name="edl", version_args=("--version",), label="edl"),
    ToolSpec(name="qdl", version_args=("--version",), label="qdl"),
    ToolSpec(name="emmcdl", version_args=("--version",), label="emmcdl"),
)


def check_qualcomm_tools() -> list[ToolCheckResult]:
    """Return validation results for Qualcomm tooling."""
    return check_tool_specs(QUALCOMM_SPECS)


def resolve_qualcomm_recovery_tool() -> tuple[str | None, dict]:
    """Pick a Qualcomm recovery tool with structured error info."""
    results = check_qualcomm_tools()
    selected = first_available(results)
    if selected:
        return selected.name, {"results": results}

    fallback_name, fallback_results = resolve_android_fallback()
    error = {
        "code": "tool_missing",
        "message": "No Qualcomm recovery tools found (edl/qdl/emmcdl).",
        "candidates": [spec.name for spec in QUALCOMM_SPECS],
    }
    if fallback_name:
        error["fallback"] = fallback_name

    return None, {"error": error, "results": results, "fallback_results": fallback_results}

"""ADB/Fastboot tool wrappers."""

from __future__ import annotations

from .base import ToolSpec, check_tool_specs, first_available
from ..utils import ToolCheckResult


ADB_SPEC = ToolSpec(name="adb", version_args=("version",), label="ADB")
FASTBOOT_SPEC = ToolSpec(name="fastboot", version_args=("--version",), label="Fastboot")


def check_android_tools() -> list[ToolCheckResult]:
    """Return validation results for Android platform tools."""
    return check_tool_specs((ADB_SPEC, FASTBOOT_SPEC))


def resolve_android_fallback() -> tuple[str | None, list[ToolCheckResult]]:
    """Return the preferred available Android tool as a fallback."""
    results = check_android_tools()
    selected = first_available(results)
    return (selected.name if selected else None, results)

"""
Utility functions for Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from ..config import Config


class SafeSubprocess:
    """Safe subprocess execution"""

    @staticmethod
    def run(cmd: List[str], timeout: int = Config.TIMEOUT_SHORT) -> Tuple[int, str, str]:
        """Execute command safely"""
        try:
            resolved_cmd = resolve_tool_command(cmd)
            result = subprocess.run(
                resolved_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as exc:
            return -1, "", str(exc)


@dataclass(frozen=True)
class ToolCheckResult:
    """Result of validating an external tool."""

    name: str
    available: bool
    label: str | None = None
    path: str | None = None
    version: str | None = None
    error: dict[str, str] = field(default_factory=dict)


def _bundled_platform_tool_path(name: str) -> Path | None:
    if name not in {"adb", "fastboot"}:
        return None

    suffix = ".exe" if platform.system().lower() == "windows" else ""
    candidate = Config.ANDROID_PLATFORM_TOOLS_DIR / f"{name}{suffix}"
    if candidate.exists():
        return candidate
    return None


def resolve_tool_command(cmd: List[str]) -> List[str]:
    """Replace tool command with bundled tool path when available."""
    if not cmd:
        return cmd
    tool = cmd[0]
    if Path(tool).is_absolute():
        return cmd

    bundled_path = _bundled_platform_tool_path(tool)
    if bundled_path:
        return [str(bundled_path), *cmd[1:]]
    return cmd


def check_tool(
    name: str,
    version_args: Sequence[str] | None = None,
    *,
    label: str | None = None,
) -> ToolCheckResult:
    """Validate a tool is on PATH and optionally resolve its version."""
    path = shutil.which(name)
    bundled_path = _bundled_platform_tool_path(name)
    if bundled_path:
        path = str(bundled_path)
    if not path:
        return ToolCheckResult(
            name=name,
            label=label,
            available=False,
            error={
                "code": "tool_missing",
                "message": f"{name} not found in PATH.",
            },
        )

    version = None
    error: dict[str, str] = {}
    if version_args:
        code, stdout, stderr = SafeSubprocess.run([path or name, *version_args])
        output = (stdout or stderr).strip()
        if code == 0 and output:
            version = output.splitlines()[0].strip()
        elif code != 0:
            error = {
                "code": "version_check_failed",
                "message": output or f"Unable to determine {name} version.",
            }

    return ToolCheckResult(
        name=name,
        label=label,
        available=True,
        path=path,
        version=version,
        error=error,
    )


def check_tools(tools: Iterable[tuple[str, Sequence[str] | None]]) -> List[ToolCheckResult]:
    """Validate a list of tools from (name, version_args) tuples."""
    return [check_tool(name, version_args) for name, version_args in tools]

from __future__ import annotations

from dataclasses import dataclass, field
import shutil
import subprocess
from typing import Iterable, List, Sequence, Tuple

from ..config import Config


class SafeSubprocess:
    """Safe subprocess execution"""

    @staticmethod
    def run(cmd: List[str], timeout: int = Config.TIMEOUT_SHORT) -> Tuple[int, str, str]:
        """Execute command safely"""
        try:
            result = subprocess.run(
                cmd,
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
    path: str | None = None
    version: str | None = None
    error: dict[str, str] = field(default_factory=dict)


def check_tool(name: str, version_args: Sequence[str] | None = None) -> ToolCheckResult:
    """Validate a tool is on PATH and optionally resolve its version."""
    path = shutil.which(name)
    if not path:
        return ToolCheckResult(
            name=name,
            available=False,
            error={
                "code": "tool_missing",
                "message": f"{name} not found in PATH.",
            },
        )

    version = None
    error: dict[str, str] = {}
    if version_args:
        code, stdout, stderr = SafeSubprocess.run([name, *version_args])
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
        available=True,
        path=path,
        version=version,
        error=error,
    )


def check_tools(tools: Iterable[tuple[str, Sequence[str] | None]]) -> List[ToolCheckResult]:
    """Validate a list of tools from (name, version_args) tuples."""
    return [check_tool(name, version_args) for name, version_args in tools]

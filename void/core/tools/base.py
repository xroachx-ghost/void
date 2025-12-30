"""Shared helpers for external tool wrappers."""

"""
Base tool interface.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..utils import ToolCheckResult, check_tool


@dataclass(frozen=True)
class ToolSpec:
    """Specification for an external tool and its version arguments."""

    name: str
    version_args: tuple[str, ...] = ()
    label: str | None = None


def check_tool_spec(spec: ToolSpec) -> ToolCheckResult:
    """Validate a tool spec."""
    label = spec.label or spec.name
    return check_tool(spec.name, spec.version_args or None, label=label)


def check_tool_specs(specs: Iterable[ToolSpec]) -> list[ToolCheckResult]:
    """Validate multiple tool specs."""
    return [check_tool_spec(spec) for spec in specs]


def first_available(results: Sequence[ToolCheckResult]) -> ToolCheckResult | None:
    """Return the first available tool result."""
    for result in results:
        if result.available:
            return result
    return None

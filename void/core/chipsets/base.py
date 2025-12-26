"""Base chipset protocol definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ChipsetDetection:
    """Structured detection results from a chipset module."""

    chipset: str
    vendor: str
    mode: str
    confidence: float = 0.0
    notes: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ChipsetActionResult:
    """Result of an action performed against a chipset workflow."""

    success: bool
    message: str
    data: dict[str, str] = field(default_factory=dict)


class BaseChipsetProtocol(Protocol):
    """Protocol for chipset implementations."""

    name: str
    vendor: str
    supported_modes: tuple[str, ...]

    def detect(self, context: dict[str, str]) -> ChipsetDetection | None:
        """Return detection info for the provided context."""

    def enter_mode(self, context: dict[str, str], target_mode: str) -> ChipsetActionResult:
        """Attempt to place the device into a target mode."""

    def recover(self, context: dict[str, str]) -> ChipsetActionResult:
        """Attempt a recovery workflow for the chipset."""

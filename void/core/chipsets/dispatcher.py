"""Dispatcher for chipset detection and workflows."""

from __future__ import annotations

from typing import Iterable

from .base import BaseChipsetProtocol, ChipsetActionResult, ChipsetDetection
from .generic import GenericChipset
from .mediatek import MediaTekChipset
from .qualcomm import QualcommChipset
from .samsung import SamsungExynosChipset


_CHIPSET_IMPLEMENTATIONS: tuple[BaseChipsetProtocol, ...] = (
    QualcommChipset(),
    MediaTekChipset(),
    SamsungExynosChipset(),
    GenericChipset(),
)


def resolve_chipset(context: dict[str, str], override: str | None = None) -> BaseChipsetProtocol:
    """Resolve a chipset implementation for the given context."""
    if override:
        for chipset in _CHIPSET_IMPLEMENTATIONS:
            if chipset.name.lower() == override.lower():
                return chipset
        return GenericChipset()

    detection = detect_chipset_for_device(context)
    if detection:
        for chipset in _CHIPSET_IMPLEMENTATIONS:
            if chipset.name == detection.chipset:
                return chipset
    return GenericChipset()


def detect_chipset_for_device(context: dict[str, str]) -> ChipsetDetection | None:
    """Run chipset detection across known implementations."""
    best: ChipsetDetection | None = None
    for chipset in _CHIPSET_IMPLEMENTATIONS:
        detection = chipset.detect(context)
        if not detection:
            continue
        if not best or detection.confidence > best.confidence:
            best = detection
    return best


def enter_chipset_mode(
    context: dict[str, str],
    target_mode: str,
    override: str | None = None,
) -> ChipsetActionResult:
    """Dispatch an enter-mode request to the resolved chipset."""
    chipset = resolve_chipset(context, override=override)
    return chipset.enter_mode(context, target_mode)


def recover_chipset_device(
    context: dict[str, str],
    override: str | None = None,
) -> ChipsetActionResult:
    """Dispatch a recovery request to the resolved chipset."""
    chipset = resolve_chipset(context, override=override)
    return chipset.recover(context)


def list_chipsets() -> Iterable[BaseChipsetProtocol]:
    """Return registered chipset implementations."""
    return _CHIPSET_IMPLEMENTATIONS

"""Utilities for chipset detection."""

"""
Chipset utilities.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from typing import Iterable


def normalize_text(value: str | None) -> str:
    """Normalize text for matching."""
    return (value or "").strip().lower()


def match_any(value: str | None, tokens: Iterable[str]) -> bool:
    """Return True when value contains any token."""
    haystack = normalize_text(value)
    return any(token in haystack for token in tokens)


def extract_usb_ids(context: dict[str, str]) -> tuple[str, str] | None:
    """Extract USB VID/PID from context."""
    vid = normalize_text(context.get("usb_vid") or context.get("vid"))
    pid = normalize_text(context.get("usb_pid") or context.get("pid"))
    if vid and pid:
        return vid, pid

    combined = normalize_text(context.get("usb_id") or context.get("usb"))
    if combined and ":" in combined:
        parts = combined.split(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
    return None

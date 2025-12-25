"""Void package."""

from __future__ import annotations

from .config import Config

__all__ = ["Config", "main"]


def __getattr__(name: str):
    if name == "main":
        from .main import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

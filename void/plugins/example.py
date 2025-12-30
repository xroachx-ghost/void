"""
Example plugin shipped with Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import platform
from typing import Sequence

from .base import PluginContext, PluginFeature, PluginMetadata, PluginResult
from .registry import register_plugin


@register_plugin
class SystemInfoPlugin(PluginFeature):
    """Sample plugin that reports host system information."""

    metadata = PluginMetadata(
        id="system-info",
        name="System Info",
        description="Report host OS and Python runtime details.",
        version="1.0.0",
        author="Void",
        tags=("system", "example"),
    )

    def run(self, context: PluginContext, args: Sequence[str]) -> PluginResult:
        details = {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        }
        message = (
            "System Info\n"
            f"OS: {details['platform']}\n"
            f"Python: {details['python']}\n"
            f"Machine: {details['machine']}"
        )
        if context.emit:
            context.emit(message)
        return PluginResult(success=True, message="System info collected.", data=details)

"""
Plugin package for Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from .base import PluginContext, PluginFeature, PluginMetadata, PluginResult
from .registry import discover_plugins, get_registry, register_plugin

__all__ = [
    "PluginContext",
    "PluginFeature",
    "PluginMetadata",
    "PluginResult",
    "discover_plugins",
    "get_registry",
    "register_plugin",
]

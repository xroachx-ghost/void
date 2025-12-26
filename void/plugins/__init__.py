"""Plugin package for Void."""

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

"""
Plugin registry and discovery helpers.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, List, Sequence

from .base import PluginContext, PluginFeature, PluginMetadata, PluginResult


class PluginRegistry:
    """Registry for plugin feature discovery and execution."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginFeature] = {}

    def register(self, plugin: PluginFeature) -> None:
        """Register a plugin by its metadata id."""
        plugin_id = plugin.metadata.id
        if plugin_id in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin_id}")
        self._plugins[plugin_id] = plugin

    def list_metadata(self) -> List[PluginMetadata]:
        """List plugin metadata sorted by name."""
        return sorted(
            (plugin.metadata for plugin in self._plugins.values()),
            key=lambda meta: meta.name.lower(),
        )

    def get(self, plugin_id: str) -> PluginFeature | None:
        """Get a plugin by id."""
        return self._plugins.get(plugin_id)

    def run(self, plugin_id: str, context: PluginContext, args: Sequence[str]) -> PluginResult:
        """Execute a plugin by id."""
        plugin = self.get(plugin_id)
        if not plugin:
            raise KeyError(f"Unknown plugin: {plugin_id}")
        return plugin.run(context, args)


_REGISTRY = PluginRegistry()
_DISCOVERED = False


def register_plugin(cls):
    """Class decorator for registering plugins with a no-arg constructor."""
    instance = cls()
    _REGISTRY.register(instance)
    return cls


def get_registry() -> PluginRegistry:
    """Return the global plugin registry."""
    return _REGISTRY


def discover_plugins() -> None:
    """Discover plugins within the void.plugins package."""
    global _DISCOVERED
    if _DISCOVERED:
        return

    package = importlib.import_module("void.plugins")
    for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        if module_info.name.endswith(".base") or module_info.name.endswith(".registry"):
            continue
        importlib.import_module(module_info.name)

    _DISCOVERED = True

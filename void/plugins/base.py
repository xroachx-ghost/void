"""
VOID Plugin Interface.

Defines the stable contract for plugins and metadata.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence


@dataclass(frozen=True)
class PluginMetadata:
    """Metadata describing a plugin feature."""

    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Void"
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata for structured outputs."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": list(self.tags),
        }


@dataclass
class PluginResult:
    """Result returned from a plugin run."""

    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginContext:
    """Execution context for plugins."""

    mode: str
    emit: Callable[[str], None] | None = None


class PluginFeature(ABC):
    """Base class for all plugins."""

    metadata: PluginMetadata

    @abstractmethod
    def run(self, context: PluginContext, args: Sequence[str]) -> PluginResult:
        """Run the plugin feature."""
        raise NotImplementedError

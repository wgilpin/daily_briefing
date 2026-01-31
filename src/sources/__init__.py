"""Feed source implementations and registry.

This module provides the source registry pattern for managing feed sources.
New sources can be registered using the source_registry.

Example usage:
    from src.sources import source_registry, FeedSource

    # Register a source class
    @source_registry.register
    class MySource(FeedSource):
        @property
        def source_type(self) -> str:
            return "my_source"

        def fetch_items(self) -> list[FeedItem]:
            return [...]

    # Or register manually
    source_registry.register(MySource)

    # Get all registered source classes
    for source_type, source_class in source_registry.get_all().items():
        print(f"{source_type}: {source_class.__name__}")

    # Get a specific source class
    zotero_class = source_registry.get("zotero")
"""

from typing import Any

from src.sources.base import BaseFeedSource, FeedSource


class SourceRegistry:
    """Registry for feed source implementations.

    Provides a central location for registering and discovering
    feed sources. Sources can be registered by class or by instance.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._sources: dict[str, type] = {}

    def register(self, source_class: type) -> type:
        """Register a feed source class.

        Can be used as a decorator or called directly.

        Args:
            source_class: A class that implements FeedSource protocol

        Returns:
            The source class (for decorator usage)

        Raises:
            ValueError: If source_type is already registered

        Example:
            @source_registry.register
            class MySource:
                ...

            # Or:
            source_registry.register(MySource)
        """
        # Create a temporary instance to get source_type
        # For classes with required __init__ args, use a class attribute
        if hasattr(source_class, "_source_type"):
            source_type = source_class._source_type
        else:
            # Try to get from class method if available
            try:
                source_type = source_class.source_type.fget(None)  # type: ignore
            except (TypeError, AttributeError):
                # Use class name as fallback
                source_type = source_class.__name__.lower().replace("source", "")

        if source_type in self._sources:
            raise ValueError(f"Source type '{source_type}' is already registered")

        self._sources[source_type] = source_class
        return source_class

    def register_with_type(self, source_type: str, source_class: type) -> None:
        """Register a source class with an explicit type name.

        Args:
            source_type: The source type identifier
            source_class: A class that implements FeedSource protocol

        Raises:
            ValueError: If source_type is already registered
        """
        if source_type in self._sources:
            raise ValueError(f"Source type '{source_type}' is already registered")
        self._sources[source_type] = source_class

    def get(self, source_type: str) -> type | None:
        """Get a registered source class by type.

        Args:
            source_type: The source type identifier

        Returns:
            The source class or None if not found
        """
        return self._sources.get(source_type)

    def get_all(self) -> dict[str, type]:
        """Get all registered source classes.

        Returns:
            Dict mapping source_type to source class
        """
        return self._sources.copy()

    def get_source_types(self) -> list[str]:
        """Get list of all registered source types.

        Returns:
            List of source type identifiers
        """
        return list(self._sources.keys())

    def get_config_schemas(self) -> dict[str, dict[str, Any]]:
        """Get configuration schemas for all registered sources.

        Returns:
            Dict mapping source_type to config schema
        """
        schemas = {}
        for source_type, source_class in self._sources.items():
            if hasattr(source_class, "get_config_schema"):
                try:
                    schemas[source_type] = source_class.get_config_schema()
                except Exception:
                    schemas[source_type] = {}
            else:
                schemas[source_type] = {}
        return schemas


# Global source registry instance
source_registry = SourceRegistry()


# Import sources after registry is created to avoid circular imports
from src.sources.newsletter import NewsletterSource
from src.sources.zotero import ZoteroSource

# Register built-in sources
source_registry.register_with_type("zotero", ZoteroSource)
source_registry.register_with_type("newsletter", NewsletterSource)

__all__ = [
    "FeedSource",
    "BaseFeedSource",
    "ZoteroSource",
    "NewsletterSource",
    "source_registry",
    "SourceRegistry",
]

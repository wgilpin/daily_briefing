"""FeedSource protocol and base classes.

Defines the interface that all feed sources must implement. To add a new
source to the unified feed:

1. Create a new module in src/sources/ (e.g., my_source.py)
2. Implement the FeedSource protocol
3. Register your source with FeedService.register_source()

Example:
    from src.sources.base import FeedSource
    from src.models.feed_item import FeedItem

    class MySource(FeedSource):
        @property
        def source_type(self) -> str:
            return "my_source"

        def fetch_items(self) -> list[FeedItem]:
            # Fetch items from your data source
            return [...]

        @classmethod
        def get_config_schema(cls) -> dict:
            return {
                "api_key": {"type": "string", "required": True},
                "max_items": {"type": "integer", "default": 50},
            }
"""

from typing import Any, Protocol, runtime_checkable

from src.models.feed_item import FeedItem


@runtime_checkable
class FeedSource(Protocol):
    """Protocol for feed source implementations.

    All feed sources (Zotero, Newsletter, future sources) must implement
    this interface to integrate with the unified feed system.

    Attributes:
        source_type: Unique identifier for this source type (e.g., "zotero").
            Must be unique across all registered sources.

    Methods:
        fetch_items: Retrieve items from the source and return as FeedItems.
        get_config_schema: Return configuration schema for the source (optional).
    """

    @property
    def source_type(self) -> str:
        """Return the unique identifier for this source type.

        Returns:
            str: Unique source type identifier (e.g., "zotero", "newsletter").
                Should be lowercase, alphanumeric, and use underscores for
                multi-word names.
        """
        ...

    def fetch_items(self) -> list[FeedItem]:
        """Fetch items from the source.

        Implementations should:
        - Handle rate limiting and retries internally
        - Return empty list (not raise) if no items available
        - Log errors but raise only for unrecoverable failures
        - Set appropriate source_type and source_id on each FeedItem

        Returns:
            list[FeedItem]: List of FeedItem objects from this source.
                Items should have unique source_id values within this source.

        Raises:
            Exception: Only for unrecoverable errors (e.g., invalid credentials).
                Transient errors should be handled internally with retries.
        """
        ...

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Return the configuration schema for this source.

        This method enables dynamic configuration UI generation for
        sources that support web-based configuration.

        Returns:
            dict: Configuration schema with field definitions:
                {
                    "field_name": {
                        "type": "string" | "integer" | "boolean" | "list",
                        "required": True | False,
                        "default": <default_value>,
                        "description": "Field description",
                        "secret": True,  # For sensitive values like API keys
                    },
                    ...
                }
                Return empty dict if no configuration is needed.

        Example:
            @classmethod
            def get_config_schema(cls) -> dict:
                return {
                    "api_key": {
                        "type": "string",
                        "required": True,
                        "secret": True,
                        "description": "API key for authentication",
                    },
                    "days_lookback": {
                        "type": "integer",
                        "required": False,
                        "default": 7,
                        "description": "Number of days to fetch",
                    },
                }
        """
        ...


class BaseFeedSource:
    """Optional base class for feed sources.

    Provides default implementations for optional protocol methods.
    Sources can extend this class instead of implementing the protocol
    directly for convenience.
    """

    @property
    def source_type(self) -> str:
        """Return the source type. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement source_type property")

    def fetch_items(self) -> list[FeedItem]:
        """Fetch items from the source. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement fetch_items method")

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Return empty config schema by default.

        Override in subclasses to provide configuration options.
        """
        return {}

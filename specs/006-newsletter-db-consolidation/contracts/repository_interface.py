"""Repository interface for newsletter email tracking.

This module defines the contract for database operations related
to newsletter email processing and tracking.

All methods use Pydantic models for type safety (constitution requirement).
"""

from datetime import datetime
from typing import List, Optional, Protocol

from pydantic import BaseModel, Field


# Pydantic Models
class ProcessedEmail(BaseModel):
    """Email tracking record."""

    message_id: str
    sender_email: str
    subject: Optional[str] = None
    collected_at: datetime
    processed_at: Optional[datetime] = None
    status: str  # 'collected', 'converted', 'parsed', 'failed'
    error_message: Optional[str] = None


class EmailTrackingQuery(BaseModel):
    """Query parameters for email tracking lookups."""

    sender_emails: Optional[List[str]] = Field(
        default=None,
        description="Filter by sender emails"
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum results"
    )


class EmailStatusUpdate(BaseModel):
    """Parameters for updating email status."""

    message_id: str
    status: str
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Repository Protocol
class NewsletterRepository(Protocol):
    """Protocol defining repository interface for newsletter operations.

    This is a Protocol (not ABC) to allow both mock and real implementations
    without inheritance coupling.
    """

    def is_email_processed(self, message_id: str) -> bool:
        """Check if email has been processed.

        Args:
            message_id: Gmail message ID

        Returns:
            True if email exists in processed_emails table
        """
        ...

    def get_processed_message_ids(
        self,
        sender_emails: Optional[List[str]] = None
    ) -> set[str]:
        """Get set of processed message IDs.

        Args:
            sender_emails: Optional filter by sender emails

        Returns:
            Set of message IDs that have been processed
        """
        ...

    def track_email_processed(
        self,
        message_id: str,
        sender_email: str,
        status: str,
        subject: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Record email as processed.

        Args:
            message_id: Gmail message ID
            sender_email: Newsletter sender email
            status: Processing status
            subject: Email subject (optional)
            error_message: Error details if status='failed'

        Raises:
            ValueError: If status not in valid set
        """
        ...

    def update_email_status(
        self,
        message_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update status of existing processed email.

        Args:
            message_id: Gmail message ID
            status: New processing status
            error_message: Error details if status='failed'

        Raises:
            ValueError: If message_id not found
            ValueError: If status not in valid set
        """
        ...

    def get_processed_email(self, message_id: str) -> Optional[ProcessedEmail]:
        """Retrieve processed email record.

        Args:
            message_id: Gmail message ID

        Returns:
            ProcessedEmail model or None if not found
        """
        ...

    def query_processed_emails(
        self,
        query: EmailTrackingQuery
    ) -> List[ProcessedEmail]:
        """Query processed emails with filters.

        Args:
            query: Query parameters model

        Returns:
            List of ProcessedEmail models matching criteria
        """
        ...


# Connection Pool Protocol
class ConnectionPool(Protocol):
    """Protocol for connection pool operations."""

    def getconn(self):
        """Get connection from pool.

        Returns:
            PostgreSQL connection object

        Raises:
            PoolError: If pool exhausted
        """
        ...

    def putconn(self, conn) -> None:
        """Return connection to pool.

        Args:
            conn: PostgreSQL connection to return
        """
        ...

    def closeall(self) -> None:
        """Close all connections in pool.

        WARNING: Only call on application shutdown.
        """
        ...

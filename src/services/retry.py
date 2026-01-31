"""Retry utility with exponential backoff.

Provides decorator for retrying functions with configurable backoff.
Uses tenacity library for robust retry handling.
"""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    exponential: bool = True,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        wait_seconds: Base wait time between retries (in seconds)
        exponential: Whether to use exponential backoff
        retry_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_attempts=3, wait_seconds=1.0)
        def fetch_data():
            return api.get_data()
    """

    def decorator(func: F) -> F:
        if exponential:
            wait_strategy = wait_exponential(
                multiplier=wait_seconds,
                min=wait_seconds,
                max=wait_seconds * 10,
            )
        else:
            wait_strategy = wait_fixed(wait_seconds)

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_strategy,
            retry=retry_if_exception_type(retry_exceptions),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Retry attempt for {func.__name__}: {type(e).__name__}: {e}"
                )
                raise

        return wrapper  # type: ignore

    return decorator


def retry_on_rate_limit(
    max_attempts: int = 5,
    base_wait: float = 2.0,
) -> Callable[[F], F]:
    """Decorator specifically for rate-limited APIs.

    Uses exponential backoff optimized for rate limiting scenarios.
    Handles 429 errors and RESOURCE_EXHAUSTED responses.

    Args:
        max_attempts: Maximum number of retry attempts
        base_wait: Base wait time in seconds

    Returns:
        Decorated function with rate-limit-aware retry logic
    """
    return with_retry(
        max_attempts=max_attempts,
        wait_seconds=base_wait,
        exponential=True,
        retry_exceptions=(Exception,),  # Catch all for now, can be refined
    )

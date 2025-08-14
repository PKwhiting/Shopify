"""
Retry mechanism for Shopify API requests

Handles automatic retries for transient errors and rate limiting.
"""

import time
import random
from typing import Any, Callable, Optional, Type
import requests

from .error_handler import ShopifyAPIError, ShopifyRateLimitError
from ..config import ShopifyConfig


class RetryHandler:
    """Handles retry logic for API requests."""

    def __init__(self, config: ShopifyConfig):
        """
        Initialize retry handler.

        Args:
            config: ShopifyConfig instance with retry settings
        """
        self.config = config

    def execute_with_retry(self, func: Callable[[], Any], *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: Final exception after all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):  # +1 for initial attempt
            try:
                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                # Check if error is retryable
                if not self._is_retryable_error(e):
                    raise e

                # Don't retry on last attempt
                if attempt >= self.config.max_retries:
                    break

                # Calculate delay with better error handling
                try:
                    delay = self._calculate_delay(e, attempt)

                    # Wait before retrying
                    if delay > 0:
                        time.sleep(delay)
                except Exception as delay_error:
                    # If delay calculation fails, use a minimal delay and continue
                    time.sleep(1.0)

        # All retries exhausted, raise the last exception
        if last_exception:
            raise last_exception

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable.

        Args:
            error: Exception to check

        Returns:
            bool: True if error is retryable
        """
        # Rate limit errors are retryable
        if isinstance(error, ShopifyRateLimitError):
            return True

        # Server errors (5xx) are retryable
        if isinstance(error, ShopifyAPIError):
            if error.status_code and 500 <= error.status_code < 600:
                return True

        # Network errors are retryable
        if isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return True

        return False

    def _calculate_delay(self, error: Exception, attempt: int) -> float:
        """
        Calculate delay before next retry.

        Args:
            error: The error that occurred
            attempt: Current attempt number (0-based)

        Returns:
            float: Delay in seconds
        """
        try:
            # For rate limit errors, use the retry-after header if available
            if isinstance(error, ShopifyRateLimitError) and error.retry_after:
                return max(0.0, float(error.retry_after))

            # For other errors, use exponential backoff with jitter
            base_delay = max(1, self.config.retry_delay)  # Ensure minimum delay
            exponential_delay = base_delay * (
                2 ** min(attempt, MAX_BACKOFF_EXPONENT)
            )  # Cap exponential growth

            # Add jitter to avoid thundering herd (0-50% of delay)
            jitter = random.uniform(0, 0.5) * exponential_delay

            # Cap the maximum delay at 60 seconds
            total_delay = min(exponential_delay + jitter, 60.0)
            return max(0.1, total_delay)  # Minimum 100ms delay

        except Exception:
            # Fallback to a safe default if calculation fails
            return 1.0

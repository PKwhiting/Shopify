"""
Error handling utilities for Shopify API

Handles various types of errors that can occur when interacting with Shopify's GraphQL API.
"""

import json
from typing import List, Dict, Any, Optional
import requests


class ShopifyAPIError(Exception):
    """Base exception for Shopify API errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        response: Optional[requests.Response] = None,
    ):
        """
        Initialize Shopify API error.

        Args:
            message (str): Error message
            error_code (str, optional): Specific error code
            response (requests.Response, optional): HTTP response object
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.response = response
        self.status_code = response.status_code if response else None


class ShopifyGraphQLError(ShopifyAPIError):
    """Exception for GraphQL-specific errors."""

    def __init__(self, errors: List[Dict[str, Any]]):
        """
        Initialize GraphQL error.

        Args:
            errors (list): List of GraphQL error objects
        """
        self.graphql_errors = errors
        messages = [error.get("message") or "Unknown GraphQL error" for error in errors]
        super().__init__("; ".join(messages))


class ShopifyRateLimitError(ShopifyAPIError):
    """Exception for rate limiting errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        """
        Initialize rate limit error.

        Args:
            message (str): Error message
            retry_after (int, optional): Seconds to wait before retrying
        """
        super().__init__(message)
        self.retry_after = retry_after


class ShopifyAuthError(ShopifyAPIError):
    """Exception for authentication errors."""

    pass


class ErrorHandler:
    """Handles various types of errors from Shopify API."""

    def __init__(self):
        """Initialize error handler."""
        pass

    def handle_graphql_errors(self, errors: List[Dict[str, Any]]) -> None:
        """
        Handle GraphQL errors from API response.

        Args:
            errors (list): List of GraphQL error objects

        Raises:
            ShopifyGraphQLError: For GraphQL-specific errors
            ShopifyAuthError: For authentication errors
            ShopifyRateLimitError: For rate limiting errors
        """
        if not errors:
            return

        # Check for specific error types
        for error in errors:
            message = error.get("message", "") or ""  # Handle None messages
            extensions = error.get("extensions", {})
            code = extensions.get("code", "")

            # Authentication errors
            if "unauthorized" in message.lower() or code == "UNAUTHORIZED":
                raise ShopifyAuthError(f"Authentication failed: {message}")

            # Rate limiting errors
            if "throttled" in message.lower() or code == "THROTTLED":
                retry_after = extensions.get("retryAfter")
                raise ShopifyRateLimitError(f"Rate limit exceeded: {message}", retry_after)

        # Generic GraphQL error
        raise ShopifyGraphQLError(errors)

    def handle_request_error(self, error: requests.RequestException) -> None:
        """
        Handle HTTP request errors.

        Args:
            error (requests.RequestException): Request error

        Raises:
            ShopifyAPIError: For various HTTP errors
            ShopifyAuthError: For authentication errors
            ShopifyRateLimitError: For rate limiting errors
        """
        if isinstance(error, requests.exceptions.HTTPError):
            response = error.response
            status_code = response.status_code

            # Try to parse error details from response
            try:
                error_data = response.json()
            except (json.JSONDecodeError, AttributeError):
                error_data = {}

            # Handle specific HTTP status codes
            if status_code == 401:
                raise ShopifyAuthError("Invalid API credentials", response=response)
            elif status_code == 403:
                raise ShopifyAuthError(
                    "Access forbidden - check API permissions", response=response
                )
            elif status_code == 429:
                retry_after = response.headers.get("Retry-After")
                retry_after = int(retry_after) if retry_after else None
                raise ShopifyRateLimitError("Rate limit exceeded", retry_after=retry_after)
            elif status_code == 422:
                message = "Validation error"
                if "errors" in error_data:
                    error_messages = []
                    errors = error_data["errors"]
                    if isinstance(errors, dict):
                        for field, msgs in errors.items():
                            if isinstance(msgs, list):
                                error_messages.extend([f"{field}: {msg}" for msg in msgs])
                            else:
                                error_messages.append(f"{field}: {msgs}")
                    elif isinstance(errors, list):
                        error_messages.extend(errors)
                    if error_messages:
                        message = "; ".join(error_messages)
                raise ShopifyAPIError(message, error_code="VALIDATION_ERROR", response=response)
            else:
                message = f"HTTP {status_code} error"
                if "message" in error_data:
                    message = error_data["message"]
                raise ShopifyAPIError(message, response=response)

        elif isinstance(error, requests.exceptions.Timeout):
            raise ShopifyAPIError("Request timeout - API response took too long")
        elif isinstance(error, requests.exceptions.ConnectionError):
            raise ShopifyAPIError("Connection error - unable to reach Shopify API")
        else:
            raise ShopifyAPIError(f"Request error: {str(error)}")

    def is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable.

        Args:
            error (Exception): The error to check

        Returns:
            bool: True if the error is retryable
        """
        if isinstance(error, ShopifyRateLimitError):
            return True
        elif isinstance(error, ShopifyAPIError):
            # Retry on 5xx server errors
            if error.status_code and 500 <= error.status_code < 600:
                return True
        elif isinstance(error, requests.exceptions.Timeout):
            return True
        elif isinstance(error, requests.exceptions.ConnectionError):
            return True

        return False

    def get_retry_delay(self, error: Exception) -> int:
        """
        Get suggested retry delay for an error.

        Args:
            error (Exception): The error to get delay for

        Returns:
            int: Delay in seconds
        """
        if isinstance(error, ShopifyRateLimitError) and error.retry_after:
            return error.retry_after

        # Default exponential backoff
        return 1

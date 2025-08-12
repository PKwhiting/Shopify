"""
Retry mechanism for Shopify API requests

Handles automatic retries for transient errors and rate limiting.
"""

import time
import random
from typing import Any, Callable, Optional, Type
from .error_handler import ShopifyAPIError

class ShopifyRateLimitError(Exception):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after
from ..config import ShopifyConfig
import requests


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
                
                # Calculate delay
                delay = self._calculate_delay(e, attempt)
                
                # Wait before retrying
                time.sleep(delay)
        
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
        # For rate limit errors, use the retry-after header if available
        if isinstance(error, ShopifyRateLimitError) and error.retry_after:
            return float(error.retry_after)
        
        # For other errors, use exponential backoff with jitter
        base_delay = self.config.retry_delay
        exponential_delay = base_delay * (2 ** attempt)
        
        # Add jitter to avoid thundering herd
        jitter = random.uniform(0, 0.5) * exponential_delay
        
        # Cap the maximum delay at 60 seconds
        return min(exponential_delay + jitter, 60.0)
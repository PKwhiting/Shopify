"""
Tests for Retry Mechanism

Comprehensive tests for the RetryHandler class including edge cases,
error conditions, and performance scenarios.
"""

import unittest
from unittest.mock import Mock, patch, call
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.utils.retry import RetryHandler, ShopifyRateLimitError
from shopify.utils.error_handler import ShopifyAPIError
from shopify.config import ShopifyConfig
import requests


class TestRetryHandler(unittest.TestCase):
    """Test cases for RetryHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ShopifyConfig(max_retries=3, retry_delay=1)
        self.retry_handler = RetryHandler(self.config)
    
    def test_retry_handler_initialization(self):
        """Test retry handler initialization."""
        self.assertEqual(self.retry_handler.config, self.config)
    
    def test_successful_execution_no_retry(self):
        """Test successful execution without retry."""
        mock_func = Mock(return_value="success")
        
        result = self.retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(result, "success")
        mock_func.assert_called_once()
    
    def test_successful_execution_with_args(self):
        """Test successful execution with function arguments."""
        mock_func = Mock(return_value="success")
        
        result = self.retry_handler.execute_with_retry(mock_func, "arg1", "arg2", kwarg1="value1")
        
        self.assertEqual(result, "success")
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value1")
    
    @patch('time.sleep')
    def test_retry_on_rate_limit_error(self, mock_sleep):
        """Test retry behavior on rate limit error."""
        mock_func = Mock()
        mock_func.side_effect = [
            ShopifyRateLimitError("Rate limited", retry_after=2.0),
            ShopifyRateLimitError("Rate limited", retry_after=2.0),
            "success"
        ]
        
        result = self.retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_has_calls([call(2.0), call(2.0)])
    
    @patch('time.sleep')
    def test_retry_on_server_error(self, mock_sleep):
        """Test retry behavior on server errors."""
        mock_func = Mock()
        # Create a mock response with 500 status
        mock_response = Mock()
        mock_response.status_code = 500
        server_error = ShopifyAPIError("Server error", response=mock_response)
        mock_func.side_effect = [
            server_error,
            server_error,
            "success"
        ]
        
        result = self.retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('time.sleep')
    def test_retry_on_network_error(self, mock_sleep):
        """Test retry behavior on network errors."""
        mock_func = Mock()
        network_error = requests.exceptions.Timeout("Request timeout")
        mock_func.side_effect = [
            network_error,
            "success"
        ]
        
        result = self.retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once()
    
    @patch('time.sleep')
    def test_max_retries_exceeded(self, mock_sleep):
        """Test behavior when max retries exceeded."""
        mock_func = Mock()
        rate_limit_error = ShopifyRateLimitError("Rate limited", retry_after=1.0)
        mock_func.side_effect = rate_limit_error
        
        with self.assertRaises(ShopifyRateLimitError):
            self.retry_handler.execute_with_retry(mock_func)
        
        # Should attempt initial call + max_retries
        self.assertEqual(mock_func.call_count, self.config.max_retries + 1)
        self.assertEqual(mock_sleep.call_count, self.config.max_retries)
    
    def test_non_retryable_error_immediate_failure(self):
        """Test immediate failure on non-retryable errors."""
        mock_func = Mock()
        # Create a mock response with 400 status
        mock_response = Mock()
        mock_response.status_code = 400
        client_error = ShopifyAPIError("Bad request", response=mock_response)
        mock_func.side_effect = client_error
        
        with self.assertRaises(ShopifyAPIError):
            self.retry_handler.execute_with_retry(mock_func)
        
        # Should only attempt once for non-retryable errors
        mock_func.assert_called_once()
    
    def test_is_retryable_error_rate_limit(self):
        """Test retry detection for rate limit errors."""
        error = ShopifyRateLimitError("Rate limited")
        self.assertTrue(self.retry_handler._is_retryable_error(error))
    
    def test_is_retryable_error_server_errors(self):
        """Test retry detection for server errors."""
        for status_code in [500, 502, 503, 504]:
            mock_response = Mock()
            mock_response.status_code = status_code
            error = ShopifyAPIError("Server error", response=mock_response)
            self.assertTrue(self.retry_handler._is_retryable_error(error))
    
    def test_is_retryable_error_client_errors(self):
        """Test retry detection for client errors (should not retry)."""
        for status_code in [400, 401, 403, 404]:
            mock_response = Mock()
            mock_response.status_code = status_code
            error = ShopifyAPIError("Client error", response=mock_response)
            self.assertFalse(self.retry_handler._is_retryable_error(error))
    
    def test_is_retryable_error_network_errors(self):
        """Test retry detection for network errors."""
        timeout_error = requests.exceptions.Timeout("Timeout")
        connection_error = requests.exceptions.ConnectionError("Connection failed")
        
        self.assertTrue(self.retry_handler._is_retryable_error(timeout_error))
        self.assertTrue(self.retry_handler._is_retryable_error(connection_error))
    
    def test_is_retryable_error_generic_exception(self):
        """Test retry detection for generic exceptions (should not retry)."""
        generic_error = ValueError("Generic error")
        self.assertFalse(self.retry_handler._is_retryable_error(generic_error))
    
    def test_calculate_delay_with_retry_after(self):
        """Test delay calculation when retry-after is provided."""
        error = ShopifyRateLimitError("Rate limited", retry_after=30.0)
        delay = self.retry_handler._calculate_delay(error, 0)
        
        self.assertEqual(delay, 30.0)
    
    @patch('random.uniform')
    def test_calculate_delay_exponential_backoff(self, mock_random):
        """Test exponential backoff delay calculation."""
        mock_random.return_value = 0.5
        mock_response = Mock()
        mock_response.status_code = 500
        error = ShopifyAPIError("Server error", response=mock_response)
        
        # Test different attempts
        for attempt in range(4):
            delay = self.retry_handler._calculate_delay(error, attempt)
            expected_base = self.config.retry_delay * (2 ** attempt)
            expected_jitter = 0.5 * expected_base  # Jitter is 0.5 * exponential_delay based on code
            expected_delay = min(expected_base + expected_jitter, 60.0)
            
            self.assertEqual(delay, expected_delay)
    
    def test_calculate_delay_max_cap(self):
        """Test delay calculation maximum cap."""
        # Large retry delay that would exceed 60 seconds
        large_config = ShopifyConfig(retry_delay=30, max_retries=5)
        large_retry_handler = RetryHandler(large_config)
        
        mock_response = Mock()
        mock_response.status_code = 500
        error = ShopifyAPIError("Server error", response=mock_response)
        delay = large_retry_handler._calculate_delay(error, 5)  # Large attempt number
        
        self.assertLessEqual(delay, 60.0)
    
    @patch('time.sleep')
    def test_retry_with_different_config(self, mock_sleep):
        """Test retry behavior with different configuration."""
        custom_config = ShopifyConfig(max_retries=1, retry_delay=1)  # Use valid integer delay
        custom_retry_handler = RetryHandler(custom_config)
        
        mock_func = Mock()
        error = ShopifyRateLimitError("Rate limited", retry_after=1.5)
        mock_func.side_effect = [error, "success"]
        
        result = custom_retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once_with(1.5)
    
    @patch('time.sleep')
    def test_retry_with_zero_max_retries(self, mock_sleep):
        """Test behavior when max_retries is 0."""
        no_retry_config = ShopifyConfig(max_retries=0)
        no_retry_handler = RetryHandler(no_retry_config)
        
        mock_func = Mock()
        error = ShopifyRateLimitError("Rate limited")
        mock_func.side_effect = error
        
        with self.assertRaises(ShopifyRateLimitError):
            no_retry_handler.execute_with_retry(mock_func)
        
        # Should only attempt once (no retries)
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()


class TestRetryHandlerIntegration(unittest.TestCase):
    """Integration tests for RetryHandler with real scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ShopifyConfig(max_retries=2, retry_delay=1)  # Use valid integer delay
        self.retry_handler = RetryHandler(self.config)
    
    def test_mixed_error_types_retry(self):
        """Test retry behavior with mixed error types."""
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise requests.exceptions.Timeout("Network timeout")
            elif call_count == 2:
                raise ShopifyRateLimitError("Rate limited", retry_after=0.1)
            else:
                return "success"
        
        result = self.retry_handler.execute_with_retry(failing_function)
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    @patch('time.sleep')
    def test_actual_timing_behavior(self, mock_sleep):
        """Test that actual delays are calculated correctly."""
        mock_func = Mock()
        mock_func.side_effect = [
            ShopifyRateLimitError("Rate limited", retry_after=2.5),
            requests.exceptions.Timeout("Timeout"),
            "success"
        ]
        
        result = self.retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(result, "success")
        # First retry should use retry_after, second should use exponential backoff
        self.assertEqual(mock_sleep.call_count, 2)
        first_call_delay = mock_sleep.call_args_list[0][0][0]
        self.assertEqual(first_call_delay, 2.5)


if __name__ == '__main__':
    unittest.main()
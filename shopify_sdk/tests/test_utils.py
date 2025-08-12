"""
Tests for Utils modules

Unit tests for pagination and error handling utilities.
"""

import unittest
from unittest.mock import Mock
import requests
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.utils.pagination import PaginationHelper
from shopify.utils.error_handler import ErrorHandler, ShopifyAPIError, ShopifyGraphQLError, ShopifyRateLimitError


class TestPaginationHelper(unittest.TestCase):
    """Test cases for PaginationHelper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pagination = PaginationHelper()
        self.sample_data = {
            "products": {
                "edges": [
                    {"node": {"id": "1"}, "cursor": "cursor1"},
                    {"node": {"id": "2"}, "cursor": "cursor2"}
                ],
                "pageInfo": {
                    "hasNextPage": True,
                    "hasPreviousPage": False,
                    "startCursor": "cursor1",
                    "endCursor": "cursor2"
                }
            }
        }
    
    def test_get_page_info(self):
        """Test extracting page info."""
        page_info = self.pagination.get_page_info(self.sample_data, "products")
        
        expected_page_info = {
            "hasNextPage": True,
            "hasPreviousPage": False,
            "startCursor": "cursor1",
            "endCursor": "cursor2"
        }
        
        self.assertEqual(page_info, expected_page_info)
    
    def test_has_next_page(self):
        """Test checking for next page."""
        result = self.pagination.has_next_page(self.sample_data, "products")
        self.assertTrue(result)
    
    def test_has_previous_page(self):
        """Test checking for previous page."""
        result = self.pagination.has_previous_page(self.sample_data, "products")
        self.assertFalse(result)
    
    def test_get_next_cursor(self):
        """Test getting next cursor."""
        cursor = self.pagination.get_next_cursor(self.sample_data, "products")
        self.assertEqual(cursor, "cursor2")
    
    def test_get_previous_cursor(self):
        """Test getting previous cursor."""
        cursor = self.pagination.get_previous_cursor(self.sample_data, "products")
        self.assertIsNone(cursor)  # hasPreviousPage is False
    
    def test_extract_nodes(self):
        """Test extracting nodes from edges."""
        nodes = self.pagination.extract_nodes(self.sample_data, "products")
        
        expected_nodes = [
            {"id": "1"},
            {"id": "2"}
        ]
        
        self.assertEqual(nodes, expected_nodes)
    
    def test_extract_nodes_empty(self):
        """Test extracting nodes from empty data."""
        empty_data = {"products": {"edges": []}}
        nodes = self.pagination.extract_nodes(empty_data, "products")
        self.assertEqual(nodes, [])


class TestErrorHandler(unittest.TestCase):
    """Test cases for ErrorHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
    
    def test_handle_graphql_errors_empty(self):
        """Test handling empty GraphQL errors."""
        # Should not raise any exception
        self.error_handler.handle_graphql_errors([])
    
    def test_handle_graphql_errors_unauthorized(self):
        """Test handling unauthorized GraphQL errors."""
        errors = [{"message": "Unauthorized access", "extensions": {"code": "UNAUTHORIZED"}}]
        
        with self.assertRaises(Exception):  # Should raise ShopifyAuthError
            self.error_handler.handle_graphql_errors(errors)
    
    def test_handle_graphql_errors_throttled(self):
        """Test handling throttled GraphQL errors."""
        errors = [{"message": "Request throttled", "extensions": {"code": "THROTTLED", "retryAfter": 60}}]
        
        with self.assertRaises(ShopifyRateLimitError) as context:
            self.error_handler.handle_graphql_errors(errors)
        
        self.assertEqual(context.exception.retry_after, 60)
    
    def test_handle_graphql_errors_generic(self):
        """Test handling generic GraphQL errors."""
        errors = [{"message": "Field error"}]
        
        with self.assertRaises(ShopifyGraphQLError) as context:
            self.error_handler.handle_graphql_errors(errors)
        
        self.assertEqual(context.exception.graphql_errors, errors)
    
    def test_handle_request_error_401(self):
        """Test handling 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {}
        
        http_error = requests.exceptions.HTTPError(response=mock_response)
        
        with self.assertRaises(Exception):  # Should raise ShopifyAuthError
            self.error_handler.handle_request_error(http_error)
    
    def test_handle_request_error_429(self):
        """Test handling 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}
        mock_response.json.return_value = {}
        
        http_error = requests.exceptions.HTTPError(response=mock_response)
        
        with self.assertRaises(ShopifyRateLimitError) as context:
            self.error_handler.handle_request_error(http_error)
        
        self.assertEqual(context.exception.retry_after, 30)
    
    def test_handle_request_error_timeout(self):
        """Test handling timeout error."""
        timeout_error = requests.exceptions.Timeout()
        
        with self.assertRaises(ShopifyAPIError) as context:
            self.error_handler.handle_request_error(timeout_error)
        
        self.assertIn("timeout", str(context.exception).lower())
    
    def test_is_retryable_error(self):
        """Test checking if error is retryable."""
        # Rate limit error should be retryable
        rate_limit_error = ShopifyRateLimitError("Rate limited")
        self.assertTrue(self.error_handler.is_retryable_error(rate_limit_error))
        
        # Timeout should be retryable
        timeout_error = requests.exceptions.Timeout()
        self.assertTrue(self.error_handler.is_retryable_error(timeout_error))
        
        # Generic API error should not be retryable
        api_error = ShopifyAPIError("Generic error")
        self.assertFalse(self.error_handler.is_retryable_error(api_error))
    
    def test_get_retry_delay(self):
        """Test getting retry delay."""
        # Rate limit error with retry_after
        rate_limit_error = ShopifyRateLimitError("Rate limited", retry_after=120)
        delay = self.error_handler.get_retry_delay(rate_limit_error)
        self.assertEqual(delay, 120)
        
        # Generic error should have default delay
        generic_error = Exception("Generic")
        delay = self.error_handler.get_retry_delay(generic_error)
        self.assertEqual(delay, 1)


if __name__ == '__main__':
    unittest.main()
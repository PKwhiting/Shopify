"""
Tests for error handling and edge case scenarios

Validates error handling robustness and prevents random exceptions.
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import requests

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.client import ShopifyClient
from shopify.config import ShopifyConfig
from shopify.query_builder import QueryBuilder
from shopify.webhooks.handler import WebhookHandler
from shopify.utils.retry import RetryHandler
from shopify.utils.error_handler import ShopifyAPIError, ShopifyRateLimitError, ShopifyGraphQLError


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.shop_url = "test-shop.myshopify.com"
        self.api_key = "test_api_key"
    
    def test_invalid_json_response_handling(self):
        """Test handling of invalid JSON responses."""
        client = ShopifyClient(self.shop_url, self.api_key)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch.object(client._session, 'post', return_value=mock_response):
            with self.assertRaises(RuntimeError) as context:
                client.execute_query("query { test }")
            
            self.assertIn("Invalid response format from API", str(context.exception))
    
    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        client = ShopifyClient(self.shop_url, self.api_key)
        
        connection_error = requests.exceptions.ConnectionError("Connection failed")
        
        with patch.object(client._session, 'post', side_effect=connection_error):
            with self.assertRaises(ShopifyAPIError) as context:
                client.execute_query("query { test }")
            
            self.assertIn("Connection error", str(context.exception))
    
    def test_timeout_handling(self):
        """Test handling of request timeouts."""
        client = ShopifyClient(self.shop_url, self.api_key)
        
        timeout_error = requests.exceptions.Timeout("Request timeout")
        
        with patch.object(client._session, 'post', side_effect=timeout_error):
            with self.assertRaises(ShopifyAPIError) as context:
                client.execute_query("query { test }")
            
            self.assertIn("Request timeout", str(context.exception))
    
    def test_rate_limit_retry_behavior(self):
        """Test retry behavior for rate limiting."""
        config = ShopifyConfig(max_retries=2, retry_delay=1)
        client = ShopifyClient(self.shop_url, self.api_key, config=config)
        
        # First call: rate limit error
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        rate_limit_error = requests.exceptions.HTTPError(response=rate_limit_response)
        
        # Second call: success
        success_response = Mock()
        success_response.json.return_value = {"data": {"test": True}}
        success_response.raise_for_status.return_value = None
        
        with patch.object(client._session, 'post', side_effect=[rate_limit_error, success_response]):
            result = client.execute_query("query { test }")
            self.assertEqual(result, {"test": True})
    
    def test_retry_calculation_edge_cases(self):
        """Test retry delay calculation edge cases."""
        config = ShopifyConfig(max_retries=5, retry_delay=0)
        retry_handler = RetryHandler(config)
        
        # Test with invalid retry delay
        delay = retry_handler._calculate_delay(Exception("test"), 0)
        self.assertGreaterEqual(delay, 0.1)  # Should have minimum delay
        
        # Test with very high attempt number
        delay = retry_handler._calculate_delay(Exception("test"), 10)
        self.assertLessEqual(delay, 60.0)  # Should be capped at 60 seconds
    
    def test_configuration_validation_edge_cases(self):
        """Test configuration validation with edge cases."""
        # Test boundary values
        config = ShopifyConfig(
            timeout=1,  # Minimum valid timeout
            max_retries=0,  # Minimum retries
            retry_delay=1,  # Minimum delay
            page_size=1  # Minimum page size
        )
        self.assertEqual(config.timeout, 1)
        self.assertEqual(config.max_retries, 0)
        
        # Test maximum values
        config = ShopifyConfig(
            timeout=300,  # Maximum valid timeout
            max_retries=10,  # Maximum retries
            retry_delay=60,  # Maximum delay
            page_size=250  # Maximum page size
        )
        self.assertEqual(config.timeout, 300)
        self.assertEqual(config.max_retries, 10)
        
        # Test invalid values
        with self.assertRaises(ValueError):
            ShopifyConfig(timeout=0)  # Too low
        
        with self.assertRaises(ValueError):
            ShopifyConfig(timeout=301)  # Too high
        
        with self.assertRaises(ValueError):
            ShopifyConfig(max_retries=-1)  # Negative
        
        with self.assertRaises(ValueError):
            ShopifyConfig(page_size=0)  # Too low
        
        with self.assertRaises(ValueError):
            ShopifyConfig(page_size=251)  # Too high
    
    def test_query_builder_edge_cases(self):
        """Test query builder with edge cases."""
        builder = QueryBuilder()
        
        # Test building without fields
        with self.assertRaises(ValueError):
            builder.build()
        
        # Test adding invalid field
        with self.assertRaises(ValueError):
            builder.add_field("")
        
        with self.assertRaises(ValueError):
            builder.add_field("   ")  # Only whitespace
        
        # Test adding invalid variable
        with self.assertRaises(ValueError):
            builder.add_variable("", "String!", "value")
        
        with self.assertRaises(ValueError):
            builder.add_variable("name", "", "value")
    
    def test_webhook_handler_edge_cases(self):
        """Test webhook handler with edge cases."""
        handler = WebhookHandler()
        
        # Test invalid topic registration
        with self.assertRaises(ValueError):
            handler.register_handler("", lambda x: x)
        
        with self.assertRaises(ValueError):
            handler.register_handler("  ", lambda x: x)
        
        # Test invalid handler registration
        with self.assertRaises(ValueError):
            handler.register_handler("test/topic", "not_callable")
        
        # Test handling with invalid topic
        result = handler.handle_webhook("", "{}")
        self.assertFalse(result['processed'])
        self.assertIn('Topic must be a non-empty string', result['error'])
        
        # Test handling with invalid JSON
        result = handler.handle_webhook("test/topic", "invalid json")
        self.assertIn('error', result)
        self.assertIn('Invalid JSON payload', result['error'])
    
    def test_webhook_signature_verification_edge_cases(self):
        """Test webhook signature verification edge cases."""
        handler = WebhookHandler("secret", verify_signature=True)
        
        # Test without headers
        result = handler.handle_webhook("test/topic", "{}")
        self.assertFalse(result['processed'])
        self.assertIn('no headers provided', result['error'])
        
        # Test with wrong signature
        headers = {"X-Shopify-Hmac-Sha256": "invalid_signature"}
        result = handler.handle_webhook("test/topic", "{}", headers)
        self.assertFalse(result['processed'])
        self.assertIn('signature verification failed', result['error'])
    
    def test_client_session_error_recovery(self):
        """Test client session error recovery."""
        client = ShopifyClient(self.shop_url, self.api_key)
        
        # Simulate session being closed/invalid
        client._session = None
        
        # The client should handle this gracefully
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"test": True}}
        mock_response.raise_for_status.return_value = None
        
        # This should raise an error since session is None
        with self.assertRaises((AttributeError, RuntimeError)):
            client.execute_query("query { test }")
    
    def test_malformed_error_responses(self):
        """Test handling of malformed error responses."""
        client = ShopifyClient(self.shop_url, self.api_key)
        
        # Test malformed GraphQL errors
        mock_response = Mock()
        mock_response.json.return_value = {
            "errors": [
                {"message": "Test error"},
                {},  # Empty error object
                {"message": None},  # None message
                {"extensions": {"code": "TEST_ERROR"}}  # No message
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client._session, 'post', return_value=mock_response):
            with self.assertRaises(ShopifyGraphQLError):  # Should be GraphQL error
                client.execute_query("query { test }")
    
    def test_concurrent_session_access_safety(self):
        """Test that concurrent session access doesn't cause corruption."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        client = ShopifyClient(self.shop_url, self.api_key)
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                # Simulate different response times
                import time
                time.sleep(0.001 * (request_id % 5))
                
                mock_response = Mock()
                mock_response.json.return_value = {"data": {"id": request_id}}
                mock_response.raise_for_status.return_value = None
                
                with patch.object(client._session, 'post', return_value=mock_response):
                    result = client.execute_query(f"query {{ test_{request_id} }}")
                    results.append((request_id, result))
                    
            except Exception as e:
                errors.append((request_id, str(e)))
        
        # Run concurrent requests that might interfere with each other
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()
        
        # Should have no errors and all results
        self.assertEqual(len(errors), 0, f"Concurrent errors: {errors[:5]}...")
        self.assertEqual(len(results), 100)
    
    def test_pagination_edge_cases(self):
        """Test pagination helper with edge cases."""
        from shopify.utils.pagination import PaginationHelper
        
        helper = PaginationHelper()
        
        # Test with empty data
        self.assertEqual(helper.get_page_info({}, "products"), {})
        self.assertFalse(helper.has_next_page({}, "products"))
        self.assertEqual(helper.extract_nodes({}, "products"), [])
        
        # Test with malformed data
        malformed_data = {
            "products": {
                "edges": [
                    {},  # Empty edge
                    {"node": None},  # None node
                    {"node": {"id": "123"}},  # Valid node
                ]
            }
        }
        
        nodes = helper.extract_nodes(malformed_data, "products")
        self.assertEqual(len(nodes), 3)
        self.assertEqual(nodes[0], {})  # Empty dict
        self.assertIsNone(nodes[1])  # None
        self.assertEqual(nodes[2], {"id": "123"})  # Valid


if __name__ == '__main__':
    unittest.main()
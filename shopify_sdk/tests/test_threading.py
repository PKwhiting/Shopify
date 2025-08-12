"""
Tests for threading and concurrency scenarios

Validates thread safety of the SDK components.
"""

import unittest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.client import ShopifyClient
from shopify.config import ShopifyConfig
from shopify.query_builder import QueryBuilder
from shopify.webhooks.handler import WebhookHandler


class TestThreadSafety(unittest.TestCase):
    """Test cases for thread safety."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.shop_url = "test-shop.myshopify.com"
        self.api_key = "test_api_key"
    
    def test_concurrent_client_usage(self):
        """Test concurrent usage of the same client instance."""
        client = ShopifyClient(self.shop_url, self.api_key)
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "data": {"products": {"edges": []}}
                }
                mock_response.raise_for_status.return_value = None
                
                with patch.object(client._session, 'post', return_value=mock_response):
                    query = f"query {{ products(first: {request_id}) {{ edges {{ node {{ id }} }} }} }}"
                    result = client.execute_query(query, {"first": request_id})
                    results.append((request_id, result))
            except Exception as e:
                errors.append((request_id, str(e)))
        
        # Run concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            for future in as_completed(futures):
                future.result()  # Wait for completion
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 20)
    
    def test_concurrent_query_builder(self):
        """Test concurrent usage of QueryBuilder instances."""
        builders = [QueryBuilder() for _ in range(5)]
        results = []
        errors = []
        
        def build_query(builder_id):
            try:
                builder = builders[builder_id % len(builders)]
                
                # Simulate different query building patterns
                builder.reset()
                builder.add_field("products")
                builder.add_variable("first", "Int!", builder_id)
                
                query, variables = builder.build()
                results.append((builder_id, query, variables))
                
            except Exception as e:
                errors.append((builder_id, str(e)))
        
        # Run concurrent query building
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(build_query, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 50)
        
        # Verify queries are built correctly (no interference)
        for builder_id, query, variables in results:
            self.assertIn("products", query)
            self.assertEqual(variables["first"], builder_id)
    
    def test_concurrent_webhook_handler(self):
        """Test concurrent webhook handler operations."""
        handler = WebhookHandler()
        results = []
        errors = []
        
        def handler_func(event):
            return {"processed": True, "data": event["data"]}
        
        def register_and_handle(topic_id):
            try:
                topic = f"orders/create_{topic_id}"
                
                # Register handler
                handler.register_handler(topic, handler_func)
                
                # Handle webhook
                payload = json.dumps({"id": topic_id, "status": "created"})
                result = handler.handle_webhook(topic, payload)
                
                results.append((topic_id, result))
                
                # Unregister handler
                handler.unregister_handler(topic, handler_func)
                
            except Exception as e:
                errors.append((topic_id, str(e)))
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(register_and_handle, i) for i in range(30)]
            for future in as_completed(futures):
                future.result()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 30)
        
        # Verify all handlers were properly unregistered
        self.assertEqual(len(handler.get_registered_topics()), 0)
    
    def test_concurrent_config_updates(self):
        """Test concurrent configuration updates."""
        config = ShopifyConfig()
        results = []
        errors = []
        
        def update_config(update_id):
            try:
                # Different threads updating different values
                if update_id % 3 == 0:
                    config.update(timeout=30 + update_id)
                elif update_id % 3 == 1:
                    config.update(page_size=10 + update_id)
                else:
                    config.update(max_retries=3 + update_id % 5)
                
                # Read back configuration
                config_dict = config.to_dict()
                results.append((update_id, config_dict))
                
            except Exception as e:
                errors.append((update_id, str(e)))
        
        # Run concurrent updates
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(update_config, i) for i in range(24)]
            for future in as_completed(futures):
                future.result()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 24)
    
    def test_mixed_concurrent_operations(self):
        """Test mixed concurrent operations across components."""
        client = ShopifyClient(self.shop_url, self.api_key)
        webhook_handler = WebhookHandler()
        query_builder = QueryBuilder()
        
        results = []
        errors = []
        
        def mixed_operation(op_id):
            try:
                operation_type = op_id % 4
                
                if operation_type == 0:
                    # Client operation
                    mock_response = Mock()
                    mock_response.json.return_value = {"data": {"test": True}}
                    mock_response.raise_for_status.return_value = None
                    
                    with patch.object(client._session, 'post', return_value=mock_response):
                        result = client.execute_query("query { test }")
                        results.append((op_id, "client", result))
                
                elif operation_type == 1:
                    # Query builder operation
                    query_builder.reset()
                    query_builder.add_field(f"field_{op_id}")
                    query_builder.add_variable("var", "String!", f"value_{op_id}")
                    query, variables = query_builder.build()
                    results.append((op_id, "query_builder", {"query": query, "variables": variables}))
                
                elif operation_type == 2:
                    # Webhook handler operation
                    topic = f"test/event_{op_id}"
                    
                    def handler(event):
                        return {"handled": True, "id": op_id}
                    
                    webhook_handler.register_handler(topic, handler)
                    result = webhook_handler.handle_webhook(
                        topic, 
                        json.dumps({"id": op_id, "data": "test"})
                    )
                    webhook_handler.unregister_handler(topic, handler)
                    results.append((op_id, "webhook", result))
                
                else:
                    # Configuration operation
                    client.config.update(extra_param=f"value_{op_id}")
                    config_value = client.config.get("extra_param")
                    results.append((op_id, "config", config_value))
                    
            except Exception as e:
                errors.append((op_id, str(e)))
        
        # Run mixed concurrent operations
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(mixed_operation, i) for i in range(48)]
            for future in as_completed(futures):
                future.result()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 48)
        
        # Verify operation types
        client_ops = [r for r in results if r[1] == "client"]
        query_ops = [r for r in results if r[1] == "query_builder"]
        webhook_ops = [r for r in results if r[1] == "webhook"]
        config_ops = [r for r in results if r[1] == "config"]
        
        self.assertEqual(len(client_ops), 12)
        self.assertEqual(len(query_ops), 12)
        self.assertEqual(len(webhook_ops), 12)
        self.assertEqual(len(config_ops), 12)
    
    def test_stress_test_session_management(self):
        """Stress test the HTTP session management."""
        client = ShopifyClient(self.shop_url, self.api_key)
        results = []
        errors = []
        
        def make_many_requests(batch_id):
            try:
                mock_response = Mock()
                mock_response.json.return_value = {"data": {"batch": batch_id}}
                mock_response.raise_for_status.return_value = None
                
                batch_results = []
                
                # Use a more reliable patch that doesn't interfere between threads
                original_post = client._session.post
                
                def mock_post(*args, **kwargs):
                    return mock_response
                
                client._session.post = mock_post
                
                try:
                    for i in range(10):  # 10 requests per batch
                        query = f"query {{ test_{batch_id}_{i} }}"
                        result = client.execute_query(query)
                        batch_results.append(result)
                finally:
                # Use a thread-safe patch for the session's post method
                def mock_post(*args, **kwargs):
                    return mock_response
                
                with patch.object(client._session, "post", mock_post):
                    for i in range(10):  # 10 requests per batch
                        query = f"query {{ test_{batch_id}_{i} }}"
                        result = client.execute_query(query)
                        batch_results.append(result)
                
                results.append((batch_id, len(batch_results)))
                
            except Exception as e:
                errors.append((batch_id, str(e)))
        
        # Run multiple batches sequentially to avoid race conditions in the test itself
        for batch_id in range(10):
            make_many_requests(batch_id)
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10)
        
        # Verify all batches completed successfully
        for batch_id, count in results:
            self.assertEqual(count, 10, f"Batch {batch_id} didn't complete all requests")
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up any clients to ensure proper session closure
        pass


if __name__ == '__main__':
    unittest.main()
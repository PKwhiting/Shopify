"""
Tests for Webhooks module

Unit tests for webhook verification and handling.
"""

import unittest
from unittest.mock import Mock
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.webhooks.verifier import WebhookVerifier
from shopify.webhooks.handler import WebhookHandler


class TestWebhookVerifier(unittest.TestCase):
    """Test cases for WebhookVerifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.webhook_secret = "test_webhook_secret"
        self.verifier = WebhookVerifier(self.webhook_secret)
    
    def test_webhook_verifier_initialization(self):
        """Test verifier initialization."""
        self.assertEqual(self.verifier.webhook_secret, self.webhook_secret)
    
    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        payload = '{"id": 123, "test": "data"}'
        # This would be the actual HMAC signature in a real scenario
        signature = self.verifier._compute_signature(payload)
        
        result = self.verifier.verify_signature(payload, signature)
        self.assertTrue(result)
    
    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        payload = '{"id": 123, "test": "data"}'
        invalid_signature = "invalid_signature"
        
        result = self.verifier.verify_signature(payload, invalid_signature)
        self.assertFalse(result)
    
    def test_verify_signature_empty(self):
        """Test signature verification with empty signature."""
        payload = '{"id": 123, "test": "data"}'
        
        result = self.verifier.verify_signature(payload, "")
        self.assertFalse(result)
    
    def test_verify_request_with_headers(self):
        """Test request verification with headers."""
        payload = '{"id": 123, "test": "data"}'
        signature = self.verifier._compute_signature(payload)
        headers = {"X-Shopify-Hmac-Sha256": signature}
        
        result = self.verifier.verify_request(payload, headers)
        self.assertTrue(result)
    
    def test_verify_request_missing_header(self):
        """Test request verification with missing signature header."""
        payload = '{"id": 123, "test": "data"}'
        headers = {}
        
        result = self.verifier.verify_request(payload, headers)
        self.assertFalse(result)


class TestWebhookHandler(unittest.TestCase):
    """Test cases for WebhookHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = WebhookHandler()
    
    def test_webhook_handler_initialization(self):
        """Test handler initialization."""
        self.assertEqual(len(self.handler._event_handlers), 0)
    
    def test_register_handler(self):
        """Test registering a webhook handler."""
        def test_handler(event):
            return {"processed": True}
        
        self.handler.register_handler("orders/create", test_handler)
        
        self.assertIn("orders/create", self.handler._event_handlers)
        self.assertEqual(len(self.handler._event_handlers["orders/create"]), 1)
    
    def test_unregister_handler(self):
        """Test unregistering a webhook handler."""
        def test_handler(event):
            return {"processed": True}
        
        self.handler.register_handler("orders/create", test_handler)
        result = self.handler.unregister_handler("orders/create", test_handler)
        
        self.assertTrue(result)
        # Topic should be removed when no handlers remain
        self.assertNotIn("orders/create", self.handler._event_handlers)
    
    def test_handle_webhook_success(self):
        """Test successful webhook handling."""
        def test_handler(event):
            return {"order_id": event["data"]["id"]}
        
        self.handler.register_handler("orders/create", test_handler)
        
        payload = json.dumps({"id": 12345, "total_price": "100.00"})
        result = self.handler.handle_webhook("orders/create", payload)
        
        self.assertTrue(result["processed"])
        self.assertEqual(result["handlers_executed"], 1)
        self.assertTrue(result["results"][0]["success"])
    
    def test_handle_webhook_invalid_json(self):
        """Test webhook handling with invalid JSON."""
        payload = "invalid json"
        result = self.handler.handle_webhook("orders/create", payload)
        
        self.assertFalse(result["processed"])
        self.assertIn("Invalid JSON payload", result["error"])
    
    def test_get_registered_topics(self):
        """Test getting registered topics."""
        def handler1(event): pass
        def handler2(event): pass
        
        self.handler.register_handler("orders/create", handler1)
        self.handler.register_handler("products/update", handler2)
        
        topics = self.handler.get_registered_topics()
        
        self.assertEqual(len(topics), 2)
        self.assertIn("orders/create", topics)
        self.assertIn("products/update", topics)
    
    def test_get_handler_count(self):
        """Test getting handler count for a topic."""
        def handler1(event): pass
        def handler2(event): pass
        
        self.handler.register_handler("orders/create", handler1)
        self.handler.register_handler("orders/create", handler2)
        
        count = self.handler.get_handler_count("orders/create")
        self.assertEqual(count, 2)
        
        count_empty = self.handler.get_handler_count("nonexistent/topic")
        self.assertEqual(count_empty, 0)
    
    def test_handle_order_created(self):
        """Test default order created handler."""
        event = {
            "topic": "orders/create",
            "data": {
                "id": 12345,
                "order_number": 1001,
                "email": "test@example.com",
                "total_price": "150.00"
            }
        }
        
        result = self.handler.handle_order_created(event)
        
        self.assertTrue(result["processed"])
        self.assertEqual(result["order_id"], 12345)
        self.assertEqual(result["order_number"], 1001)
        self.assertEqual(result["customer_email"], "test@example.com")
        self.assertEqual(result["total_price"], "150.00")


if __name__ == '__main__':
    unittest.main()
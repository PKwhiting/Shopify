"""
Tests for Authentication module

Unit tests for API key authentication.
"""

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.auth.api_key import ApiKeyAuth


class TestApiKeyAuth(unittest.TestCase):
    """Test cases for ApiKeyAuth."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key_12345"
        self.auth = ApiKeyAuth(self.api_key)
    
    def test_auth_initialization(self):
        """Test auth initialization."""
        self.assertEqual(self.auth.api_key, self.api_key)
    
    def test_get_headers(self):
        """Test getting authentication headers."""
        headers = self.auth.get_headers()
        
        expected_headers = {
            "X-Shopify-Access-Token": self.api_key
        }
        
        self.assertEqual(headers, expected_headers)
    
    def test_is_valid_with_valid_key(self):
        """Test validation with valid API key."""
        self.assertTrue(self.auth.is_valid())
    
    def test_is_valid_with_empty_key(self):
        """Test validation with empty API key."""
        empty_auth = ApiKeyAuth("")
        self.assertFalse(empty_auth.is_valid())
    
    def test_is_valid_with_whitespace_key(self):
        """Test validation with whitespace-only API key."""
        whitespace_auth = ApiKeyAuth("   ")
        self.assertFalse(whitespace_auth.is_valid())
    
    def test_is_valid_with_none_key(self):
        """Test validation with None API key."""
        none_auth = ApiKeyAuth(None)
        self.assertFalse(none_auth.is_valid())


if __name__ == '__main__':
    unittest.main()
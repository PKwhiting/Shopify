"""
Tests for Shopify Client

Unit tests for the main ShopifyClient class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.client import ShopifyClient
from shopify.utils.error_handler import ShopifyAPIError, ShopifyGraphQLError


class TestShopifyClient(unittest.TestCase):
    """Test cases for ShopifyClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.shop_url = "test-shop.myshopify.com"
        self.api_key = "test_api_key"
        self.client = ShopifyClient(self.shop_url, self.api_key)
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.shop_url, "test-shop.myshopify.com")
        self.assertEqual(self.client.api_version, "2024-01")
        self.assertIsNotNone(self.client.auth)
        self.assertIsNotNone(self.client.error_handler)
        self.assertEqual(
            self.client.base_url, 
            "https://test-shop.myshopify.com/admin/api/2024-01/graphql.json"
        )
    
    def test_client_initialization_with_custom_version(self):
        """Test client initialization with custom API version."""
        client = ShopifyClient(self.shop_url, self.api_key, "2023-10")
        self.assertEqual(client.api_version, "2023-10")
        self.assertEqual(
            client.base_url,
            "https://test-shop.myshopify.com/admin/api/2023-10/graphql.json"
        )
    
    @patch('shopify.client.requests.post')
    def test_execute_query_success(self, mock_post):
        """Test successful query execution."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"products": {"edges": []}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        query = "query { products { edges { node { id } } } }"
        result = self.client.execute_query(query)
        
        self.assertEqual(result, {"products": {"edges": []}})
        mock_post.assert_called_once()
    
    @patch('shopify.client.requests.post')
    def test_execute_query_with_variables(self, mock_post):
        """Test query execution with variables."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"products": {"edges": []}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        query = "query($first: Int!) { products(first: $first) { edges { node { id } } } }"
        variables = {"first": 10}
        
        result = self.client.execute_query(query, variables)
        
        # Verify the request payload
        call_args = mock_post.call_args
        request_data = json.loads(call_args[1]['data'])
        self.assertEqual(request_data['query'], query)
        self.assertEqual(request_data['variables'], variables)
    
    @patch('shopify.client.requests.post')
    def test_execute_query_graphql_error(self, mock_post):
        """Test handling of GraphQL errors."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errors": [{"message": "Field 'invalid' doesn't exist"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        query = "query { invalid }"
        
        with self.assertRaises(ShopifyGraphQLError):
            self.client.execute_query(query)
    
    @patch('shopify.client.requests.post')
    def test_execute_mutation(self, mock_post):
        """Test mutation execution."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"productCreate": {"product": {"id": "123"}}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        mutation = "mutation { productCreate(input: {title: \"Test\"}) { product { id } } }"
        result = self.client.execute_mutation(mutation)
        
        self.assertEqual(result, {"productCreate": {"product": {"id": "123"}}})


if __name__ == '__main__':
    unittest.main()
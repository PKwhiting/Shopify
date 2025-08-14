#!/usr/bin/env python3
"""
Test script for environment variable client auto-initialization functionality.
This script validates that Order and Product classes can auto-initialize ShopifyClient
from environment variables.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add the package to path
sys.path.insert(0, 'Shopify')

from Shopify.shopify.client import ShopifyClient, create_client_from_environment
from Shopify.shopify.product import Product
from Shopify.shopify.order import Order


class TestEnvironmentClientInit(unittest.TestCase):
    """Test cases for environment variable client auto-initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing environment variables
        env_vars = ['SHOPIFY_ACCESS_TOKEN', 'SHOP_URL']
        self.original_env = {}
        for var in env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
        
        # Clear test environment variables
        env_vars = ['SHOPIFY_ACCESS_TOKEN', 'SHOP_URL']
        for var in env_vars:
            if var in os.environ and var not in self.original_env:
                del os.environ[var]
    
    def test_create_client_from_environment_success(self):
        """Test creating client from environment variables successfully."""
        # Set up environment variables
        os.environ['SHOPIFY_ACCESS_TOKEN'] = 'test_token_12345'
        os.environ['SHOP_URL'] = 'test-shop.myshopify.com'
        
        client = create_client_from_environment()
        
        self.assertIsInstance(client, ShopifyClient)
        self.assertEqual(client.auth.api_key, 'test_token_12345')
        self.assertEqual(client.shop_url, 'test-shop.myshopify.com')
    
    def test_create_client_from_environment_missing_token(self):
        """Test creating client without access token raises error."""
        os.environ['SHOP_URL'] = 'test-shop.myshopify.com'
        # No SHOPIFY_ACCESS_TOKEN set
        
        with self.assertRaises(ValueError) as context:
            create_client_from_environment()
        
        self.assertIn("API key is required", str(context.exception))
        self.assertIn("SHOPIFY_ACCESS_TOKEN", str(context.exception))
    
    def test_create_client_from_environment_missing_shop_url(self):
        """Test creating client without shop URL raises error."""
        os.environ['SHOPIFY_ACCESS_TOKEN'] = 'test_token_12345'
        # No SHOP_URL set
        
        with self.assertRaises(ValueError) as context:
            create_client_from_environment()
        
        self.assertIn("Shop URL must be", str(context.exception))


class TestOrderEnvironmentInit(unittest.TestCase):
    """Test Order class with environment variable initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set up environment variables for successful client creation
        os.environ['SHOPIFY_ACCESS_TOKEN'] = 'test_token_12345'
        os.environ['SHOP_URL'] = 'test-shop.myshopify.com'
        
        # Mock client to avoid actual API calls
        self.mock_client = MagicMock(spec=ShopifyClient)
        # Configure auth as a mock with api_key attribute
        self.mock_client.auth = MagicMock()
        self.mock_client.auth.api_key = 'test_token_12345'
        self.mock_client.shop_url = 'test-shop.myshopify.com'
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up environment variables
        env_vars = ['SHOPIFY_ACCESS_TOKEN', 'SHOP_URL']
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    @patch('Shopify.shopify.client.create_client_from_environment')
    @patch('Shopify.shopify.resources.orders.Orders')
    def test_order_get_with_env_client(self, mock_orders, mock_create_client):
        """Test Order.get with environment variable client creation."""
        # Setup mocks
        mock_create_client.return_value = self.mock_client
        mock_resource = MagicMock()
        mock_orders.return_value = mock_resource
        mock_resource.get.return_value = {'order': {'id': 'test_order_123', 'name': '#1001'}}
        
        # Test new style call: Order.get(order_id)
        order = Order.get('test_order_123')
        
        # Verify client was created from environment
        mock_create_client.assert_called_once()
        mock_orders.assert_called_once_with(self.mock_client)
        mock_resource.get.assert_called_once_with('test_order_123')
        
        # Verify order was created correctly
        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, 'test_order_123')
    
    @patch('Shopify.shopify.resources.orders.Orders')
    def test_order_get_with_explicit_client(self, mock_orders):
        """Test Order.get with explicit client (traditional way)."""
        # Setup mocks
        mock_resource = MagicMock()
        mock_orders.return_value = mock_resource
        mock_resource.get.return_value = {'order': {'id': 'test_order_123', 'name': '#1001'}}
        
        # Test traditional style call: Order.get(client, order_id)
        order = Order.get(self.mock_client, 'test_order_123')
        
        # Verify explicit client was used
        mock_orders.assert_called_once_with(self.mock_client)
        mock_resource.get.assert_called_once_with('test_order_123')
        
        # Verify order was created correctly
        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, 'test_order_123')
    
    @patch('Shopify.shopify.client.create_client_from_environment')
    @patch('Shopify.shopify.resources.orders.Orders')
    def test_order_get_buyer_info_with_env_client(self, mock_orders, mock_create_client):
        """Test Order.get_buyer_info with environment variable client creation."""
        # Setup mocks
        mock_create_client.return_value = self.mock_client
        mock_resource = MagicMock()
        mock_orders.return_value = mock_resource
        buyer_info = {'order': {'customer': {'email': 'test@example.com'}}}
        mock_resource.get_buyer_info.return_value = buyer_info
        
        # Test new style call: Order.get_buyer_info(order_id)
        result = Order.get_buyer_info('test_order_123')
        
        # Verify client was created from environment
        mock_create_client.assert_called_once()
        mock_orders.assert_called_once_with(self.mock_client)
        mock_resource.get_buyer_info.assert_called_once_with('test_order_123')
        
        # Verify result
        self.assertEqual(result, buyer_info['order'])
    
    @patch('Shopify.shopify.client.create_client_from_environment')
    @patch('Shopify.shopify.resources.orders.Orders')
    def test_order_list_with_env_client(self, mock_orders, mock_create_client):
        """Test Order.list with environment variable client creation."""
        # Setup mocks
        mock_create_client.return_value = self.mock_client
        mock_resource = MagicMock()
        mock_orders.return_value = mock_resource
        
        # Mock the paginated response
        orders_data = {
            'orders': {
                'edges': [
                    {'node': {'id': 'order_1', 'name': '#1001'}},
                    {'node': {'id': 'order_2', 'name': '#1002'}}
                ],
                'pageInfo': {'hasNextPage': False, 'endCursor': 'cursor123'}
            }
        }
        mock_resource.list.return_value = orders_data
        
        # Test new style call: Order.list()
        orders = list(Order.list())
        
        # Verify client was created from environment
        mock_create_client.assert_called_once()
        mock_orders.assert_called_once_with(self.mock_client)
        mock_resource.list.assert_called_with(first=250, after=None)
        
        # Verify orders were created correctly
        self.assertEqual(len(orders), 2)
        self.assertIsInstance(orders[0], Order)
        self.assertEqual(orders[0].id, 'order_1')


class TestProductEnvironmentInit(unittest.TestCase):
    """Test Product class with environment variable initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set up environment variables for successful client creation
        os.environ['SHOPIFY_ACCESS_TOKEN'] = 'test_token_12345'
        os.environ['SHOP_URL'] = 'test-shop.myshopify.com'
        
        # Mock client to avoid actual API calls
        self.mock_client = MagicMock(spec=ShopifyClient)
        # Configure auth as a mock with api_key attribute
        self.mock_client.auth = MagicMock()
        self.mock_client.auth.api_key = 'test_token_12345'
        self.mock_client.shop_url = 'test-shop.myshopify.com'
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up environment variables
        env_vars = ['SHOPIFY_ACCESS_TOKEN', 'SHOP_URL']
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    @patch('Shopify.shopify.client.create_client_from_environment')
    def test_product_get_with_env_client(self, mock_create_client):
        """Test Product.get with environment variable client creation."""
        # Setup mocks
        mock_create_client.return_value = self.mock_client
        product_data = {'id': 'test_product_123', 'title': 'Test Product'}
        self.mock_client.execute_query.return_value = {'product': product_data}
        
        # Test new style call: Product.get(product_id)
        product = Product.get('test_product_123')
        
        # Verify client was created from environment
        mock_create_client.assert_called_once()
        self.mock_client.execute_query.assert_called_once()
        
        # Verify product was created correctly
        self.assertIsInstance(product, Product)
        self.assertEqual(product.id, 'test_product_123')
    
    def test_product_get_with_explicit_client(self):
        """Test Product.get with explicit client (traditional way)."""
        # Setup mocks
        product_data = {'id': 'test_product_123', 'title': 'Test Product'}
        self.mock_client.execute_query.return_value = {'product': product_data}
        
        # Test traditional style call: Product.get(client, product_id)
        product = Product.get(self.mock_client, 'test_product_123')
        
        # Verify explicit client was used
        self.mock_client.execute_query.assert_called_once()
        
        # Verify product was created correctly
        self.assertIsInstance(product, Product)
        self.assertEqual(product.id, 'test_product_123')
    
    @patch('Shopify.shopify.client.create_client_from_environment')
    def test_product_search_with_env_client(self, mock_create_client):
        """Test Product.search with environment variable client creation."""
        # Setup mocks
        mock_create_client.return_value = self.mock_client
        products_data = {
            'products': {
                'edges': [
                    {'node': {'id': 'product_1', 'title': 'Product 1'}},
                    {'node': {'id': 'product_2', 'title': 'Product 2'}}
                ]
            }
        }
        self.mock_client.execute_query.return_value = products_data
        
        # Test new style call: Product.search()
        products = Product.search()
        
        # Verify client was created from environment
        mock_create_client.assert_called_once()
        self.mock_client.execute_query.assert_called_once()
        
        # Verify products were created correctly
        self.assertEqual(len(products), 2)
        self.assertIsInstance(products[0], Product)
        self.assertEqual(products[0].id, 'product_1')
    
    @patch('Shopify.shopify.client.create_client_from_environment')
    def test_product_create_with_env_client(self, mock_create_client):
        """Test Product.create with environment variable client creation."""
        # Setup mocks
        mock_create_client.return_value = self.mock_client
        product_data = {'id': 'new_product_123', 'title': 'New Product'}
        mutation_response = {'productCreate': {'product': product_data, 'userErrors': []}}
        self.mock_client.execute_mutation.return_value = mutation_response
        
        input_data = {'title': 'New Product', 'productType': 'Test'}
        
        # Test new style call: Product.create(product_data)
        product = Product.create(input_data)
        
        # Verify client was created from environment
        mock_create_client.assert_called_once()
        self.mock_client.execute_mutation.assert_called_once()
        
        # Verify product was created correctly
        self.assertIsInstance(product, Product)
        self.assertEqual(product.id, 'new_product_123')


if __name__ == '__main__':
    unittest.main()
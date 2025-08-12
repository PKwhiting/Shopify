"""
Tests for SDK improvements

Tests for new validation, configuration, and base class functionality.
"""

import unittest
from unittest.mock import Mock
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.client import ShopifyClient
from shopify.config import ShopifyConfig
from shopify.resources import Products, Customers, Orders
from shopify.query_builder import QueryBuilder


class TestShopifyConfig(unittest.TestCase):
    """Test cases for ShopifyConfig."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = ShopifyConfig()
        self.assertEqual(config.api_version, "2024-01")
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_delay, 1)
        self.assertEqual(config.page_size, 10)
    
    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = ShopifyConfig(
            api_version="2023-10",
            timeout=60,
            max_retries=5,
            retry_delay=2,
            page_size=25
        )
        self.assertEqual(config.api_version, "2023-10")
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.retry_delay, 2)
        self.assertEqual(config.page_size, 25)
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Invalid timeout
        with self.assertRaises(ValueError):
            ShopifyConfig(timeout=-1)
        
        # Invalid API version
        with self.assertRaises(ValueError):
            ShopifyConfig(api_version="")
        
        # Invalid page size
        with self.assertRaises(ValueError):
            ShopifyConfig(page_size=300)
    
    def test_base_url_generation(self):
        """Test base URL generation."""
        config = ShopifyConfig()
        base_url = config.get_base_url("test-shop.myshopify.com")
        expected = "https://test-shop.myshopify.com/admin/api/2024-01/graphql.json"
        self.assertEqual(base_url, expected)


class TestClientValidation(unittest.TestCase):
    """Test cases for client validation."""
    
    def test_invalid_shop_url(self):
        """Test client with invalid shop URL."""
        with self.assertRaises(ValueError):
            ShopifyClient("", "test_key")
        
        with self.assertRaises(ValueError):
            ShopifyClient("invalid-url", "test_key")
    
    def test_invalid_api_key(self):
        """Test client with invalid API key."""
        with self.assertRaises(ValueError):
            ShopifyClient("test-shop.myshopify.com", "")
    
    def test_client_with_config(self):
        """Test client initialization with configuration."""
        config = ShopifyConfig(timeout=60)
        client = ShopifyClient("test-shop.myshopify.com", "test_key", config=config)
        self.assertEqual(client.config.timeout, 60)


class TestResourceValidation(unittest.TestCase):
    """Test cases for resource validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Mock()
        self.client.execute_query = Mock(return_value={})
        self.client.execute_mutation = Mock(return_value={})
        self.products = Products(self.client)
    
    def test_invalid_pagination_params(self):
        """Test invalid pagination parameters."""
        # Invalid first parameter
        with self.assertRaises(ValueError):
            self.products.list(first=-1)
        
        # Exceeds maximum
        with self.assertRaises(ValueError):
            self.products.list(first=300)
        
        # Invalid after parameter
        with self.assertRaises(ValueError):
            self.products.list(first=10, after="")
    
    def test_invalid_resource_id(self):
        """Test invalid resource ID."""
        # Empty ID
        with self.assertRaises(ValueError):
            self.products.get("")
        
        # None ID
        with self.assertRaises(ValueError):
            self.products.get(None)
        
        # Whitespace only
        with self.assertRaises(ValueError):
            self.products.get("   ")
    
    def test_invalid_create_data(self):
        """Test invalid create data."""
        # Non-dict data
        with self.assertRaises(ValueError):
            self.products.create("invalid")
        
        # Empty data
        with self.assertRaises(ValueError):
            self.products.create({})
    
    def test_invalid_update_data(self):
        """Test invalid update data."""
        # Non-dict data
        with self.assertRaises(ValueError):
            self.products.update("gid://shopify/Product/123", "invalid")
        
        # Empty data
        with self.assertRaises(ValueError):
            self.products.update("gid://shopify/Product/123", {})


class TestQueryBuilderValidation(unittest.TestCase):
    """Test cases for QueryBuilder validation."""
    
    def test_invalid_variable_params(self):
        """Test invalid variable parameters."""
        builder = QueryBuilder()
        
        # Empty variable name
        with self.assertRaises(ValueError):
            builder.add_variable("", "String!", "test")
        
        # Empty variable type
        with self.assertRaises(ValueError):
            builder.add_variable("test", "", "value")
    
    def test_invalid_field_params(self):
        """Test invalid field parameters."""
        builder = QueryBuilder()
        
        # Empty field
        with self.assertRaises(ValueError):
            builder.add_field("")
    
    def test_build_without_fields(self):
        """Test building query without fields."""
        builder = QueryBuilder()
        
        with self.assertRaises(ValueError):
            builder.build()
    
    def test_static_method_validation(self):
        """Test static method validation."""
        # Invalid first parameter
        with self.assertRaises(ValueError):
            QueryBuilder.build_product_query(first=-1)
        
        # Invalid after parameter
        with self.assertRaises(ValueError):
            QueryBuilder.build_product_query(first=10, after="")


class TestResourceInheritance(unittest.TestCase):
    """Test cases for resource inheritance."""
    
    def test_resource_names(self):
        """Test resource name methods."""
        client = Mock()
        client.execute_query = Mock()
        client.execute_mutation = Mock()
        
        products = Products(client)
        customers = Customers(client)
        orders = Orders(client)
        
        self.assertEqual(products.get_resource_name(), "product")
        self.assertEqual(products.get_plural_resource_name(), "products")
        
        self.assertEqual(customers.get_resource_name(), "customer")
        self.assertEqual(customers.get_plural_resource_name(), "customers")
        
        self.assertEqual(orders.get_resource_name(), "order")
        self.assertEqual(orders.get_plural_resource_name(), "orders")
    
    def test_invalid_client(self):
        """Test resource with invalid client."""
        # No client
        with self.assertRaises(ValueError):
            Products(None)
        
        # Invalid client without execute_query
        invalid_client = Mock()
        del invalid_client.execute_query  # Remove the method
        with self.assertRaises(ValueError):
            Products(invalid_client)


if __name__ == '__main__':
    unittest.main()
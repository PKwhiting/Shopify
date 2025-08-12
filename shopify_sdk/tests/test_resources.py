"""
Tests for Resources modules

Unit tests for products, customers, and orders resources.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.resources.products import Products
from shopify.resources.customers import Customers
from shopify.resources.orders import Orders


class TestProductsResource(unittest.TestCase):
    """Test cases for Products resource."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.products = Products(self.mock_client)
    
    def test_list_products(self):
        """Test listing products."""
        expected_result = {"products": {"edges": []}}
        self.mock_client.execute_query.return_value = expected_result
        
        result = self.products.list(first=10)
        
        self.assertEqual(result, expected_result)
        self.mock_client.execute_query.assert_called_once()
    
    def test_get_product(self):
        """Test getting a specific product."""
        product_id = "gid://shopify/Product/123"
        expected_result = {"product": {"id": product_id}}
        self.mock_client.execute_query.return_value = expected_result
        
        result = self.products.get(product_id)
        
        self.assertEqual(result, expected_result)
        call_args = self.mock_client.execute_query.call_args
        self.assertIn("getProduct", call_args[0][0])
        # Check that execute_query was called with 2 arguments: query and variables
        self.assertEqual(len(call_args[0]), 2)
        variables = call_args[0][1]  # Second positional argument
        self.assertEqual(variables["id"], product_id)
    
    def test_create_product(self):
        """Test creating a product."""
        product_data = {"title": "Test Product"}
        expected_result = {"productCreate": {"product": {"id": "123"}}}
        self.mock_client.execute_mutation.return_value = expected_result
        
        result = self.products.create(product_data)
        
        self.assertEqual(result, expected_result)
        self.mock_client.execute_mutation.assert_called_once()


class TestCustomersResource(unittest.TestCase):
    """Test cases for Customers resource."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.customers = Customers(self.mock_client)
    
    def test_list_customers(self):
        """Test listing customers."""
        expected_result = {"customers": {"edges": []}}
        self.mock_client.execute_query.return_value = expected_result
        
        result = self.customers.list(first=5)
        
        self.assertEqual(result, expected_result)
        self.mock_client.execute_query.assert_called_once()
    
    def test_get_customer(self):
        """Test getting a specific customer."""
        customer_id = "gid://shopify/Customer/456"
        expected_result = {"customer": {"id": customer_id}}
        self.mock_client.execute_query.return_value = expected_result
        
        result = self.customers.get(customer_id)
        
        self.assertEqual(result, expected_result)
        call_args = self.mock_client.execute_query.call_args
        self.assertIn("getCustomer", call_args[0][0])
        # Check that execute_query was called with 2 arguments: query and variables
        self.assertEqual(len(call_args[0]), 2)
        variables = call_args[0][1]  # Second positional argument
        self.assertEqual(variables["id"], customer_id)


class TestOrdersResource(unittest.TestCase):
    """Test cases for Orders resource."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.orders = Orders(self.mock_client)
    
    def test_list_orders(self):
        """Test listing orders."""
        expected_result = {"orders": {"edges": []}}
        self.mock_client.execute_query.return_value = expected_result
        
        result = self.orders.list(first=15)
        
        self.assertEqual(result, expected_result)
        self.mock_client.execute_query.assert_called_once()
    
    def test_get_order(self):
        """Test getting a specific order."""
        order_id = "gid://shopify/Order/789"
        expected_result = {"order": {"id": order_id}}
        self.mock_client.execute_query.return_value = expected_result
        
        result = self.orders.get(order_id)
        
        self.assertEqual(result, expected_result)
        call_args = self.mock_client.execute_query.call_args
        self.assertIn("getOrder", call_args[0][0])
        # Check that execute_query was called with 2 arguments: query and variables
        self.assertEqual(len(call_args[0]), 2)
        variables = call_args[0][1]  # Second positional argument
        self.assertEqual(variables["id"], order_id)
    
    def test_cancel_order(self):
        """Test cancelling an order."""
        order_id = "gid://shopify/Order/789"
        expected_result = {"orderCancel": {"order": {"id": order_id, "cancelled": True}}}
        self.mock_client.execute_mutation.return_value = expected_result
        
        result = self.orders.cancel(order_id, reason="customer")
        
        self.assertEqual(result, expected_result)
        call_args = self.mock_client.execute_mutation.call_args
        self.assertIn("orderCancel", call_args[0][0])
        # Check that execute_mutation was called with 2 arguments: query and variables
        self.assertEqual(len(call_args[0]), 2)
        variables = call_args[0][1]  # Second positional argument
        self.assertEqual(variables["orderId"], order_id)
        self.assertEqual(variables["reason"], "CUSTOMER")


if __name__ == '__main__':
    unittest.main()
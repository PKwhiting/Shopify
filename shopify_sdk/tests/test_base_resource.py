"""
Tests for BaseResource Class

Comprehensive tests for the BaseResource abstract base class including
inheritance, validation, error handling, and edge cases.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.resources.base import BaseResource
from shopify.client import ShopifyClient


class ConcreteResource(BaseResource):
    """Concrete implementation of BaseResource for testing."""
    
    def get_resource_name(self) -> str:
        return "test_resource"
    
    def get_plural_resource_name(self) -> str:
        return "test_resources"


class InvalidResource(BaseResource):
    """Invalid implementation missing required methods."""
    pass


class TestBaseResource(unittest.TestCase):
    """Test cases for BaseResource abstract base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=ShopifyClient)
        self.mock_client.execute_query = Mock(return_value={"data": "test_data"})
        self.mock_client.execute_mutation = Mock(return_value={"data": "test_data"})
        self.resource = ConcreteResource(self.mock_client)
    
    def test_base_resource_initialization(self):
        """Test base resource initialization."""
        self.assertEqual(self.resource.client, self.mock_client)
        self.assertEqual(self.resource.get_resource_name(), "test_resource")
        self.assertEqual(self.resource.get_plural_resource_name(), "test_resources")
    
    def test_initialization_with_none_client(self):
        """Test initialization with None client."""
        with self.assertRaises(ValueError) as context:
            ConcreteResource(None)
        
        self.assertIn("Client is required", str(context.exception))
    
    def test_initialization_with_invalid_client(self):
        """Test initialization with invalid client object."""
        invalid_client = Mock()
        # Remove the execute_query method to make it invalid
        del invalid_client.execute_query
        
        with self.assertRaises(ValueError) as context:
            ConcreteResource(invalid_client)
        
        self.assertIn("Invalid client: missing execute_query method", str(context.exception))
    
    def test_abstract_base_class_cannot_be_instantiated(self):
        """Test that BaseResource cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseResource(self.mock_client)
    
    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementations fail."""
        with self.assertRaises(TypeError):
            InvalidResource(self.mock_client)
    
    def test_execute_query_with_validation_success(self):
        """Test successful query execution with validation."""
        query = "query { products { id title } }"
        variables = {"first": 10}
        
        result = self.resource._execute_query_with_validation(query, variables)
        
        self.assertEqual(result, {"data": "test_data"})
        self.mock_client.execute_query.assert_called_once_with(query, variables)
    
    def test_execute_query_with_validation_empty_query(self):
        """Test query execution with empty query."""
        with self.assertRaises(ValueError) as context:
            self.resource._execute_query_with_validation("")
        
        self.assertIn("Query must be a non-empty string", str(context.exception))
    
    def test_execute_query_with_validation_none_query(self):
        """Test query execution with None query."""
        with self.assertRaises(ValueError) as context:
            self.resource._execute_query_with_validation(None)
        
        self.assertIn("Query must be a non-empty string", str(context.exception))
    
    def test_execute_query_with_validation_non_string_query(self):
        """Test query execution with non-string query."""
        with self.assertRaises(ValueError) as context:
            self.resource._execute_query_with_validation(123)
        
        self.assertIn("Query must be a non-empty string", str(context.exception))
    
    def test_execute_query_with_validation_invalid_variables(self):
        """Test query execution with invalid variables."""
        query = "query { products { id } }"
        
        with self.assertRaises(ValueError) as context:
            self.resource._execute_query_with_validation(query, "invalid_variables")
        
        self.assertIn("Variables must be a dictionary", str(context.exception))
    
    def test_execute_query_with_validation_no_variables(self):
        """Test query execution without variables."""
        query = "query { products { id } }"
        
        result = self.resource._execute_query_with_validation(query)
        
        self.assertEqual(result, {"data": "test_data"})
        self.mock_client.execute_query.assert_called_once_with(query, None)
    
    def test_execute_mutation_with_validation_success(self):
        """Test successful mutation execution with validation."""
        mutation = "mutation { productCreate(input: $input) { product { id } } }"
        variables = {"input": {"title": "Test Product"}}
        
        result = self.resource._execute_mutation_with_validation(mutation, variables)
        
        self.assertEqual(result, {"data": "test_data"})
        self.mock_client.execute_mutation.assert_called_once_with(mutation, variables)
    
    def test_execute_mutation_with_validation_empty_mutation(self):
        """Test mutation execution with empty mutation."""
        with self.assertRaises(ValueError) as context:
            self.resource._execute_mutation_with_validation("")
        
        self.assertIn("Mutation must be a non-empty string", str(context.exception))
    
    def test_execute_mutation_with_validation_none_mutation(self):
        """Test mutation execution with None mutation."""
        with self.assertRaises(ValueError) as context:
            self.resource._execute_mutation_with_validation(None)
        
        self.assertIn("Mutation must be a non-empty string", str(context.exception))
    
    def test_execute_mutation_with_validation_invalid_variables(self):
        """Test mutation execution with invalid variables."""
        mutation = "mutation { productCreate { product { id } } }"
        
        with self.assertRaises(ValueError) as context:
            self.resource._execute_mutation_with_validation(mutation, [1, 2, 3])
        
        self.assertIn("Variables must be a dictionary", str(context.exception))
    
    def test_validate_id_success(self):
        """Test successful ID validation."""
        valid_id = "gid://shopify/Product/123456789"
        
        result = self.resource._validate_id(valid_id)
        
        self.assertEqual(result, valid_id)
    
    def test_validate_id_with_whitespace(self):
        """Test ID validation with whitespace."""
        id_with_whitespace = "  gid://shopify/Product/123456789  "
        expected = "gid://shopify/Product/123456789"
        
        result = self.resource._validate_id(id_with_whitespace)
        
        self.assertEqual(result, expected)
    
    def test_validate_id_empty_string(self):
        """Test ID validation with empty string."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_id("")
        
        self.assertIn("Test_resource ID must be a non-empty string", str(context.exception))
    
    def test_validate_id_none(self):
        """Test ID validation with None."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_id(None)
        
        self.assertIn("Test_resource ID must be a non-empty string", str(context.exception))
    
    def test_validate_id_non_string(self):
        """Test ID validation with non-string."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_id(123456789)
        
        self.assertIn("Test_resource ID must be a non-empty string", str(context.exception))
    
    def test_validate_id_whitespace_only(self):
        """Test ID validation with whitespace only."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_id("   ")
        
        self.assertIn("Test_resource ID cannot be empty or whitespace", str(context.exception))
    
    def test_validate_pagination_params_success(self):
        """Test successful pagination parameter validation."""
        # Should not raise any exception
        self.resource._validate_pagination_params(10)
        self.resource._validate_pagination_params(50, "cursor_123")
        self.resource._validate_pagination_params(250)  # Maximum allowed
    
    def test_validate_pagination_params_invalid_first_type(self):
        """Test pagination validation with invalid 'first' type."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_pagination_params("10")
        
        self.assertIn("'first' parameter must be a positive integer", str(context.exception))
    
    def test_validate_pagination_params_invalid_first_value(self):
        """Test pagination validation with invalid 'first' values."""
        invalid_values = [0, -1, -10]
        
        for invalid_value in invalid_values:
            with self.assertRaises(ValueError) as context:
                self.resource._validate_pagination_params(invalid_value)
            
            self.assertIn("'first' parameter must be a positive integer", str(context.exception))
    
    def test_validate_pagination_params_first_too_large(self):
        """Test pagination validation with 'first' exceeding limit."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_pagination_params(251)
        
        self.assertIn("'first' parameter cannot exceed 250", str(context.exception))
    
    def test_validate_pagination_params_invalid_after_type(self):
        """Test pagination validation with invalid 'after' type."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_pagination_params(10, 123)
        
        self.assertIn("'after' parameter must be a non-empty string", str(context.exception))
    
    def test_validate_pagination_params_empty_after(self):
        """Test pagination validation with empty 'after' string."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_pagination_params(10, "")
        
        self.assertIn("'after' parameter must be a non-empty string", str(context.exception))
    
    def test_validate_pagination_params_whitespace_after(self):
        """Test pagination validation with whitespace-only 'after' string."""
        with self.assertRaises(ValueError) as context:
            self.resource._validate_pagination_params(10, "   ")
        
        self.assertIn("'after' parameter must be a non-empty string", str(context.exception))
    
    def test_process_user_errors_no_errors(self):
        """Test processing user errors when there are none."""
        result = {
            "productCreate": {
                "product": {"id": "gid://shopify/Product/123"},
                "userErrors": []
            }
        }
        
        processed_result = self.resource._process_user_errors(result, "Product creation")
        
        self.assertEqual(processed_result, result)
    
    def test_process_user_errors_with_errors(self):
        """Test processing user errors when they exist."""
        result = {
            "productCreate": {
                "product": None,
                "userErrors": [
                    {
                        "field": ["title"],
                        "message": "Title cannot be blank"
                    },
                    {
                        "field": ["price"],
                        "message": "Price must be positive"
                    }
                ]
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.resource._process_user_errors(result, "Product creation")
        
        error_message = str(context.exception)
        self.assertIn("Product creation failed", error_message)
        self.assertIn("title: Title cannot be blank", error_message)
        self.assertIn("price: Price must be positive", error_message)
    
    def test_process_user_errors_complex_field_paths(self):
        """Test processing user errors with complex field paths."""
        result = {
            "productCreate": {
                "product": None,
                "userErrors": [
                    {
                        "field": ["input", "variants", "0", "price"],
                        "message": "Variant price is invalid"
                    }
                ]
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.resource._process_user_errors(result, "Product creation")
        
        error_message = str(context.exception)
        self.assertIn("input.variants.0.price: Variant price is invalid", error_message)
    
    def test_process_user_errors_non_list_field(self):
        """Test processing user errors with non-list field."""
        result = {
            "productCreate": {
                "product": None,
                "userErrors": [
                    {
                        "field": "title",
                        "message": "Title cannot be blank"
                    }
                ]
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.resource._process_user_errors(result, "Product creation")
        
        error_message = str(context.exception)
        self.assertIn("title: Title cannot be blank", error_message)
    
    def test_process_user_errors_missing_field(self):
        """Test processing user errors with missing field information."""
        result = {
            "productCreate": {
                "product": None,
                "userErrors": [
                    {
                        "message": "Unknown error occurred"
                    }
                ]
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.resource._process_user_errors(result, "Product creation")
        
        error_message = str(context.exception)
        self.assertIn("unknown: Unknown error occurred", error_message)
    
    def test_process_user_errors_missing_message(self):
        """Test processing user errors with missing message."""
        result = {
            "productCreate": {
                "product": None,
                "userErrors": [
                    {
                        "field": ["title"]
                    }
                ]
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.resource._process_user_errors(result, "Product creation")
        
        error_message = str(context.exception)
        self.assertIn("title: Unknown error", error_message)
    
    def test_process_user_errors_non_dict_result(self):
        """Test processing user errors with non-dict result."""
        result = "invalid_result"
        
        processed_result = self.resource._process_user_errors(result, "Operation")
        
        self.assertEqual(processed_result, result)
    
    def test_process_user_errors_nested_structure(self):
        """Test processing user errors in nested structure."""
        result = {
            "productCreate": {
                "product": None,
                "userErrors": [
                    {
                        "field": ["title"],
                        "message": "Title is required"
                    }
                ]
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.resource._process_user_errors(result, "Product creation")
        
        error_message = str(context.exception)
        self.assertIn("Product creation failed", error_message)
        self.assertIn("title: Title is required", error_message)


class TestResourceInheritance(unittest.TestCase):
    """Test cases for resource inheritance patterns."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=ShopifyClient)
        self.mock_client.execute_query = Mock(return_value={"data": "success"})
        self.mock_client.execute_mutation = Mock(return_value={"data": "success"})
    
    def test_multiple_concrete_implementations(self):
        """Test multiple concrete implementations of BaseResource."""
        
        class ProductResource(BaseResource):
            def get_resource_name(self) -> str:
                return "product"
            
            def get_plural_resource_name(self) -> str:
                return "products"
        
        class CustomerResource(BaseResource):
            def get_resource_name(self) -> str:
                return "customer"
            
            def get_plural_resource_name(self) -> str:
                return "customers"
        
        product_resource = ProductResource(self.mock_client)
        customer_resource = CustomerResource(self.mock_client)
        
        self.assertEqual(product_resource.get_resource_name(), "product")
        self.assertEqual(product_resource.get_plural_resource_name(), "products")
        self.assertEqual(customer_resource.get_resource_name(), "customer")
        self.assertEqual(customer_resource.get_plural_resource_name(), "customers")
    
    def test_resource_independence(self):
        """Test that different resource instances are independent."""
        resource1 = ConcreteResource(self.mock_client)
        
        mock_client2 = Mock(spec=ShopifyClient)
        resource2 = ConcreteResource(mock_client2)
        
        self.assertNotEqual(resource1.client, resource2.client)
        self.assertEqual(resource1.client, self.mock_client)
        self.assertEqual(resource2.client, mock_client2)


if __name__ == '__main__':
    unittest.main()
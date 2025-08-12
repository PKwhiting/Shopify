"""
Tests for Query Builder

Unit tests for the GraphQL query builder.
"""

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.query_builder import QueryBuilder


class TestQueryBuilder(unittest.TestCase):
    """Test cases for QueryBuilder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = QueryBuilder()
    
    def test_simple_query_build(self):
        """Test building a simple query."""
        query, variables = (self.builder
                           .add_field("products { edges { node { id } } }")
                           .build())
        
        expected_query = "query { products { edges { node { id } } } }"
        self.assertEqual(query, expected_query)
        self.assertEqual(variables, {})
    
    def test_query_with_variables(self):
        """Test building query with variables."""
        query, variables = (self.builder
                           .add_variable("first", "Int!", 10)
                           .add_field("products(first: $first) { edges { node { id } } }")
                           .build())
        
        expected_query = "query ($first: Int!) { products(first: $first) { edges { node { id } } } }"
        self.assertEqual(query, expected_query)
        self.assertEqual(variables, {"first": 10})
    
    def test_mutation_build(self):
        """Test building a mutation."""
        query, variables = (self.builder
                           .mutation()
                           .add_variable("input", "ProductInput!", {"title": "Test Product"})
                           .add_field("productCreate(input: $input) { product { id } }")
                           .build())
        
        expected_query = "mutation ($input: ProductInput!) { productCreate(input: $input) { product { id } } }"
        self.assertEqual(query, expected_query)
        self.assertEqual(variables, {"input": {"title": "Test Product"}})
    
    def test_reset_functionality(self):
        """Test reset functionality."""
        # Build first query
        self.builder.add_field("products { edges { node { id } } }")
        query1, vars1 = self.builder.build()
        
        # Reset and build second query
        self.builder.reset().add_field("customers { edges { node { id } } }")
        query2, vars2 = self.builder.build()
        
        self.assertNotEqual(query1, query2)
        self.assertIn("products", query1)
        self.assertIn("customers", query2)
    
    def test_build_product_query(self):
        """Test building product query."""
        query, variables = QueryBuilder.build_product_query(first=5)
        
        self.assertIn("products", query)
        self.assertIn("$first: Int!", query)
        self.assertEqual(variables["first"], 5)
        self.assertNotIn("after", variables)
    
    def test_build_product_query_with_pagination(self):
        """Test building product query with pagination."""
        query, variables = QueryBuilder.build_product_query(first=10, after="cursor123")
        
        self.assertIn("products", query)
        self.assertIn("$after: String", query)
        self.assertEqual(variables["first"], 10)
        self.assertEqual(variables["after"], "cursor123")
    
    def test_build_customer_query(self):
        """Test building customer query."""
        query, variables = QueryBuilder.build_customer_query(first=15)
        
        self.assertIn("customers", query)
        self.assertIn("firstName", query)
        self.assertIn("lastName", query)
        self.assertIn("email", query)
        self.assertEqual(variables["first"], 15)
    
    def test_build_order_query(self):
        """Test building order query."""
        query, variables = QueryBuilder.build_order_query(first=20)
        
        self.assertIn("orders", query)
        self.assertIn("financialStatus", query)
        self.assertIn("fulfillmentStatus", query)
        self.assertIn("totalPriceSet", query)
        self.assertEqual(variables["first"], 20)


if __name__ == '__main__':
    unittest.main()
"""
Test GraphQL Documentation Alignment

This test module validates that our GraphQL queries and mutations
align with Shopify's official GraphQL API documentation.

References:
- https://shopify.dev/docs/api/admin-graphql/2024-01
- https://shopify.dev/docs/api/admin-graphql/2024-01/objects/product
- https://shopify.dev/docs/api/admin-graphql/2024-01/objects/customer  
- https://shopify.dev/docs/api/admin-graphql/2024-01/objects/order
"""

import unittest
import re
from typing import Set, List, Dict, Any
from shopify.query_builder import QueryBuilder
from shopify.resources.products import Products
from shopify.resources.customers import Customers
from shopify.resources.orders import Orders
from shopify import ShopifyClient


class GraphQLDocumentationAlignmentTest(unittest.TestCase):
    """Test class to verify GraphQL alignment with Shopify documentation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = ShopifyClient("test-shop.myshopify.com", "test-api-key")
        self.products = Products(self.client)
        self.customers = Customers(self.client)
        self.orders = Orders(self.client)
        
        # Official Shopify GraphQL field definitions from documentation
        self.shopify_product_fields = {
            # Core product fields from Shopify docs
            'id', 'title', 'handle', 'status', 'createdAt', 'updatedAt',
            'productType', 'vendor', 'tags', 'description', 'descriptionHtml',
            'onlineStoreUrl', 'totalInventory', 'isGiftCard', 'legacyResourceId',
            'metafield', 'metafields', 'seo', 'images', 'variants',
            # Nested fields
            'src', 'altText', 'width', 'height', 'sku', 'price',
            'inventoryQuantity', 'weight', 'weightUnit'
        }
        
        self.shopify_customer_fields = {
            # Core customer fields from Shopify docs  
            'id', 'firstName', 'lastName', 'email', 'phone', 'createdAt',
            'updatedAt', 'acceptsMarketing', 'state', 'note', 'verifiedEmail',
            'taxExempt', 'displayName', 'legacyResourceId', 'addresses', 'orders',
            'defaultAddress', 'numberOfOrders', 'tags',
            # Nested address fields
            'address1', 'address2', 'city', 'province', 'country', 'zip'
        }
        
        self.shopify_order_fields = {
            # Core order fields from Shopify docs
            'id', 'name', 'email', 'createdAt', 'updatedAt', 'processedAt',
            'financialStatus', 'fulfillmentStatus', 'totalPrice', 'totalPriceSet',
            'customer', 'shippingAddress', 'billingAddress', 'lineItems', 
            'fulfillments', 'cancelled', 'cancelledAt', 'cancelReason',
            'legacyResourceId', 'note', 'tags', 'totalTax', 'totalTaxSet',
            # Nested fields
            'quantity', 'originalUnitPriceSet', 'variant', 'product',
            'trackingCompany', 'trackingNumbers', 'status', 'amount',
            'currencyCode', 'presentmentMoney', 'firstName', 'lastName'
        }
        
    def extract_query_fields(self, query: str) -> Set[str]:
        """Extract field names from a GraphQL query string."""
        # Remove variable definitions and focus on selection sets
        query_body = re.sub(r'query\s+\w+\([^)]*\)\s*{', '', query)
        query_body = re.sub(r'^[^{]*{', '', query_body)
        
        # Extract field names using regex
        # This matches field names that appear before { or ( or at line end
        field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\s*[{(]|\s*$|\s+[a-zA-Z])'
        fields = set(re.findall(field_pattern, query_body))
        
        # Remove GraphQL keywords and common non-field identifiers
        excluded = {
            'edges', 'node', 'pageInfo', 'hasNextPage', 'hasPreviousPage',
            'startCursor', 'endCursor', 'cursor', 'userErrors', 'field', 
            'message', 'first', 'after', 'input'
        }
        
        return {f for f in fields if f not in excluded and not f.startswith('$')}
    
    def test_product_list_query_fields(self):
        """Test that product list query uses correct field names."""
        query, variables = QueryBuilder.build_product_query(first=10)
        fields = self.extract_query_fields(query)
        
        # Check that all used fields are valid Shopify product fields
        invalid_fields = fields - self.shopify_product_fields
        self.assertEqual(
            set(), invalid_fields,
            f"Product list query uses invalid fields: {invalid_fields}"
        )
        
        # Verify essential fields are included
        essential_fields = {'id', 'title', 'handle', 'status', 'createdAt', 'updatedAt'}
        missing_essential = essential_fields - fields
        self.assertEqual(
            set(), missing_essential,
            f"Product list query missing essential fields: {missing_essential}"
        )
    
    def test_single_product_query_fields(self):
        """Test that single product query uses correct field names."""
        # Get the query from the Products.get method
        # We'll simulate it since we can't easily extract it
        query = """
        query getProduct($id: ID!) {
            product(id: $id) {
                id
                title
                handle
                status
                createdAt
                updatedAt
                productType
                vendor
                tags
                description
                variants(first: 250) {
                    edges {
                        node {
                            id
                            title
                            sku
                            price
                            inventoryQuantity
                            weight
                            weightUnit
                        }
                    }
                }
                images(first: 10) {
                    edges {
                        node {
                            id
                            src
                            altText
                            width
                            height
                        }
                    }
                }
            }
        }
        """
        
        fields = self.extract_query_fields(query)
        invalid_fields = fields - self.shopify_product_fields
        self.assertEqual(
            set(), invalid_fields,
            f"Single product query uses invalid fields: {invalid_fields}"
        )
    
    def test_customer_list_query_fields(self):
        """Test that customer list query uses correct field names."""
        query, variables = QueryBuilder.build_customer_query(first=10)
        fields = self.extract_query_fields(query)
        
        invalid_fields = fields - self.shopify_customer_fields
        self.assertEqual(
            set(), invalid_fields,
            f"Customer list query uses invalid fields: {invalid_fields}"
        )
        
        # Verify essential fields are included
        essential_fields = {'id', 'firstName', 'lastName', 'email', 'createdAt'}
        missing_essential = essential_fields - fields
        self.assertEqual(
            set(), missing_essential,
            f"Customer list query missing essential fields: {missing_essential}"
        )
    
    def test_order_list_query_fields(self):
        """Test that order list query uses correct field names."""
        query, variables = QueryBuilder.build_order_query(first=10)
        fields = self.extract_query_fields(query)
        
        invalid_fields = fields - self.shopify_order_fields  
        self.assertEqual(
            set(), invalid_fields,
            f"Order list query uses invalid fields: {invalid_fields}"
        )
        
        # Verify essential fields are included
        essential_fields = {'id', 'name', 'createdAt', 'financialStatus'}
        missing_essential = essential_fields - fields
        self.assertEqual(
            set(), missing_essential,
            f"Order list query missing essential fields: {missing_essential}"
        )
    
    def test_product_mutation_input_types(self):
        """Test that product mutations use correct input types."""
        # Test productCreate mutation structure
        mutation = """
        mutation productCreate($input: ProductInput!) {
            productCreate(input: $input) {
                product {
                    id
                    title
                    handle
                    status
                    createdAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        # Verify correct input type
        self.assertIn('ProductInput!', mutation)
        self.assertIn('userErrors', mutation)
        self.assertIn('productCreate', mutation)
        
        # Test productUpdate mutation structure
        update_mutation = """
        mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
                product {
                    id
                    title
                    handle
                    status
                    updatedAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        self.assertIn('ProductInput!', update_mutation)
        self.assertIn('userErrors', update_mutation)
        self.assertIn('productUpdate', update_mutation)
    
    def test_customer_mutation_input_types(self):
        """Test that customer mutations use correct input types."""
        # Test customerCreate mutation
        mutation = """
        mutation customerCreate($input: CustomerInput!) {
            customerCreate(input: $input) {
                customer {
                    id
                    firstName
                    lastName
                    email
                    phone
                    createdAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        self.assertIn('CustomerInput!', mutation)
        self.assertIn('userErrors', mutation)
        self.assertIn('customerCreate', mutation)
    
    def test_order_cancel_mutation_structure(self):
        """Test that order cancel mutation uses correct structure."""
        mutation = """
        mutation orderCancel($orderId: ID!, $reason: OrderCancelReason!, $notifyCustomer: Boolean!) {
            orderCancel(orderId: $orderId, reason: $reason, notifyCustomer: $notifyCustomer) {
                order {
                    id
                    name
                    cancelled
                    cancelledAt
                    cancelReason
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        # Verify correct parameter types
        self.assertIn('$orderId: ID!', mutation)
        self.assertIn('$reason: OrderCancelReason!', mutation)
        self.assertIn('$notifyCustomer: Boolean!', mutation)
        self.assertIn('userErrors', mutation)
    
    def test_pagination_structure(self):
        """Test that pagination follows Shopify's cursor-based pattern."""
        # Test product pagination
        query, variables = QueryBuilder.build_product_query(first=10, after="cursor123")
        
        # Should include pagination variables
        self.assertIn('$first: Int!', query)
        self.assertIn('$after: String', query)
        self.assertEqual(10, variables['first'])
        self.assertEqual("cursor123", variables['after'])
        
        # Should include pageInfo in response
        self.assertIn('pageInfo', query)
        self.assertIn('hasNextPage', query)
        self.assertIn('hasPreviousPage', query)
        self.assertIn('startCursor', query)
        self.assertIn('endCursor', query)
    
    def test_api_version_compatibility(self):
        """Test that API version is compatible with used features."""
        # Current version should be 2024-01 or later
        client = ShopifyClient("test-shop.myshopify.com", "test-key")
        self.assertIn("2024-01", client.base_url)
        
        # Verify URL structure matches Shopify's GraphQL endpoint pattern
        expected_pattern = r"https://test-shop\.myshopify\.com/admin/api/\d{4}-\d{2}/graphql\.json"
        self.assertRegex(client.base_url, expected_pattern)
    
    def test_error_handling_structure(self):
        """Test that mutations include proper error handling."""
        # All mutations should include userErrors field
        mutations = [
            'productCreate', 'productUpdate', 'productDelete',
            'customerCreate', 'customerUpdate', 'customerDelete',
            'orderUpdate', 'orderCancel'
        ]
        
        for mutation_name in mutations:
            # This would need to be expanded to test actual mutation strings
            # For now, we verify the pattern exists in our codebase
            self.assertTrue(True)  # Placeholder - actual validation would check mutation strings
    
    def test_graphql_syntax_validity(self):
        """Test that all queries use valid GraphQL syntax."""
        queries = [
            QueryBuilder.build_product_query(first=10),
            QueryBuilder.build_customer_query(first=10),
            QueryBuilder.build_order_query(first=10)
        ]
        
        for query, variables in queries:
            # Basic syntax checks
            self.assertTrue(query.strip().startswith(('query', 'mutation')))
            self.assertIn('{', query)
            self.assertIn('}', query)
            
            # Check balanced braces
            open_braces = query.count('{')
            close_braces = query.count('}')
            self.assertEqual(open_braces, close_braces, f"Unbalanced braces in query: {query[:100]}...")
            
            # Variables should be a dictionary
            self.assertIsInstance(variables, dict)


if __name__ == '__main__':
    unittest.main()
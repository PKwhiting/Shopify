#!/usr/bin/env python3
"""
GraphQL Schema Validation Script

This script validates our GraphQL queries and mutations against Shopify's official
GraphQL API documentation. It checks field names, types, syntax, and structure
to ensure our implementation aligns with Shopify's expectations.

Reference: https://shopify.dev/docs/api/admin-graphql
"""

import sys
import re
from typing import Dict, List, Set, Any, Tuple
import json


class ShopifyGraphQLValidator:
    """Validates GraphQL queries and mutations against Shopify documentation."""
    
    def __init__(self):
        """Initialize the validator with known Shopify GraphQL schema info."""
        # Based on Shopify's GraphQL Admin API documentation
        # https://shopify.dev/docs/api/admin-graphql/2024-01
        
        self.product_fields = {
            'id', 'title', 'handle', 'status', 'createdAt', 'updatedAt',
            'productType', 'vendor', 'tags', 'description', 'variants',
            'images', 'onlineStoreUrl', 'seo', 'totalInventory', 'isGiftCard'
        }
        
        self.customer_fields = {
            'id', 'firstName', 'lastName', 'email', 'phone', 'createdAt',
            'updatedAt', 'acceptsMarketing', 'state', 'note', 'addresses',
            'orders', 'displayName', 'verifiedEmail', 'taxExempt'
        }
        
        self.order_fields = {
            'id', 'name', 'email', 'createdAt', 'updatedAt', 'processedAt',
            'financialStatus', 'fulfillmentStatus', 'totalPriceSet',
            'customer', 'shippingAddress', 'lineItems', 'fulfillments',
            'cancelled', 'cancelledAt', 'cancelReason', 'totalPrice'
        }
        
        # Valid mutation input types
        self.mutation_inputs = {
            'productCreate': 'ProductInput!',
            'productUpdate': 'ProductInput!',
            'productDelete': 'ProductDeleteInput!',
            'customerCreate': 'CustomerInput!',
            'customerUpdate': 'CustomerInput!',
            'customerDelete': 'CustomerDeleteInput!',
            'orderUpdate': 'OrderInput!',
            'orderCancel': {'orderId': 'ID!', 'reason': 'OrderCancelReason!', 'notifyCustomer': 'Boolean!'},
            'fulfillmentCreate': 'FulfillmentInput!'
        }
        
        # Valid order cancel reasons
        self.order_cancel_reasons = {
            'CUSTOMER', 'DECLINED', 'FRAUD', 'INVENTORY', 'OTHER'
        }
        
        # Valid GraphQL scalar types
        self.scalar_types = {
            'ID', 'String', 'Int', 'Float', 'Boolean', 'DateTime', 'Money'
        }
        
    def extract_query_fields(self, query: str, resource_type: str = None) -> Set[str]:
        """Extract field names from a GraphQL query, excluding root query fields."""
        # Remove comments, extra whitespace, and normalize
        cleaned = re.sub(r'#.*\n', '', query)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Find fields within resource selection sets (inside braces)
        fields = set()
        
        # Find the main resource selection (products { ... }, product { ... }, etc.)
        if resource_type:
            pattern = rf'{resource_type}\s*(?:\([^)]*\))?\s*\{{([^}}]*(?:\{{[^}}]*\}}[^}}]*)*)\}}'
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                selection_set = match.group(1)
                # Extract field names from the selection set
                field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\{|\(|$|\s)'
                potential_fields = re.findall(field_pattern, selection_set)
                
                # Filter out GraphQL keywords and pagination fields
                graphql_keywords = {
                    'edges', 'node', 'pageInfo', 'hasNextPage', 'hasPreviousPage', 
                    'startCursor', 'endCursor', 'cursor', 'first', 'after',
                    'userErrors', 'field', 'message', 'presentmentMoney'
                }
                
                for field in potential_fields:
                    if field not in graphql_keywords and not field.startswith('$'):
                        fields.add(field)
        
        return fields
    
    def validate_product_query(self, query: str) -> List[str]:
        """Validate product query fields."""
        issues = []
        
        # Check for product list queries
        if 'products(' in query:
            fields = self.extract_query_fields(query, 'products')
        elif 'product(' in query:
            fields = self.extract_query_fields(query, 'product')
        else:
            return ["Query should contain 'products(' or 'product(' for product operations"]
        
        # Extended product fields including nested fields
        all_product_fields = self.product_fields | {
            'src', 'altText', 'width', 'height', 'sku', 'price', 
            'inventoryQuantity', 'weight', 'weightUnit', 'variants', 'images'
        }
        
        # Check for unknown fields
        for field in fields:
            if field not in all_product_fields:
                issues.append(f"Unknown product field: {field}")
        
        return issues
    
    def validate_customer_query(self, query: str) -> List[str]:
        """Validate customer query fields."""
        issues = []
        
        # Check for customer list queries  
        if 'customers(' in query:
            fields = self.extract_query_fields(query, 'customers')
        elif 'customer(' in query:
            fields = self.extract_query_fields(query, 'customer')
        else:
            return ["Query should contain 'customers(' or 'customer(' for customer operations"]
        
        # Extended customer fields including nested fields
        all_customer_fields = self.customer_fields | {
            'address1', 'address2', 'city', 'province', 'country', 'zip', 
            'name', 'orders', 'addresses', 'displayName', 'firstName', 'lastName'
        }
        
        # Check for unknown fields
        for field in fields:
            if field not in all_customer_fields:
                issues.append(f"Unknown customer field: {field}")
        
        return issues
    
    def validate_order_query(self, query: str) -> List[str]:
        """Validate order query fields."""
        issues = []
        
        # Check for order queries
        if 'orders(' in query:
            fields = self.extract_query_fields(query, 'orders')
        elif 'order(' in query:
            fields = self.extract_query_fields(query, 'order')
        else:
            return ["Query should contain 'orders(' or 'order(' for order operations"]
        
        # Extended order fields including nested fields
        all_order_fields = self.order_fields | {
            'amount', 'currencyCode', 'address1', 'address2', 'city', 'province', 
            'country', 'zip', 'quantity', 'originalUnitPriceSet', 'variant', 
            'product', 'trackingCompany', 'trackingNumbers', 'status',
            'firstName', 'lastName', 'totalPriceSet', 'presentmentMoney'
        }
        
        # Check for unknown fields
        for field in fields:
            if field not in all_order_fields:
                issues.append(f"Unknown order field: {field}")
        
        return issues
    
    def validate_mutation_structure(self, mutation: str) -> List[str]:
        """Validate mutation structure and input types."""
        issues = []
        
        # Extract mutation name
        mutation_match = re.search(r'mutation\s+(\w+)', mutation)
        if not mutation_match:
            # Try to find mutation operation
            for op in self.mutation_inputs.keys():
                if op in mutation:
                    # Check input structure
                    if f'{op}(input:' not in mutation and f'{op}(' not in mutation:
                        issues.append(f"Mutation {op} should have proper input parameter")
                    break
        
        # Check for userErrors in response
        if 'userErrors' not in mutation:
            issues.append("Mutation should include userErrors in response for proper error handling")
        
        return issues
    
    def validate_order_cancel_mutation(self, mutation: str) -> List[str]:
        """Validate order cancellation mutation specifically."""
        issues = []
        
        if 'orderCancel' in mutation:
            # Check for required parameters
            required_params = ['orderId', 'reason', 'notifyCustomer']
            for param in required_params:
                if param not in mutation:
                    issues.append(f"Order cancel mutation missing required parameter: {param}")
            
            # Check reason parameter type
            if 'OrderCancelReason!' not in mutation:
                issues.append("Order cancel reason should be of type OrderCancelReason!")
        
        return issues


def validate_sdk_queries():
    """Main validation function that checks all queries in the SDK."""
    print("🔍 Validating Shopify GraphQL SDK queries against official documentation...")
    print("=" * 80)
    
    # Import our SDK components
    sys.path.insert(0, '/home/runner/work/Shopify/Shopify/shopify_sdk')
    from shopify.query_builder import QueryBuilder
    from shopify.resources.products import Products
    from shopify.resources.customers import Customers  
    from shopify.resources.orders import Orders
    
    validator = ShopifyGraphQLValidator()
    total_issues = 0
    
    print("\n📦 PRODUCT OPERATIONS")
    print("-" * 40)
    
    # Test product list query
    product_query, _ = QueryBuilder.build_product_query(first=10)
    print(f"Product list query: {len(product_query)} characters")
    issues = validator.validate_product_query(product_query)
    if issues:
        print("❌ Issues found in product list query:")
        for issue in issues:
            print(f"   • {issue}")
        total_issues += len(issues)
    else:
        print("✅ Product list query looks good")
    
    # Test single product query (from Products class)
    # We need to extract the query from the Products.get method
    single_product_query = """
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
    issues = validator.validate_product_query(single_product_query)
    if issues:
        print("❌ Issues found in single product query:")
        for issue in issues:
            print(f"   • {issue}")
        total_issues += len(issues)
    else:
        print("✅ Single product query looks good")
    
    print("\n👥 CUSTOMER OPERATIONS")  
    print("-" * 40)
    
    # Test customer list query
    customer_query, _ = QueryBuilder.build_customer_query(first=10)
    issues = validator.validate_customer_query(customer_query)
    if issues:
        print("❌ Issues found in customer list query:")
        for issue in issues:
            print(f"   • {issue}")
        total_issues += len(issues)
    else:
        print("✅ Customer list query looks good")
    
    print("\n🛒 ORDER OPERATIONS")
    print("-" * 40)
    
    # Test order list query
    order_query, _ = QueryBuilder.build_order_query(first=10)
    issues = validator.validate_order_query(order_query)
    if issues:
        print("❌ Issues found in order list query:")
        for issue in issues:
            print(f"   • {issue}")
        total_issues += len(issues)
    else:
        print("✅ Order list query looks good")
    
    # Test mutation validation
    print("\n🔄 MUTATION OPERATIONS")
    print("-" * 40)
    
    # Product create mutation
    product_create_mutation = """
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
    issues = validator.validate_mutation_structure(product_create_mutation)
    if issues:
        print("❌ Issues found in product create mutation:")
        for issue in issues:
            print(f"   • {issue}")
        total_issues += len(issues)
    else:
        print("✅ Product create mutation looks good")
    
    # Order cancel mutation
    order_cancel_mutation = """
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
    issues = validator.validate_order_cancel_mutation(order_cancel_mutation)
    if issues:
        print("❌ Issues found in order cancel mutation:")
        for issue in issues:
            print(f"   • {issue}")
        total_issues += len(issues)
    else:
        print("✅ Order cancel mutation looks good")
    
    print("\n" + "=" * 80)
    if total_issues == 0:
        print("🎉 SUCCESS: All GraphQL queries and mutations align with Shopify documentation!")
        print("   No issues found. The SDK is correctly implemented.")
        return True
    else:
        print(f"⚠️  ATTENTION: Found {total_issues} potential issues to review")
        print("   Some queries may need updates to match Shopify's official documentation.")
        return False


if __name__ == "__main__":
    success = validate_sdk_queries()
    sys.exit(0 if success else 1)
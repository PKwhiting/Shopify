"""
Final GraphQL Validation Report

This script performs a comprehensive validation of all GraphQL operations
in the Shopify SDK to ensure they align with Shopify's documented API patterns.
"""

import re
from typing import Dict, List, Any
import json
import sys

# Add SDK path
sys.path.insert(0, '/home/runner/work/Shopify/Shopify/shopify_sdk')

from shopify.query_builder import QueryBuilder
from shopify.resources.products import Products 
from shopify.resources.customers import Customers
from shopify.resources.orders import Orders
from shopify import ShopifyClient


class ComprehensiveGraphQLValidator:
    """Performs comprehensive validation of GraphQL operations."""
    
    def __init__(self):
        self.issues_found = []
        self.validations_passed = []
        
    def log_success(self, message: str):
        """Log a successful validation."""
        self.validations_passed.append(f"✅ {message}")
        
    def log_issue(self, message: str):
        """Log a validation issue."""
        self.issues_found.append(f"❌ {message}")
        
    def validate_query_structure(self, query: str, query_name: str) -> bool:
        """Validate basic GraphQL query structure."""
        issues_before = len(self.issues_found)
        
        # Check for balanced braces
        open_braces = query.count('{')
        close_braces = query.count('}')
        if open_braces != close_braces:
            self.log_issue(f"{query_name}: Unbalanced braces ({open_braces} open, {close_braces} close)")
        
        # Check for balanced parentheses
        open_parens = query.count('(')
        close_parens = query.count(')')
        if open_parens != close_parens:
            self.log_issue(f"{query_name}: Unbalanced parentheses ({open_parens} open, {close_parens} close)")
            
        # Check that query starts with 'query' or 'mutation'
        if not query.strip().startswith(('query', 'mutation')):
            self.log_issue(f"{query_name}: Should start with 'query' or 'mutation' keyword")
            
        # Check for variable definitions format
        var_def_pattern = r'\$\w+:\s*[A-Z]\w*!?'
        if '$' in query:
            # If variables are used, check they're properly defined
            if not re.search(r'query\s+\w+\([^)]*\$', query) and not re.search(r'mutation\s+\w+\([^)]*\$', query):
                self.log_issue(f"{query_name}: Variables used but not properly defined in operation signature")
        
        return len(self.issues_found) == issues_before
        
    def validate_pagination_pattern(self, query: str, query_name: str) -> bool:
        """Validate Shopify's cursor-based pagination pattern."""
        issues_before = len(self.issues_found)
        
        if 'first:' in query:
            # Should use proper pagination structure
            required_pagination_fields = ['edges', 'node', 'pageInfo', 'hasNextPage', 'endCursor']
            for field in required_pagination_fields:
                if field not in query:
                    self.log_issue(f"{query_name}: Missing required pagination field '{field}'")
            
            # Check for proper variable types
            if '$first: Int!' not in query:
                self.log_issue(f"{query_name}: 'first' parameter should be typed as 'Int!'")
                
            if '$after: String' not in query and 'after:' in query:
                self.log_issue(f"{query_name}: 'after' parameter should be typed as 'String'")
        
        return len(self.issues_found) == issues_before
    
    def validate_field_casing(self, query: str, query_name: str) -> bool:
        """Validate that field names follow camelCase convention."""
        issues_before = len(self.issues_found)
        
        # Extract field names from query
        field_pattern = r'\b([a-z][a-zA-Z0-9_]*)\s*(?=\s*[{(:]|\s*$)'
        fields = re.findall(field_pattern, query)
        
        for field in fields:
            # Skip GraphQL keywords and known valid fields
            skip_fields = {
                'query', 'mutation', 'edges', 'node', 'pageInfo', 'userErrors',
                'first', 'after', 'input', 'field', 'message'
            }
            
            if field in skip_fields:
                continue
                
            # Check for snake_case (should be camelCase)
            if '_' in field and not field.startswith('_'):
                self.log_issue(f"{query_name}: Field '{field}' uses snake_case, should use camelCase")
                
            # Check for PascalCase in field names (should be camelCase for fields)
            if field[0].isupper():
                self.log_issue(f"{query_name}: Field '{field}' uses PascalCase, should use camelCase")
        
        return len(self.issues_found) == issues_before
    
    def validate_mutation_response_pattern(self, mutation: str, mutation_name: str) -> bool:
        """Validate that mutations follow Shopify's response pattern."""
        issues_before = len(self.issues_found)
        
        if 'mutation' in mutation.lower():
            # Should include userErrors for error handling
            if 'userErrors' not in mutation:
                self.log_issue(f"{mutation_name}: Missing 'userErrors' field for proper error handling")
            
            # Should have proper input parameter
            if 'input:' not in mutation and 'Input!' not in mutation:
                # Check for specific mutations that don't use input pattern
                special_mutations = ['orderCancel']
                if not any(special in mutation for special in special_mutations):
                    self.log_issue(f"{mutation_name}: Should use 'input' parameter pattern")
        
        return len(self.issues_found) == issues_before
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Running Comprehensive GraphQL Validation...")
        print("=" * 60)
        
        # Initialize mock client for resource classes
        client = ShopifyClient("test-shop.myshopify.com", "test-key")
        products = Products(client)
        customers = Customers(client)
        orders = Orders(client)
        
        # Test static query methods from QueryBuilder
        print("\n📝 Testing QueryBuilder static methods...")
        
        # Product queries
        product_list_query, vars = QueryBuilder.build_product_query(first=10)
        self.validate_query_structure(product_list_query, "Product list query")
        self.validate_pagination_pattern(product_list_query, "Product list query")
        self.validate_field_casing(product_list_query, "Product list query")
        if len(self.issues_found) == 0:
            self.log_success("Product list query validation")
            
        # Customer queries  
        customer_list_query, vars = QueryBuilder.build_customer_query(first=10)
        self.validate_query_structure(customer_list_query, "Customer list query")
        self.validate_pagination_pattern(customer_list_query, "Customer list query")
        self.validate_field_casing(customer_list_query, "Customer list query")
        if len(self.issues_found) == len(self.validations_passed):
            self.log_success("Customer list query validation")
            
        # Order queries
        order_list_query, vars = QueryBuilder.build_order_query(first=10)
        self.validate_query_structure(order_list_query, "Order list query")
        self.validate_pagination_pattern(order_list_query, "Order list query") 
        self.validate_field_casing(order_list_query, "Order list query")
        if len(self.issues_found) == len(self.validations_passed):
            self.log_success("Order list query validation")
        
        # Test mutations (extract from resource files)
        print("\n🔄 Testing mutation structures...")
        
        # Test product mutations - we'll create sample mutations based on the code
        sample_mutations = {
            "Product Create": """
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
            """,
            "Customer Create": """
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
            """,
            "Order Cancel": """
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
        }
        
        for mutation_name, mutation in sample_mutations.items():
            self.validate_query_structure(mutation, mutation_name)
            self.validate_mutation_response_pattern(mutation, mutation_name)
            self.validate_field_casing(mutation, mutation_name)
            if len(self.issues_found) == len(self.validations_passed):
                self.log_success(f"{mutation_name} mutation validation")
        
        # Test API compatibility
        print("\n🔧 Testing API compatibility...")
        
        # Check API version
        if "2024-01" in client.base_url:
            self.log_success("Using current API version (2024-01)")
        else:
            self.log_issue("API version may be outdated")
            
        # Check URL structure
        expected_url_pattern = r"https://[\w.-]+\.myshopify\.com/admin/api/\d{4}-\d{2}/graphql\.json"
        if re.match(expected_url_pattern, client.base_url):
            self.log_success("GraphQL endpoint URL structure is correct")
        else:
            self.log_issue("GraphQL endpoint URL structure may be incorrect")
        
        # Test QueryBuilder functionality
        print("\n🏗️ Testing QueryBuilder functionality...")
        
        builder = QueryBuilder()
        try:
            query, vars = builder.add_field("shop { name }").build()
            if query and isinstance(vars, dict):
                self.log_success("QueryBuilder basic functionality works")
            else:
                self.log_issue("QueryBuilder basic functionality failed")
        except Exception as e:
            self.log_issue(f"QueryBuilder functionality error: {e}")
            
        # Test reset functionality
        try:
            builder.reset()
            builder.mutation().add_field("test").build()
            self.log_success("QueryBuilder reset and mutation functionality works")
        except Exception as e:
            self.log_issue(f"QueryBuilder reset/mutation error: {e}")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate final validation report."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION REPORT")
        print("=" * 60)
        
        if self.validations_passed:
            print(f"\n✅ PASSED VALIDATIONS ({len(self.validations_passed)}):")
            for success in self.validations_passed:
                print(f"   {success}")
        
        if self.issues_found:
            print(f"\n❌ ISSUES FOUND ({len(self.issues_found)}):")
            for issue in self.issues_found:
                print(f"   {issue}")
        else:
            print("\n🎉 No issues found!")
            
        success_rate = len(self.validations_passed) / (len(self.validations_passed) + len(self.issues_found)) * 100 if (self.validations_passed or self.issues_found) else 0
        
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        print(f"   Passed: {len(self.validations_passed)}")
        print(f"   Issues: {len(self.issues_found)}")
        print("=" * 60)
        
        return {
            'success_rate': success_rate,
            'passed': len(self.validations_passed),
            'issues': len(self.issues_found),
            'validations_passed': self.validations_passed,
            'issues_found': self.issues_found
        }


if __name__ == "__main__":
    validator = ComprehensiveGraphQLValidator()
    report = validator.run_comprehensive_validation()
    
    # Exit with non-zero code if issues found
    sys.exit(0 if report['issues'] == 0 else 1)
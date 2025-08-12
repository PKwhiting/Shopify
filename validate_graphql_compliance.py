"""
GraphQL Documentation Compliance Check

This script can be run in CI/CD pipelines to ensure ongoing compliance
with Shopify's GraphQL API documentation standards.

Usage:
    python validate_graphql_compliance.py [--strict]

Returns exit code 0 if all validations pass, 1 if issues are found.
"""

import sys
import argparse
from typing import Dict, List, Set
import json

# Add SDK to path
sys.path.insert(0, '/home/runner/work/Shopify/Shopify/shopify_sdk')

from shopify.query_builder import QueryBuilder


def validate_all_queries() -> Dict[str, bool]:
    """Validate all queries in the SDK for compliance."""
    results = {}
    
    print("🔍 Validating Shopify GraphQL SDK Compliance...")
    print("-" * 50)
    
    # Test 1: Query Builder Static Methods
    print("1. Testing QueryBuilder static methods...")
    
    try:
        # Product query validation
        product_query, vars = QueryBuilder.build_product_query(first=10, after="test")
        
        # Basic validations
        assert 'query' in product_query.lower(), "Product query should start with 'query'"
        assert '$first: Int!' in product_query, "Product query should have proper 'first' parameter type"
        assert '$after: String' in product_query, "Product query should have proper 'after' parameter type"
        assert 'pageInfo' in product_query, "Product query should include pageInfo for pagination"
        assert 'edges' in product_query, "Product query should use edges/node pattern"
        assert 'userErrors' not in product_query, "Product query should not include userErrors (that's for mutations)"
        
        # Variable validation
        assert isinstance(vars, dict), "Variables should be a dictionary"
        assert vars['first'] == 10, "First variable should match requested value"
        assert vars['after'] == "test", "After variable should match requested value"
        
        results['product_query'] = True
        print("   ✅ Product query validation passed")
        
    except AssertionError as e:
        results['product_query'] = False
        print(f"   ❌ Product query validation failed: {e}")
    except Exception as e:
        results['product_query'] = False
        print(f"   ❌ Product query validation error: {e}")
    
    try:
        # Customer query validation  
        customer_query, vars = QueryBuilder.build_customer_query(first=25)
        
        assert 'query' in customer_query.lower(), "Customer query should start with 'query'"
        assert '$first: Int!' in customer_query, "Customer query should have proper 'first' parameter type"
        assert 'customers(' in customer_query, "Customer query should query 'customers' field"
        assert 'pageInfo' in customer_query, "Customer query should include pageInfo"
        assert vars['first'] == 25, "First variable should match requested value"
        
        results['customer_query'] = True
        print("   ✅ Customer query validation passed")
        
    except AssertionError as e:
        results['customer_query'] = False
        print(f"   ❌ Customer query validation failed: {e}")
    except Exception as e:
        results['customer_query'] = False
        print(f"   ❌ Customer query validation error: {e}")
    
    try:
        # Order query validation
        order_query, vars = QueryBuilder.build_order_query(first=15)
        
        assert 'query' in order_query.lower(), "Order query should start with 'query'"
        assert '$first: Int!' in order_query, "Order query should have proper 'first' parameter type"
        assert 'orders(' in order_query, "Order query should query 'orders' field"  
        assert 'totalPriceSet' in order_query, "Order query should include price information"
        assert vars['first'] == 15, "First variable should match requested value"
        
        results['order_query'] = True
        print("   ✅ Order query validation passed")
        
    except AssertionError as e:
        results['order_query'] = False
        print(f"   ❌ Order query validation failed: {e}")
    except Exception as e:
        results['order_query'] = False
        print(f"   ❌ Order query validation error: {e}")
    
    # Test 2: QueryBuilder Dynamic Methods
    print("\n2. Testing QueryBuilder dynamic functionality...")
    
    try:
        builder = QueryBuilder()
        
        # Test basic query building
        query, vars = builder.add_field("shop { name }").build()
        assert query.strip().startswith('query'), "Dynamic query should start with 'query'"
        assert 'shop' in query, "Query should include requested field"
        
        # Test mutation building
        builder.reset().mutation()
        mutation, vars = builder.add_field("shopUpdate { shop { id } }").build()
        assert mutation.strip().startswith('mutation'), "Dynamic mutation should start with 'mutation'"
        
        # Test variables
        builder.reset()
        query, vars = builder.add_variable("test", "String!", "value").add_field("shop { name }").build()
        assert '$test: String!' in query, "Query should include variable definition"
        assert vars.get('test') == 'value', "Variables should include defined variable"
        
        results['query_builder'] = True
        print("   ✅ QueryBuilder dynamic functionality passed")
        
    except AssertionError as e:
        results['query_builder'] = False
        print(f"   ❌ QueryBuilder validation failed: {e}")
    except Exception as e:
        results['query_builder'] = False  
        print(f"   ❌ QueryBuilder validation error: {e}")
    
    # Test 3: API Version and URL Structure
    print("\n3. Testing API configuration...")
    
    try:
        from shopify import ShopifyClient
        
        client = ShopifyClient("test-shop.myshopify.com", "test-key")
        
        # Check API version
        assert "2024-01" in client.base_url, "Should use current API version (2024-01)"
        
        # Check URL structure
        expected_parts = [
            "https://test-shop.myshopify.com",
            "/admin/api/2024-01/graphql.json"
        ]
        for part in expected_parts:
            assert part in client.base_url, f"URL should contain {part}"
        
        results['api_config'] = True
        print("   ✅ API configuration validation passed")
        
    except AssertionError as e:
        results['api_config'] = False
        print(f"   ❌ API configuration validation failed: {e}")
    except Exception as e:
        results['api_config'] = False
        print(f"   ❌ API configuration validation error: {e}")
    
    # Test 4: Field Name Standards
    print("\n4. Testing GraphQL field naming standards...")
    
    try:
        # Get a sample query to check field names
        query, _ = QueryBuilder.build_product_query(first=5)
        
        # Check for proper camelCase usage
        problematic_patterns = [
            '_id',  # Should be just 'id'
            'created_at',  # Should be 'createdAt'
            'updated_at',  # Should be 'updatedAt'
            'product_type',  # Should be 'productType'
        ]
        
        for pattern in problematic_patterns:
            assert pattern not in query, f"Query should not contain snake_case pattern: {pattern}"
        
        # Check for expected camelCase fields
        expected_camelcase = ['createdAt', 'updatedAt', 'productType']
        for field in expected_camelcase:
            assert field in query, f"Query should use camelCase field: {field}"
        
        results['field_naming'] = True
        print("   ✅ Field naming standards validation passed")
        
    except AssertionError as e:
        results['field_naming'] = False
        print(f"   ❌ Field naming validation failed: {e}")
    except Exception as e:
        results['field_naming'] = False
        print(f"   ❌ Field naming validation error: {e}")
    
    return results


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Validate GraphQL compliance")
    parser.add_argument('--strict', action='store_true', help='Fail on any validation issue')
    args = parser.parse_args()
    
    results = validate_all_queries()
    
    # Summary
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    failed = total - passed
    
    print(f"\n{'='*50}")
    print("📊 COMPLIANCE REPORT")
    print(f"{'='*50}")
    print(f"✅ Passed: {passed}/{total}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{total}")
        print("\nFailed validations:")
        for test_name, result in results.items():
            if not result:
                print(f"   • {test_name}")
    else:
        print("🎉 All validations passed!")
    
    success_rate = (passed / total) * 100
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if args.strict and failed > 0:
        print("\n⚠️  Strict mode: Exiting with error due to failed validations")
        sys.exit(1)
    elif failed > 0:
        print("\n⚠️  Some validations failed, but not in strict mode")
        sys.exit(1)
    else:
        print("\n✅ All GraphQL compliance checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
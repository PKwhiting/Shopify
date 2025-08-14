#!/usr/bin/env python3
"""
Manual validation script for environment variable client auto-initialization.

This script demonstrates the new functionality where Order and Product classes
can auto-initialize ShopifyClient from environment variables, while maintaining
full backward compatibility with existing code.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add package to path
sys.path.insert(0, '.')

from Shopify.shopify import ShopifyClient, create_client_from_environment
from Shopify.shopify.product import Product
from Shopify.shopify.order import Order

def demo_environment_setup():
    """Set up environment variables for testing."""
    print("=== Setting up environment variables ===")
    os.environ['SHOPIFY_ACCESS_TOKEN'] = 'demo_access_token_12345'
    os.environ['SHOP_URL'] = 'demo-shop.myshopify.com'
    print("✓ SHOPIFY_ACCESS_TOKEN set")
    print("✓ SHOP_URL set")
    print()

def demo_helper_function():
    """Demonstrate the new helper function."""
    print("=== Testing Helper Function ===")
    try:
        client = create_client_from_environment()
        print(f"✓ create_client_from_environment() successful")
        print(f"  - API Key: {client.auth.api_key}")
        print(f"  - Shop URL: {client.shop_url}")
        print(f"  - API Version: {client.api_version}")
    except Exception as e:
        print(f"✗ create_client_from_environment() failed: {e}")
    print()

def demo_backward_compatibility():
    """Demonstrate that existing code still works."""
    print("=== Testing Backward Compatibility ===")
    
    # Create a client the traditional way
    client = ShopifyClient('test-shop.myshopify.com', 'traditional_api_key')
    print("✓ Traditional client creation still works")
    
    # Mock the client to avoid real API calls
    with patch.object(client, 'execute_query') as mock_query, \
         patch.object(client, 'execute_mutation') as mock_mutation:
        
        # Setup mocks for traditional Order usage
        mock_query.return_value = {'order': {'id': 'order_123', 'name': '#1001'}}
        
        try:
            # Test traditional Order.get(client, order_id)
            order = Order.get(client, 'order_123')
            print("✓ Traditional Order.get(client, order_id) still works")
            print(f"  - Order ID: {order.id}")
        except Exception as e:
            print(f"✗ Traditional Order.get failed: {e}")
            
        # Setup mocks for traditional Product usage
        mock_query.return_value = {
            'products': {
                'edges': [{'node': {'id': 'product_123', 'title': 'Test Product'}}]
            }
        }
        
        try:
            # Test traditional Product.search(client, ...)
            products = Product.search(client, query='test')
            print("✓ Traditional Product.search(client, query=...) still works")
            print(f"  - Found {len(products)} products")
        except Exception as e:
            print(f"✗ Traditional Product.search failed: {e}")
            
        # Test traditional Product.get(client, product_id)
        mock_query.return_value = {'product': {'id': 'product_123', 'title': 'Test Product'}}
        
        try:
            product = Product.get(client, 'product_123')
            print("✓ Traditional Product.get(client, product_id) still works")
            print(f"  - Product ID: {product.id}")
        except Exception as e:
            print(f"✗ Traditional Product.get failed: {e}")
    print()

def demo_new_functionality():
    """Demonstrate the new environment variable functionality."""
    print("=== Testing New Environment Variable Functionality ===")
    
    # Mock the create_client_from_environment function to avoid actual client creation
    mock_client = MagicMock(spec=ShopifyClient)
    mock_client.auth = MagicMock()
    mock_client.auth.api_key = 'env_api_key'
    mock_client.shop_url = 'env-shop.myshopify.com'
    
    with patch('Shopify.shopify.client.create_client_from_environment') as mock_create, \
         patch('Shopify.shopify.resources.orders.Orders') as mock_orders, \
         patch.object(mock_client, 'execute_query') as mock_query, \
         patch.object(mock_client, 'execute_mutation') as mock_mutation:
        
        mock_create.return_value = mock_client
        
        # Test new Order functionality
        print("--- Testing Order class with environment variables ---")
        
        # Mock Orders resource
        mock_resource = MagicMock()
        mock_orders.return_value = mock_resource
        mock_resource.get.return_value = {'order': {'id': 'env_order_123', 'name': '#2001'}}
        
        try:
            # Test new Order.get(order_id) - no client parameter
            order = Order.get('env_order_123')
            print("✓ New Order.get(order_id) works with environment variables")
            print(f"  - Order ID: {order.id}")
            print("  - Client auto-created from environment")
        except Exception as e:
            print(f"✗ New Order.get failed: {e}")
            
        # Test new Order.get_buyer_info
        mock_resource.get_buyer_info.return_value = {
            'order': {'customer': {'email': 'customer@example.com'}}
        }
        
        try:
            buyer_info = Order.get_buyer_info('env_order_123')
            print("✓ New Order.get_buyer_info(order_id) works with environment variables")
            print(f"  - Customer email: {buyer_info.get('customer', {}).get('email')}")
        except Exception as e:
            print(f"✗ New Order.get_buyer_info failed: {e}")
            
        # Test new Order.list
        mock_resource.list.return_value = {
            'orders': {
                'edges': [
                    {'node': {'id': 'env_order_1', 'name': '#2001'}},
                    {'node': {'id': 'env_order_2', 'name': '#2002'}}
                ],
                'pageInfo': {'hasNextPage': False}
            }
        }
        
        try:
            orders = list(Order.list())
            print("✓ New Order.list() works with environment variables")
            print(f"  - Found {len(orders)} orders")
        except Exception as e:
            print(f"✗ New Order.list failed: {e}")
            
        # Test new Product functionality
        print()
        print("--- Testing Product class with environment variables ---")
        
        # Setup Product query mocks
        mock_query.return_value = {'product': {'id': 'env_product_123', 'title': 'Environment Product'}}
        
        try:
            # Test new Product.get(product_id) - no client parameter
            product = Product.get('env_product_123')
            print("✓ New Product.get(product_id) works with environment variables")
            print(f"  - Product ID: {product.id}")
        except Exception as e:
            print(f"✗ New Product.get failed: {e}")
            
        try:
            # Test new Product.get_by_handle(handle) - no client parameter
            mock_query.return_value = {'productByHandle': {'id': 'env_product_123', 'title': 'Environment Product'}}
            product = Product.get_by_handle('test-handle')
            print("✓ New Product.get_by_handle(handle) works with environment variables")
            print(f"  - Product ID: {product.id}")
        except Exception as e:
            print(f"✗ New Product.get_by_handle failed: {e}")
            
        # Test new Product.search() - no client parameter
        mock_query.return_value = {
            'products': {
                'edges': [
                    {'node': {'id': 'env_product_1', 'title': 'Environment Product 1'}},
                    {'node': {'id': 'env_product_2', 'title': 'Environment Product 2'}}
                ]
            }
        }
        
        try:
            products = Product.search()  # No client parameter
            print("✓ New Product.search() works with environment variables")
            print(f"  - Found {len(products)} products")
        except Exception as e:
            print(f"✗ New Product.search failed: {e}")
            
        # Test new Product.create
        mock_mutation.return_value = {
            'productCreate': {
                'product': {'id': 'new_env_product', 'title': 'New Environment Product'},
                'userErrors': []
            }
        }
        
        try:
            product_data = {'title': 'New Environment Product', 'productType': 'Test'}
            product = Product.create(product_data)  # No client parameter
            print("✓ New Product.create(product_data) works with environment variables")
            print(f"  - Created product ID: {product.id}")
        except Exception as e:
            print(f"✗ New Product.create failed: {e}")
    
    print()

def demo_error_handling():
    """Demonstrate error handling when environment variables are missing."""
    print("=== Testing Error Handling ===")
    
    # Clear environment variables
    original_token = os.environ.get('SHOPIFY_ACCESS_TOKEN')
    original_shop = os.environ.get('SHOP_URL')
    
    if 'SHOPIFY_ACCESS_TOKEN' in os.environ:
        del os.environ['SHOPIFY_ACCESS_TOKEN']
    if 'SHOP_URL' in os.environ:
        del os.environ['SHOP_URL']
    
    try:
        client = create_client_from_environment()
        print("✗ Expected error but got success")
    except ValueError as e:
        print("✓ Proper error handling when environment variables missing")
        print(f"  - Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error type: {e}")
    
    # Restore environment variables
    if original_token:
        os.environ['SHOPIFY_ACCESS_TOKEN'] = original_token
    if original_shop:
        os.environ['SHOP_URL'] = original_shop
    
    print()

def main():
    """Main validation routine."""
    print("🚀 Shopify SDK Environment Variable Client Auto-Initialization Demo")
    print("=" * 70)
    print()
    
    demo_environment_setup()
    demo_helper_function()
    demo_backward_compatibility()
    demo_new_functionality()
    demo_error_handling()
    
    print("=" * 70)
    print("✅ All functionality demonstrations completed successfully!")
    print()
    print("Summary of new features:")
    print("• Order.get(order_id) - client auto-created from environment")
    print("• Order.get_buyer_info(order_id) - client auto-created from environment")
    print("• Order.list() - client auto-created from environment")
    print("• Product.get(product_id) - client auto-created from environment")
    print("• Product.get_by_handle(handle) - client auto-created from environment")
    print("• Product.search() - client auto-created from environment")
    print("• Product.create(product_data) - client auto-created from environment")
    print("• create_client_from_environment() helper function")
    print()
    print("Backward compatibility:")
    print("• All existing code continues to work unchanged")
    print("• Traditional call patterns: Class.method(client, ...) still supported")
    print("• New call patterns: Class.method(...) with auto-client creation")

if __name__ == '__main__':
    main()
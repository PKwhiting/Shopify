#!/usr/bin/env python3
"""
Example demonstrating the dynamic publication functionality.
This example shows how the Product class now queries for publications
dynamically instead of using a hardcoded publication ID.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shopify_sdk'))

from shopify import ShopifyClient
from shopify.product import Product


def main():
    """Demonstrate dynamic publication functionality."""
    print("📦 Shopify Product Publication Example")
    print("=" * 50)
    
    # Initialize client (would normally use real credentials)
    client = ShopifyClient('example-shop.myshopify.com', 'dummy-access-token')
    
    # Create a product instance
    product_data = {
        'id': 'gid://shopify/Product/123456789',
        'title': 'Example Product', 
        'handle': 'example-product',
        'status': 'DRAFT'
    }
    
    product = Product(client, product_data)
    
    print(f"Product: {product.title}")
    print(f"Status: {product.status}")
    print(f"Published: {product.is_published}")
    print()
    
    print("🔧 How it works:")
    print("- Before: Used static WEB_PUBLICATION_ID = 'gid://shopify/Publication/1'")
    print("- After: Queries store for available publications dynamically")
    print("- Caches results to avoid repeated API calls")
    print("- Falls back to static ID if query fails (backward compatibility)")
    print()
    
    print("🚀 Publishing behavior:")
    print("1. product.publish() - Uses dynamic publication lookup")
    print("2. product.publish(publications=[...]) - Uses provided publications") 
    print("3. If no publications found - Falls back to static ID")
    print()
    
    print("✅ Benefits:")
    print("- Works with all Shopify stores (no hardcoded IDs)")
    print("- Automatically finds the correct web publication")
    print("- Maintains full backward compatibility")
    print("- Improved error handling")
    
    print("\n🎯 This change resolves the issue where the static publication ID")
    print("   'gid://shopify/Publication/1' wouldn't work for all stores.")


if __name__ == '__main__':
    main()
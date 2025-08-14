"""
Integration test: Product lifecycle (create, query, publish, unpublish, delete)

This test will create products, verify their existence, publish/unpublish, and clean up by deleting them.
Requires valid Shopify API credentials in environment variables.
"""

import os
import pytest
import sys
import pathlib

# Ensure project root is on sys.path for absolute imports
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from shopify_sdk.shopify import ShopifyClient
from shopify_sdk.shopify.product import Product


@pytest.mark.integration
def test_product_lifecycle():
    client = ShopifyClient()

    # 1. Create a product
    new_product_data = {
        'title': 'Integration Test Product',
        'descriptionHtml': 'Created by integration test.',
        'vendor': 'IntegrationTestVendor',
        'productType': 'IntegrationTestType',
        'status': 'DRAFT',
        'tags': ['integration', 'test'],
    }
    try:
        product = Product.create(client, new_product_data)
        assert product.id, "Product creation failed: No ID returned."
    except Exception as e:
        # Print the full mutation response for debugging
        import traceback
        print("Product creation failed:", e)
        traceback.print_exc()
        # Try to print the last mutation response if available
        if hasattr(client, '_last_response'):
            print("Last mutation response:", client._last_response)
        raise

    # 2. Query the product by handle
    queried = Product.get_by_handle(client, product.handle)
    assert queried is not None, "Product not found by handle."
    assert queried.id == product.id

    # 3. Publish the product
    published = product.publish()
    assert published.status == "ACTIVE"

    # 4. Unpublish the product
    unpublished = product.unpublish()
    assert unpublished.status == "DRAFT"

    # 5. Delete the product
    deleted = product.delete()
    assert deleted is True, "Product deletion failed."

    # 6. Confirm deletion
    should_be_none = Product.get(client, product.id)
    assert should_be_none is None, "Product still exists after deletion."

import pytest
from shopify_sdk.shopify import ShopifyClient
from shopify_sdk.shopify.product import Product

@pytest.mark.integration
def test_product_update_lifecycle():
    client = ShopifyClient()

    # 1. Create a product
    product_data = {
        'title': 'Integration Update Test Product',
        'descriptionHtml': 'Initial description.',
        'vendor': 'IntegrationTestVendor',
        'productType': 'IntegrationTestType',
        'status': 'DRAFT',
        'tags': ['integration', 'update'],
    }
    product = Product.create(client, product_data)
    assert product.id
    assert product.title == 'Integration Update Test Product'
    assert product.description == 'Initial description.'

    # 2. Update product fields
    product.title = 'Integration Updated Title'
    product.description = 'Updated description.'
    tags = product.tags.copy()
    tags.append('updated')
    product.tags = tags
    product.save()

    # 3. Retrieve and verify updates
    updated = Product.get(client, product.id)
    assert updated.title == 'Integration Updated Title'
    assert updated.description == 'Updated description.'
    assert 'updated' in updated.tags

    # 4. Clean up
    assert product.delete()

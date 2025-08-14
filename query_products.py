"""
Example script to query products from Shopify using the SDK
"""
import os
from shopify_sdk.shopify import ShopifyClient, QueryBuilder
from shopify_sdk.shopify.product import Product
from shopify_sdk.shopify.client import ShopifyClient


# Load credentials from environment variables
# shop_url = os.getenv("SHOP_URL", "your-shop.myshopify.com")
# api_key = os.getenv("SHOPIFY_API_KEY", "your-api-key")

# Initialize client
client = ShopifyClient()

# Build a simple products query
builder = QueryBuilder()
builder.add_field("products(first: 10) { edges { node { id title handle } } }")
query, variables = builder.build()

# Execute query

print(query)
print(variables)
response = client.execute_query(query, variables)
print("Products response:", response)

# Extract and print handles from the products response

product_nodes = [edge['node'] for edge in response.get('products', {}).get('edges', [])]
print('Product nodes (full data):')
for prod in product_nodes:
	print(prod)


# Use the first product's handle for get_by_handle, then test publish/unpublish
first_handle = product_nodes[0].get('handle') if product_nodes and product_nodes[0].get('handle') else None
if first_handle:
	p_by_handle = Product.get_by_handle(client, first_handle)
	print('Product by handle:', p_by_handle)
	if p_by_handle:
		# Try to unpublish the product
		try:
			p_by_handle.unpublish()
			print('Product unpublished. Status:', p_by_handle.status)
		except Exception as e:
			print('Unpublish failed:', e)
		# Try to publish the product
		try:
			p_by_handle.publish()
			print('Product published. Status:', p_by_handle.status)
		except Exception as e:
			print('Publish failed:', e)
	else:
		print('Product.get_by_handle returned None.')
else:
	print('No valid handle found for get_by_handle test.')

# Test search with a likely keyword
products = Product.search(client, query='Mazda', first=2)
print('Product search:', products)

# Test create (will fail if you do not have permissions or required fields)
# Uncomment to test product creation
# new_product_data = {
#     'title': 'Test Product',
#     'vendor': 'Test Vendor',
#     'productType': 'Test Type',
#     'tags': ['test'],
#     'description': 'Created via API',
# }
# try:
#     created_product = Product.create(client, new_product_data)
#     print('Created product:', created_product)
# except Exception as e:
#     print('Product creation failed:', e)



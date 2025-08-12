"""
Example script to query products from Shopify using the SDK
"""
import os
from shopify_sdk.shopify import ShopifyClient, QueryBuilder

def main():
    # Load credentials from environment variables
    shop_url = os.getenv("SHOP_URL", "your-shop.myshopify.com")
    api_key = os.getenv("SHOPIFY_API_KEY", "your-api-key")

    # Initialize client
    client = ShopifyClient(shop_url, api_key)

    # Build a simple products query
    builder = QueryBuilder()
    builder.add_field("products { edges { node { id title } } }")
    query, variables = builder.build()

    # Execute query
    response = client.execute_query(query, variables)
    print("Products response:", response)

if __name__ == "__main__":
    main()

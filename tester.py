"""
Example script to query products from Shopify using the SDK
"""
import os
from shopify_sdk.shopify import ShopifyClient, QueryBuilder
# https://avq109-tj.myshopify.com/admin/api/2025-07/graphql.json
# https://your-development-store.myshopify.com/admin/api/2025-01/graphql.json
def main():
    # Load credentials from environment variables
    # shop_url = os.getenv("SHOP_URL", "your-shop.myshopify.com")
    # api_key = os.getenv("SHOPIFY_ACCESS_TOKEN", "your-api-key")
    # print(shop_url)
    # print(api_key)

    # Initialize client
    client = ShopifyClient()

    # Build a simple products query
    builder = QueryBuilder()
    builder.add_field("""
    products(first: 10) {
        nodes {
            id
            title
        }
    }
    """)
    query, variables = builder.build()

    # Execute query
    response = client.execute_query(query, variables)
    print("Products response:", response)

if __name__ == "__main__":
    main()

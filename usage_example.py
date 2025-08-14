#!/usr/bin/env python3
"""
Simple usage example demonstrating the new environment variable functionality.
This shows how the new feature improves developer experience.
"""

import os
import sys

# Add package to path for demonstration
sys.path.insert(0, '.')

# Set up environment variables (in real usage, these would be in .env file)
os.environ['SHOPIFY_ACCESS_TOKEN'] = 'your_actual_access_token_here'
os.environ['SHOP_URL'] = 'your-shop.myshopify.com'

# Import the SDK
from Shopify.shopify.product import Product
from Shopify.shopify.order import Order

def before_and_after_comparison():
    """Show the improvement in developer experience."""
    
    print("🔄 BEFORE (traditional approach):")
    print("""
from shopify import ShopifyClient
from shopify.auth import from_environment

# Step 1: Create authentication
auth = from_environment()

# Step 2: Create client
client = ShopifyClient("your-shop.myshopify.com", auth.api_key)

# Step 3: Use the client for operations
order = Order.get(client, "order_id_here")
product = Product.get(client, "product_id_here")
products = Product.search(client, query="shirts")
""")
    
    print("✨ AFTER (new environment variable approach):")
    print("""
from shopify.product import Product
from shopify.order import Order

# Environment variables are automatically used - no client setup needed!
order = Order.get("order_id_here")
product = Product.get("product_id_here")  
products = Product.search(query="shirts")
""")

def usage_examples():
    """Show practical usage examples of the new functionality."""
    
    print("📖 Usage Examples:")
    print("\n1. Get an order (no client needed):")
    print("   order = Order.get('gid://shopify/Order/12345')")
    
    print("\n2. Get buyer information (no client needed):")
    print("   buyer_info = Order.get_buyer_info('gid://shopify/Order/12345')")
    
    print("\n3. List all orders (no client needed):")
    print("   for order in Order.list():")
    print("       print(f'Order {order.name}: {order.email}')")
    
    print("\n4. Search for products (no client needed):")
    print("   products = Product.search(query='t-shirt', first=20)")
    
    print("\n5. Get a product by ID (no client needed):")
    print("   product = Product.get('gid://shopify/Product/67890')")
    
    print("\n6. Get a product by handle (no client needed):")
    print("   product = Product.get_by_handle('awesome-t-shirt')")
    
    print("\n7. Create a new product (no client needed):")
    print("   product_data = {'title': 'New T-Shirt', 'productType': 'Apparel'}")
    print("   product = Product.create(product_data)")

def environment_setup():
    """Show how to set up environment variables."""
    
    print("⚙️  Environment Setup:")
    print("\nOption 1 - Using .env file (recommended):")
    print("""
# Create .env file in your project root
SHOPIFY_ACCESS_TOKEN=your_actual_access_token_here
SHOP_URL=your-shop.myshopify.com

# The SDK automatically loads these variables
""")
    
    print("Option 2 - Set environment variables directly:")
    print("""
import os
os.environ['SHOPIFY_ACCESS_TOKEN'] = 'your_actual_access_token_here'
os.environ['SHOP_URL'] = 'your-shop.myshopify.com'
""")

def backward_compatibility():
    """Emphasize that existing code continues to work."""
    
    print("🔒 Backward Compatibility:")
    print("""
✅ All existing code continues to work unchanged!

# Traditional approach still works
from shopify import ShopifyClient
client = ShopifyClient("shop.myshopify.com", "api_key")
order = Order.get(client, "order_id")
product = Product.search(client, query="shirts")

# New approach is optional - use it when you want simpler code
order = Order.get("order_id")  # Auto-creates client from environment
product = Product.search(query="shirts")  # Auto-creates client from environment
""")

def main():
    """Main demonstration."""
    print("🚀 Shopify SDK - Environment Variable Client Auto-Initialization")
    print("=" * 70)
    
    before_and_after_comparison()
    print("\n" + "=" * 70)
    
    usage_examples()  
    print("\n" + "=" * 70)
    
    environment_setup()
    print("\n" + "=" * 70)
    
    backward_compatibility()
    print("\n" + "=" * 70)
    
    print("🎉 Key Benefits:")
    print("• Simpler, cleaner code")
    print("• Fewer lines of boilerplate")
    print("• Automatic client management")
    print("• Environment variable best practices")
    print("• 100% backward compatible")
    print("• Same powerful functionality")

if __name__ == '__main__':
    main()
# Shopify GraphQL SDK

A Python SDK for interacting with Shopify's GraphQL API. This SDK provides a clean and intuitive interface for working with Shopify's GraphQL API, including authentication via API keys, resource management, pagination, error handling, and webhook processing.

## Features

- **GraphQL API Support**: Full support for Shopify's GraphQL API
- **API Key Authentication**: Simple authentication using API access tokens (no OAuth)
- **Resource Management**: Easy-to-use classes for Products, Customers, and Orders
- **Query Builder**: Flexible GraphQL query building utilities
- **Pagination**: Automatic handling of cursor-based pagination
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Webhook Processing**: Webhook signature verification and event handling
- **Type Hints**: Full type hint support for better IDE integration

## Installation

```bash
pip install shopify-graphql-sdk
```

Or install from source with dependencies:

```bash
pip install -r requirements.txt
```

### Environment Configuration

For secure credential management, you can use environment variables instead of hardcoding API keys:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual Shopify credentials in `.env`:
   ```env
   SHOPIFY_API_KEY=your_actual_api_key
   SHOPIFY_SECRET=your_actual_secret
   SHOPIFY_ACCESS_TOKEN=your_actual_access_token
   ```

3. The `.env` file is automatically ignored by git for security.

## Quick Start

### Using Direct API Key

```python
from shopify import ShopifyClient

# Initialize the client with explicit API key
client = ShopifyClient(
    shop_url="your-shop.myshopify.com",
    api_key="your-api-access-token"
)

# List products
products_response = client.execute_query("""
    query {
        products(first: 10) {
            edges {
                node {
                    id
                    title
                    handle
                }
            }
        }
    }
""")

print(products_response)
```

### Using Environment Variables

```python
from shopify import ShopifyClient
from shopify.auth import from_environment

# Initialize authentication from environment variables
auth = from_environment()  # Loads SHOPIFY_ACCESS_TOKEN from .env

# Initialize client with environment-based auth
client = ShopifyClient(
    shop_url="your-shop.myshopify.com",
    api_key=auth.api_key  # Uses token from environment
)

# Or simply use the environment variable directly (if available)
import os
client = ShopifyClient(
    shop_url="your-shop.myshopify.com", 
    api_key=os.getenv('SHOPIFY_ACCESS_TOKEN')
)
```

## Usage

### Authentication

The SDK supports two methods of authentication:

#### 1. Direct API Key (Traditional)
```python
from shopify.auth import ApiKeyAuth

# Create auth with explicit API key
auth = ApiKeyAuth("your-api-access-token")
print(auth.get_headers())  # {'X-Shopify-Access-Token': 'your-api-access-token'}
```

#### 2. Environment Variables (Recommended)
```python
from shopify.auth import from_environment
import os

# Set environment variable
os.environ['SHOPIFY_ACCESS_TOKEN'] = 'your-api-access-token'

# Create auth from environment
auth = from_environment()
print(auth.get_headers())  # {'X-Shopify-Access-Token': 'your-api-access-token'}
```

The environment variable approach is more secure as it keeps sensitive credentials out of your code.

### Client Initialization

```python
from shopify import ShopifyClient

client = ShopifyClient(
    shop_url="your-shop.myshopify.com",
    api_key="your-api-access-token",
    api_version="2025-07"  # Optional, defaults to 2025-07
)
```

### Working with Resources

#### Products

```python
from shopify.resources import Products

products = Products(client)

# List products with pagination
products_data = products.list(first=20)

# Get a specific product
product = products.get("gid://shopify/Product/123456789")

# Create a new product
new_product = products.create({
    "title": "New Product",
    "productType": "Widget",
    "vendor": "Acme Corp"
})

# Update a product
updated_product = products.update("gid://shopify/Product/123456789", {
    "title": "Updated Product Title"
})
```

#### Customers

```python
from shopify.resources import Customers

customers = Customers(client)

# List customers
customers_data = customers.list(first=50)

# Get a specific customer
customer = customers.get("gid://shopify/Customer/123456789")

# Create a new customer
new_customer = customers.create({
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
})
```

#### Orders

```python
from shopify.resources import Orders

orders = Orders(client)

# List orders
orders_data = orders.list(first=25)

# Get a specific order
order = orders.get("gid://shopify/Order/123456789")

# Cancel an order
cancelled_order = orders.cancel(
    "gid://shopify/Order/123456789",
    reason="customer",
    notify_customer=True
)

# Get comprehensive buyer information for an order
buyer_info = orders.get_buyer_info("gid://shopify/Order/123456789")

# The buyer info includes:
# - Customer details (name, email, phone, marketing preferences, tags)
# - Customer addresses (default address and all addresses)
# - Order billing and shipping addresses
# - Customer order history
print(f"Customer: {buyer_info['order']['customer']['firstName']} {buyer_info['order']['customer']['lastName']}")
print(f"Email: {buyer_info['order']['customer']['email']}")
print(f"Phone: {buyer_info['order']['customer']['phone']}")
print(f"Marketing: {buyer_info['order']['customer']['acceptsMarketing']}")
```

#### Enhanced Buyer Information

The Orders resource now provides comprehensive buyer information with enhanced queries that include:

- **Customer Details**: Name, email, phone, marketing preferences, tags, notes, creation date
- **Customer Addresses**: Default address and all customer addresses
- **Order Addresses**: Billing and shipping addresses with complete details
- **Customer History**: Access to customer's order history and lifetime data

```python
# List orders with enhanced buyer information
orders_with_buyers = orders.list(first=20)

# Each order now includes comprehensive buyer data:
for edge in orders_with_buyers['orders']['edges']:
    order = edge['node']
    customer = order['customer']
    billing = order['billingAddress']
    shipping = order['shippingAddress']
    
    print(f"Order {order['name']}")
    print(f"Customer: {customer['firstName']} {customer['lastName']}")
    print(f"Email: {customer['email']}")
    print(f"Phone: {customer['phone']}")
    print(f"Marketing: {customer['acceptsMarketing']}")
    if billing:
        print(f"Billing: {billing['city']}, {billing['province']}")
    if shipping:
        print(f"Shipping: {shipping['city']}, {shipping['province']}")
```
```

### Query Builder

```python
from shopify import QueryBuilder

# Using the query builder
builder = QueryBuilder()

query, variables = (builder
    .add_variable("first", "Int!", 10)
    .add_field("products(first: $first) { edges { node { id title } } }")
    .build())

result = client.execute_query(query, variables)

# Pre-built queries
query, variables = QueryBuilder.build_product_query(first=20)
products = client.execute_query(query, variables)
```

### Pagination

```python
from shopify.utils import PaginationHelper

pagination = PaginationHelper()

# Get products with pagination
query, variables = QueryBuilder.build_product_query(first=10)
data = client.execute_query(query, variables)

# Extract nodes
products = pagination.extract_nodes(data, "products")

# Check for next page
if pagination.has_next_page(data, "products"):
    next_cursor = pagination.get_next_cursor(data, "products")
    
    # Fetch next page
    query, variables = QueryBuilder.build_product_query(first=10, after=next_cursor)
    next_data = client.execute_query(query, variables)

# Auto-paginate through all results
for product in pagination.paginate_all(client, query_func, "products", page_size=50):
    print(f"Product: {product['title']}")
```

### Error Handling

```python
from shopify.utils.error_handler import ShopifyAPIError, ShopifyGraphQLError, ShopifyRateLimitError

try:
    result = client.execute_query("invalid query")
except ShopifyGraphQLError as e:
    print(f"GraphQL Error: {e.message}")
    print(f"Errors: {e.graphql_errors}")
except ShopifyRateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except ShopifyAPIError as e:
    print(f"API Error: {e.message}")
```

### Webhook Handling

```python
from shopify.webhooks import WebhookVerifier, WebhookHandler

# Verify webhook signatures
verifier = WebhookVerifier("your-webhook-secret")
is_valid = verifier.verify_signature(payload, signature)

# Handle webhook events
handler = WebhookHandler()

def process_order_created(event):
    order = event['data']
    print(f"New order: {order['name']}")
    # Process order...

# Register event handlers
handler.register_handler("orders/create", process_order_created)

# Process incoming webhook
result = handler.handle_webhook("orders/create", webhook_payload)
```

## API Coverage

This SDK covers the most commonly used Shopify GraphQL API features:

### Resources
- **Products**: Create, read, update, delete products and variants
- **Customers**: Manage customer information and addresses  
- **Orders**: Retrieve and manage orders, fulfillments, and cancellations with comprehensive buyer information

### Enhanced Buyer Information
- **Customer Details**: Full customer profiles with marketing preferences, tags, and notes
- **Address Management**: Billing, shipping, and default addresses with complete details  
- **Customer History**: Access to customer order history and lifetime data
- **Dedicated Buyer API**: Specialized `get_buyer_info()` method for comprehensive buyer data retrieval

### Features
- **Authentication**: API key-based authentication (no OAuth)
- **Pagination**: Cursor-based pagination with helper utilities
- **Error Handling**: Comprehensive error handling and retry logic
- **Webhooks**: Signature verification and event processing
- **Query Building**: Flexible GraphQL query construction

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/

# Run specific test file
python -m unittest tests.test_client
```

### Project Structure

```
shopify_sdk/
├── shopify/
│   ├── __init__.py
│   ├── client.py              # Main GraphQL client
│   ├── query_builder.py       # GraphQL query builder
│   ├── auth/
│   │   ├── __init__.py
│   │   └── api_key.py         # API key authentication
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── products.py        # Product operations
│   │   ├── customers.py       # Customer operations
│   │   └── orders.py          # Order operations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── pagination.py      # Pagination helpers
│   │   └── error_handler.py   # Error handling
│   └── webhooks/
│       ├── __init__.py
│       ├── verifier.py        # Webhook verification
│       └── handler.py         # Webhook event handling
├── tests/                     # Unit tests
├── setup.py                   # Package setup
└── README.md                  # Documentation
```

## Requirements

- Python 3.7+
- requests >= 2.25.0  
- python-dotenv >= 0.19.0 (for environment variable support)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/PKwhiting/Shopify/issues) page.

## Changelog

### v1.1.0
- Added environment variable support for secure credential management
- New `from_environment()` function for loading credentials from environment variables
- Added `requirements.txt` for easier dependency management
- Enhanced documentation with environment variable usage examples
- Maintains full backward compatibility with existing code

### v1.0.0
- Initial release
- Support for Products, Customers, and Orders resources
- GraphQL query builder
- Pagination utilities
- Error handling
- Webhook processing
- API key authentication
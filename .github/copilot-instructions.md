# Shopify GraphQL SDK

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- Install dependencies: 
  - `pip install -r requirements.txt` -- takes 7 seconds. Installs requests>=2.25.0, python-dotenv>=0.19.0, pytest>=6.0.0
- Development installation:
  - `cd shopify_sdk && pip install -e .` -- takes 2 seconds. Installs the SDK in development mode
- Development dependencies:
  - `cd shopify_sdk && pip install -e ".[dev]"` -- takes 13 seconds. Adds black, flake8, mypy, pytest-cov

### Build and Test
- Run all tests: 
  - `pytest shopify_sdk/tests/ -v` -- takes less than 1 second. NEVER CANCEL. Set timeout to 60+ seconds for safety
  - `pytest` from repository root -- takes less than 1 second. Runs all 61 tests
- Run tests with coverage:
  - `pytest shopify_sdk/tests/ --cov=shopify_sdk/shopify --cov-report=term-missing` -- takes 4 seconds. Shows 75% coverage
- Run specific test:
  - `python -m unittest shopify_sdk.tests.test_client.TestShopifyClient.test_client_initialization`

### Validation
- ALWAYS manually validate any changes by running the end-to-end validation script:
  ```bash
  # Create validation script to test all functionality
  python3 -c "
  import sys
  sys.path.insert(0, '/path/to/shopify_sdk')
  from shopify import ShopifyClient, QueryBuilder
  # Test client creation
  client = ShopifyClient('test-shop.myshopify.com', 'dummy-key')
  print(f'Client: {client.base_url}')
  # Test query building  
  builder = QueryBuilder()
  query, vars = builder.add_field('shop { name }').build()
  print(f'Query works: {query[:30]}...')
  print('✓ SDK validation successful')
  "
  ```
- Always test both direct API key and environment variable authentication methods
- ALWAYS run through at least one complete end-to-end scenario after making changes

### Code Quality
- Linting: 
  - `cd shopify_sdk && flake8 shopify/ --max-line-length=100` -- Current code has linting issues (whitespace, line length). Fix before committing
- Formatting: 
  - `cd shopify_sdk && black --line-length=100 shopify/` -- Current code needs formatting. Always run before committing
  - `cd shopify_sdk && black --check --line-length=100 shopify/` to check without changing
- Type checking:
  - `cd shopify_sdk && mypy shopify/` -- Available but not currently configured

## Environment Configuration

### Required Python Version
- Python 3.7+ (tested with Python 3.12.3)

### Environment Variables Setup
- Copy environment template: `cp .env.example .env`
- Required variables in `.env`:
  ```
  SHOPIFY_API_KEY=your_api_key_here
  SHOPIFY_SECRET=your_api_secret_here  
  SHOPIFY_ACCESS_TOKEN=your_access_token_here
  ```
- ALWAYS use environment variables for credentials in production code

### Repository Structure
```
/
├── .env.example                    # Environment template
├── .github/workflows/              # CI/CD pipeline
│   └── pull_request_tests.yml     # Runs pytest on PRs
├── requirements.txt                # Core dependencies
├── LICENSE                         # MIT license
└── shopify_sdk/                   # Main SDK directory
    ├── README.md                   # Comprehensive documentation
    ├── setup.py                    # Package configuration
    ├── shopify/                    # Source code
    │   ├── __init__.py            # Main exports: ShopifyClient, QueryBuilder
    │   ├── client.py              # GraphQL client implementation
    │   ├── query_builder.py       # GraphQL query utilities
    │   ├── auth/                  # Authentication modules
    │   ├── resources/             # Product, Customer, Order managers
    │   ├── utils/                 # Pagination, error handling
    │   └── webhooks/              # Webhook verification/handling
    └── tests/                     # Unit tests (61 tests, 100% pass rate)
        ├── test_client.py
        ├── test_auth.py
        ├── test_query_builder.py
        ├── test_resources.py
        ├── test_utils.py
        └── test_webhooks.py
```

## Common Development Tasks

### Testing Authentication
- Direct API key method:
  ```python
  from shopify import ShopifyClient
  client = ShopifyClient("your-shop.myshopify.com", "your-api-key")
  ```
- Environment variable method (PREFERRED):
  ```python
  from shopify import ShopifyClient
  from shopify.auth import from_environment
  auth = from_environment()
  client = ShopifyClient("your-shop.myshopify.com", auth.api_key)
  ```

### Working with Resources
- Products: `from shopify.resources import Products`
- Customers: `from shopify.resources import Customers`  
- Orders: `from shopify.resources import Orders`

### Query Building
- Custom queries: `QueryBuilder().add_field("...").build()`
- Pre-built queries: `QueryBuilder.build_product_query(first=20)`

### CI/CD Information
- GitHub Actions workflow in `.github/workflows/pull_request_tests.yml`
- Runs on Python 3.9 with Ubuntu
- Workflow steps: checkout → setup python → install deps → run pytest
- ALWAYS ensure tests pass before submitting PRs

## Validation Scenarios

### After Making Changes
1. Run full test suite: `pytest shopify_sdk/tests/ -v`
2. Test basic imports and client creation (see validation script above)
3. Verify both authentication methods work
4. Test query building functionality
5. Run linting and formatting tools
6. Check that GitHub Actions workflow would pass

### Known Issues
- Current codebase has linting issues (whitespace, line length violations)
- Code formatting needs to be applied with black
- 75% test coverage (room for improvement in resources and webhooks)

## Timing Expectations
- Dependency installation: 7 seconds
- Development installation: 2 seconds  
- Full test suite: <1 second. NEVER CANCEL. Set timeout to 60+ seconds
- Test with coverage: 4 seconds
- Linting: <1 second
- Formatting check: <1 second
- End-to-end validation: <1 second

## Key Implementation Notes
- This is a **GraphQL SDK** for Shopify (not REST API)
- Uses API key authentication (no OAuth implementation)
- Supports cursor-based pagination
- Includes webhook signature verification
- Full type hints support
- Comprehensive error handling with custom exceptions
- Environment variable support for secure credential management
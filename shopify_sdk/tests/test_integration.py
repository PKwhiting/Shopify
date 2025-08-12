"""
Integration Tests for Shopify SDK

Tests for complete workflows and integration between components.
These tests verify that different parts of the SDK work together correctly.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.client import ShopifyClient
from shopify.resources import Products, Customers, Orders
from shopify.query_builder import QueryBuilder
from shopify.config import ShopifyConfig
from shopify.auth.api_key import ApiKeyAuth
from shopify.utils.pagination import PaginationHelper
from shopify.utils.error_handler import ErrorHandler, ShopifyAPIError, ShopifyRateLimitError
from shopify.webhooks import WebhookVerifier, WebhookHandler


class TestEndToEndWorkflows(unittest.TestCase):
    """End-to-end integration tests for complete workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ShopifyConfig(api_version="2024-01", timeout=30)
        self.shop_url = "test-shop.myshopify.com"
        self.api_key = "test_api_key_12345"
        
        # Create a real client (but we'll mock the HTTP requests)
        self.client = ShopifyClient(self.shop_url, self.api_key, config=self.config)
        
        # Create resource instances
        self.products = Products(self.client)
        self.customers = Customers(self.client)
        self.orders = Orders(self.client)
    
    @patch('requests.post')
    def test_complete_product_workflow(self, mock_post):
        """Test complete product workflow: create, read, update, list."""
        # Mock responses for different operations
        create_response = {
            "data": {
                "productCreate": {
                    "product": {
                        "id": "gid://shopify/Product/123456789",
                        "title": "Test Product",
                        "handle": "test-product"
                    },
                    "userErrors": []
                }
            }
        }
        
        get_response = {
            "data": {
                "product": {
                    "id": "gid://shopify/Product/123456789",
                    "title": "Test Product",
                    "handle": "test-product",
                    "variants": {
                        "edges": []
                    }
                }
            }
        }
        
        update_response = {
            "data": {
                "productUpdate": {
                    "product": {
                        "id": "gid://shopify/Product/123456789",
                        "title": "Updated Product",
                        "handle": "test-product"
                    },
                    "userErrors": []
                }
            }
        }
        
        list_response = {
            "data": {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/Product/123456789",
                                "title": "Updated Product",
                                "handle": "test-product"
                            },
                            "cursor": "eyJ0aXRsZSI6IlRlc3QgUHJvZHVjdCJ9"
                        }
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False
                    }
                }
            }
        }
        
        # Configure mock to return different responses for each call
        mock_post.side_effect = [
            Mock(json=Mock(return_value=create_response), status_code=200),
            Mock(json=Mock(return_value=get_response), status_code=200),
            Mock(json=Mock(return_value=update_response), status_code=200),
            Mock(json=Mock(return_value=list_response), status_code=200)
        ]
        
        # 1. Create a product
        created_product = self.products.create({
            "title": "Test Product",
            "productType": "Widget"
        })
        
        self.assertEqual(created_product["productCreate"]["product"]["title"], "Test Product")
        
        # 2. Get the created product
        product_id = created_product["productCreate"]["product"]["id"]
        retrieved_product = self.products.get(product_id)
        
        self.assertEqual(retrieved_product["product"]["id"], product_id)
        
        # 3. Update the product
        updated_product = self.products.update(product_id, {
            "title": "Updated Product"
        })
        
        self.assertEqual(updated_product["productUpdate"]["product"]["title"], "Updated Product")
        
        # 4. List products to verify it appears
        products_list = self.products.list(first=10)
        
        self.assertEqual(len(products_list["products"]["edges"]), 1)
        self.assertEqual(products_list["products"]["edges"][0]["node"]["title"], "Updated Product")
        
        # Verify all HTTP calls were made
        self.assertEqual(mock_post.call_count, 4)
    
    @patch('requests.post')
    def test_pagination_workflow(self, mock_post):
        """Test pagination workflow across multiple pages."""
        # Mock responses for pagination
        page1_response = {
            "data": {
                "products": {
                    "edges": [
                        {"node": {"id": f"gid://shopify/Product/{i}", "title": f"Product {i}"}, 
                         "cursor": f"cursor_{i}"}
                        for i in range(1, 6)
                    ],
                    "pageInfo": {
                        "hasNextPage": True,
                        "hasPreviousPage": False,
                        "startCursor": "cursor_1",
                        "endCursor": "cursor_5"
                    }
                }
            }
        }
        
        page2_response = {
            "data": {
                "products": {
                    "edges": [
                        {"node": {"id": f"gid://shopify/Product/{i}", "title": f"Product {i}"}, 
                         "cursor": f"cursor_{i}"}
                        for i in range(6, 11)
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": True,
                        "startCursor": "cursor_6",
                        "endCursor": "cursor_10"
                    }
                }
            }
        }
        
        mock_post.side_effect = [
            Mock(json=Mock(return_value=page1_response), status_code=200),
            Mock(json=Mock(return_value=page2_response), status_code=200)
        ]
        
        pagination_helper = PaginationHelper()
        all_products = []
        
        # Get first page
        first_page = self.products.list(first=5)
        products = pagination_helper.extract_nodes(first_page, "products")
        all_products.extend(products)
        
        # Check if there's a next page
        if pagination_helper.has_next_page(first_page, "products"):
            next_cursor = pagination_helper.get_next_cursor(first_page, "products")
            
            # Get second page
            second_page = self.products.list(first=5, after=next_cursor)
            products = pagination_helper.extract_nodes(second_page, "products")
            all_products.extend(products)
        
        # Verify we got all products
        self.assertEqual(len(all_products), 10)
        self.assertEqual(all_products[0]["title"], "Product 1")
        self.assertEqual(all_products[9]["title"], "Product 10")
    
    def test_query_builder_client_integration(self):
        """Test integration between QueryBuilder and Client."""
        builder = QueryBuilder()
        
        # Build a complex query
        query, variables = (builder
                          .add_variable("first", "Int!", 10)
                          .add_variable("query", "String", "title:test")
                          .add_field("""
                              products(first: $first, query: $query) {
                                  edges {
                                      node {
                                          id
                                          title
                                          handle
                                          productType
                                          variants(first: 3) {
                                              edges {
                                                  node {
                                                      id
                                                      title
                                                      price
                                                  }
                                              }
                                          }
                                      }
                                  }
                                  pageInfo {
                                      hasNextPage
                                      hasPreviousPage
                                      startCursor
                                      endCursor
                                  }
                              }
                          """)
                          .build())
        
        # Verify the query is properly formatted
        self.assertIn("query ($first: Int!, $query: String)", query)  # Note space after query
        self.assertIn("products(first: $first, query: $query)", query)
        self.assertEqual(variables["first"], 10)
        self.assertEqual(variables["query"], "title:test")
        
        # Reset and build another query
        builder.reset()
        mutation, variables = (builder
                             .add_variable("input", "ProductInput!")
                             .add_field("""
                                 productCreate(input: $input) {
                                     product {
                                         id
                                         title
                                     }
                                     userErrors {
                                         field
                                         message
                                     }
                                 }
                             """)
                             .build_mutation())
        
        self.assertIn("mutation ($input: ProductInput!)", mutation)  # Note space after mutation
        self.assertIn("productCreate(input: $input)", mutation)
    
    def test_authentication_flow(self):
        """Test authentication integration."""
        # Test API key authentication
        auth = ApiKeyAuth("test_key_123")
        headers = auth.get_headers()
        
        self.assertEqual(headers["X-Shopify-Access-Token"], "test_key_123")
        self.assertTrue(auth.is_valid())
        
        # Test client initialization with auth
        client = ShopifyClient(self.shop_url, auth.api_key)
        self.assertEqual(client.shop_url, self.shop_url)
        self.assertEqual(client.auth.api_key, "test_key_123")
    
    @patch('requests.post')
    def test_error_handling_integration(self, mock_post):
        """Test error handling integration across components."""
        # Mock a GraphQL error response
        error_response = {
            "errors": [
                {
                    "message": "Access denied",
                    "extensions": {
                        "code": "ACCESS_DENIED"
                    }
                }
            ]
        }
        
        mock_post.return_value = Mock(json=Mock(return_value=error_response), status_code=200)
        
        with self.assertRaises(ShopifyAPIError) as context:
            self.products.list(first=10)
        
        self.assertIn("GraphQL errors", str(context.exception))
    
    @patch('requests.post')
    def test_retry_integration(self, mock_post):
        """Test retry mechanism integration."""
        # Mock rate limit response, then success
        rate_limit_response = {
            "errors": [
                {
                    "message": "Throttled",
                    "extensions": {
                        "code": "THROTTLED"
                    }
                }
            ]
        }
        
        success_response = {
            "data": {
                "products": {
                    "edges": [],
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False
                    }
                }
            }
        }
        
        mock_post.side_effect = [
            Mock(json=Mock(return_value=rate_limit_response), status_code=200),
            Mock(json=Mock(return_value=success_response), status_code=200)
        ]
        
        # This should succeed after retry
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.products.list(first=10)
        
        self.assertIn("products", result)
        self.assertEqual(mock_post.call_count, 2)


class TestWebhookIntegration(unittest.TestCase):
    """Integration tests for webhook functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.webhook_secret = "test_webhook_secret_123"
        self.verifier = WebhookVerifier(self.webhook_secret)
        self.handler = WebhookHandler()
    
    def test_webhook_verification_and_handling(self):
        """Test complete webhook verification and handling workflow."""
        # Sample webhook payload
        webhook_payload = {
            "id": 12345,
            "name": "#1001",
            "created_at": "2024-01-15T10:00:00Z",
            "total_price": "100.00"
        }
        
        payload_json = json.dumps(webhook_payload)
        
        # Generate signature
        import hmac
        import hashlib
        import base64
        
        computed_hmac = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        )
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        
        # Verify signature
        is_valid = self.verifier.verify_signature(payload_json, signature)
        self.assertTrue(is_valid)
        
        # Set up event handler
        processed_events = []
        
        def handle_order_created(event_data):
            processed_events.append(event_data)
            return {"status": "processed"}
        
        self.handler.register_handler("orders/create", handle_order_created)
        
        # Handle the webhook
        result = self.handler.handle_webhook("orders/create", payload_json)
        
        self.assertEqual(result["status"], "processed")
        self.assertEqual(len(processed_events), 1)
        self.assertEqual(processed_events[0]["name"], "#1001")
    
    def test_webhook_security_integration(self):
        """Test webhook security features."""
        # Test invalid signature rejection
        invalid_payload = '{"fake": "data"}'
        fake_signature = "invalid_signature"
        
        is_valid = self.verifier.verify_signature(invalid_payload, fake_signature)
        self.assertFalse(is_valid)
        
        # Test headers verification
        headers = {
            "X-Shopify-Hmac-Sha256": fake_signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-shop.myshopify.com"
        }
        
        is_valid_request = self.verifier.verify_request(invalid_payload, headers)
        self.assertFalse(is_valid_request)


class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration management."""
    
    def test_configuration_propagation(self):
        """Test that configuration is properly propagated through components."""
        custom_config = ShopifyConfig(
            api_version="2023-10",
            timeout=60,
            max_retries=5,
            page_size=25
        )
        
        client = ShopifyClient("test-shop.myshopify.com", "test_key", config=custom_config)
        
        # Verify configuration is used in client
        self.assertEqual(client.api_version, "2023-10")
        self.assertEqual(client.config.timeout, 60)
        self.assertEqual(client.config.max_retries, 5)
        
        # Verify base URL generation
        expected_url = "https://test-shop.myshopify.com/admin/api/2023-10/graphql.json"
        self.assertEqual(client.base_url, expected_url)
    
    @patch.dict(os.environ, {"SHOPIFY_ACCESS_TOKEN": "env_token_123"})
    def test_environment_configuration(self):
        """Test configuration from environment variables."""
        from shopify.auth import from_environment
        
        auth = from_environment()
        self.assertEqual(auth.api_key, "env_token_123")
        
        client = ShopifyClient("test-shop.myshopify.com", auth.api_key)
        self.assertEqual(client.api_key, "env_token_123")


class TestConcurrencyScenarios(unittest.TestCase):
    """Tests for concurrent usage scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = ShopifyClient("test-shop.myshopify.com", "test_key")
    
    def test_multiple_resource_instances(self):
        """Test multiple resource instances with same client."""
        products1 = Products(self.client)
        products2 = Products(self.client)
        customers = Customers(self.client)
        
        # Should all share the same client instance
        self.assertIs(products1.client, products2.client)
        self.assertIs(products1.client, customers.client)
        
        # But should be independent instances
        self.assertIsNot(products1, products2)
        self.assertIsNot(products1, customers)
    
    def test_independent_client_instances(self):
        """Test that different client instances are independent."""
        client1 = ShopifyClient("shop1.myshopify.com", "key1")
        client2 = ShopifyClient("shop2.myshopify.com", "key2")
        
        products1 = Products(client1)
        products2 = Products(client2)
        
        # Should have different clients
        self.assertIsNot(products1.client, products2.client)
        self.assertEqual(products1.client.shop_url, "shop1.myshopify.com")
        self.assertEqual(products2.client.shop_url, "shop2.myshopify.com")


class TestComplexDataScenarios(unittest.TestCase):
    """Tests for complex real-world data scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = ShopifyClient("test-shop.myshopify.com", "test_key")
        self.products = Products(self.client)
    
    @patch('requests.post')
    def test_large_product_with_variants(self, mock_post):
        """Test handling products with many variants."""
        # Mock response with product containing many variants
        large_product_response = {
            "data": {
                "product": {
                    "id": "gid://shopify/Product/123456789",
                    "title": "Complex Product",
                    "variants": {
                        "edges": [
                            {
                                "node": {
                                    "id": f"gid://shopify/ProductVariant/{i}",
                                    "title": f"Variant {i}",
                                    "price": f"{i * 10}.00",
                                    "sku": f"SKU-{i}",
                                    "inventoryQuantity": i * 5
                                },
                                "cursor": f"variant_cursor_{i}"
                            }
                            for i in range(1, 51)  # 50 variants
                        ],
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False
                        }
                    }
                }
            }
        }
        
        mock_post.return_value = Mock(json=Mock(return_value=large_product_response), status_code=200)
        
        result = self.products.get("gid://shopify/Product/123456789")
        
        # Verify we can handle large data structures
        self.assertEqual(result["product"]["title"], "Complex Product")
        self.assertEqual(len(result["product"]["variants"]["edges"]), 50)
        self.assertEqual(result["product"]["variants"]["edges"][0]["node"]["title"], "Variant 1")
        self.assertEqual(result["product"]["variants"]["edges"][49]["node"]["title"], "Variant 50")
    
    def test_user_error_processing(self):
        """Test processing of complex user error scenarios."""
        # Mock complex user error response
        complex_error_result = {
            "productCreate": {
                "product": None,
                "userErrors": [
                    {
                        "field": ["input", "title"],
                        "message": "Title cannot be blank"
                    },
                    {
                        "field": ["input", "variants", "0", "price"],
                        "message": "Price must be greater than 0"
                    },
                    {
                        "field": ["input", "variants", "0", "inventoryPolicy"],
                        "message": "Inventory policy is invalid"
                    },
                    {
                        "field": ["input", "images", "0", "altText"],
                        "message": "Alt text is too long"
                    }
                ]
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.products._process_user_errors(complex_error_result, "Product creation")
        
        error_message = str(context.exception)
        self.assertIn("Product creation failed", error_message)
        self.assertIn("input.title: Title cannot be blank", error_message)
        self.assertIn("input.variants.0.price: Price must be greater than 0", error_message)
        self.assertIn("input.variants.0.inventoryPolicy: Inventory policy is invalid", error_message)
        self.assertIn("input.images.0.altText: Alt text is too long", error_message)


if __name__ == '__main__':
    unittest.main()
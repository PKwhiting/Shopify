"""
Performance and Stress Tests for Shopify SDK

Tests for performance characteristics, memory usage, and behavior under load.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import threading
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.client import ShopifyClient
from shopify.resources import Products, Customers, Orders
from shopify.query_builder import QueryBuilder
from shopify.config import ShopifyConfig
from shopify.utils.pagination import PaginationHelper
from shopify.webhooks import WebhookHandler
from shopify.utils.retry import RetryHandler


class TestPerformance(unittest.TestCase):
    """Performance tests for SDK components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ShopifyConfig(timeout=30, max_retries=2)
        self.client = ShopifyClient("test-shop.myshopify.com", "test_key", config=self.config)
        self.products = Products(self.client)
    
    def test_query_builder_performance(self):
        """Test QueryBuilder performance with complex queries."""
        builder = QueryBuilder()
        
        start_time = time.time()
        
        # Build 100 complex queries
        for i in range(100):
            builder.reset()
            query, variables = (builder
                              .add_variable("first", "Int!", 50)
                              .add_variable("query", "String", f"title:test{i}")
                              .add_variable("sortBy", "ProductSortKeys", "TITLE")
                              .add_field(f"""
                                  products(first: $first, query: $query, sortBy: $sortBy) {{
                                      edges {{
                                          node {{
                                              id
                                              title
                                              handle
                                              productType
                                              vendor
                                              tags
                                              createdAt
                                              updatedAt
                                              variants(first: 10) {{
                                                  edges {{
                                                      node {{
                                                          id
                                                          title
                                                          price
                                                          compareAtPrice
                                                          sku
                                                          barcode
                                                          inventoryQuantity
                                                      }}
                                                  }}
                                              }}
                                              images(first: 5) {{
                                                  edges {{
                                                      node {{
                                                          id
                                                          url
                                                          altText
                                                          width
                                                          height
                                                      }}
                                                  }}
                                              }}
                                          }}
                                      }}
                                      pageInfo {{
                                          hasNextPage
                                          hasPreviousPage
                                          startCursor
                                          endCursor
                                      }}
                                  }}
                              """)
                              .build())
            
            # Verify the query was built correctly
            self.assertIn("products(first: $first", query)
            self.assertEqual(variables["first"], 50)
            self.assertEqual(variables["query"], f"title:test{i}")
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Should be able to build 100 complex queries in under 1 second
        self.assertLess(elapsed_time, 1.0, f"Query building took {elapsed_time:.3f}s, expected < 1.0s")
        
        # Average time per query should be reasonable
        avg_time = elapsed_time / 100
        self.assertLess(avg_time, 0.01, f"Average query build time {avg_time:.6f}s, expected < 0.01s")
    
    def test_pagination_helper_performance(self):
        """Test PaginationHelper performance with large datasets."""
        pagination_helper = PaginationHelper()
        
        # Create mock data with many pages
        large_dataset = {
            "products": {
                "edges": [
                    {
                        "node": {
                            "id": f"gid://shopify/Product/{i}",
                            "title": f"Product {i}",
                            "handle": f"product-{i}",
                            "productType": f"Type {i % 10}",
                            "vendor": f"Vendor {i % 5}",
                            "tags": [f"tag{j}" for j in range(5)],
                            "variants": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": f"gid://shopify/ProductVariant/{i}_{j}",
                                            "title": f"Variant {j}",
                                            "price": f"{j * 10}.00"
                                        }
                                    } for j in range(3)
                                ]
                            }
                        },
                        "cursor": f"cursor_{i}"
                    }
                    for i in range(1000)  # 1000 products
                ],
                "pageInfo": {
                    "hasNextPage": True,
                    "hasPreviousPage": False,
                    "startCursor": "cursor_1",
                    "endCursor": "cursor_1000"
                }
            }
        }
        
        start_time = time.time()
        
        # Extract nodes 100 times
        for _ in range(100):
            nodes = pagination_helper.extract_nodes(large_dataset, "products")
            self.assertEqual(len(nodes), 1000)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Should be able to extract nodes 100 times in under 1 second
        self.assertLess(elapsed_time, 1.0, f"Node extraction took {elapsed_time:.3f}s, expected < 1.0s")
    
    @patch('requests.post')
    def test_client_request_performance(self, mock_post):
        """Test client request performance."""
        # Mock a typical response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "products": {
                    "edges": [
                        {
                            "node": {"id": f"gid://shopify/Product/{i}", "title": f"Product {i}"}
                        }
                        for i in range(50)
                    ],
                    "pageInfo": {"hasNextPage": False}
                }
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        start_time = time.time()
        
        # Make 50 requests
        for i in range(50):
            self.products.list(first=10)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Should complete 50 mocked requests quickly (mainly testing SDK overhead)
        self.assertLess(elapsed_time, 0.5, f"50 requests took {elapsed_time:.3f}s, expected < 0.5s")
        
        # Verify all requests were made
        self.assertEqual(mock_post.call_count, 50)


class TestConcurrency(unittest.TestCase):
    """Concurrency and thread safety tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = ShopifyClient("test-shop.myshopify.com", "test_key")
    
    def test_concurrent_resource_creation(self):
        """Test concurrent creation of resource instances."""
        results = []
        errors = []
        
        def create_resource(resource_type):
            try:
                if resource_type == "products":
                    resource = Products(self.client)
                elif resource_type == "customers":
                    resource = Customers(self.client)
                else:
                    resource = Orders(self.client)
                
                results.append((resource_type, resource))
            except Exception as e:
                errors.append((resource_type, e))
        
        # Create resources concurrently
        threads = []
        resource_types = ["products", "customers", "orders"] * 10  # 30 total
        
        for resource_type in resource_types:
            thread = threading.Thread(target=create_resource, args=(resource_type,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 30)
        
        # Verify all resources share the same client
        for resource_type, resource in results:
            self.assertEqual(resource.client, self.client)
    
    @patch('requests.post')
    def test_concurrent_requests(self, mock_post):
        """Test concurrent API requests."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"products": {"edges": [], "pageInfo": {"hasNextPage": False}}}
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        products = Products(self.client)
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                result = products.list(first=10)
                results.append((request_id, result))
            except Exception as e:
                errors.append((request_id, e))
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            
            for future in as_completed(futures):
                future.result()  # Wait for completion
        
        # Should have no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 50)
        self.assertEqual(mock_post.call_count, 50)
    
    def test_concurrent_query_building(self):
        """Test concurrent query building."""
        results = []
        errors = []
        
        def build_query(query_id):
            try:
                builder = QueryBuilder()
                query, variables = (builder
                                  .add_variable("first", "Int!", query_id)
                                  .add_field(f"products(first: $first) {{ edges {{ node {{ id title }} }} }}")
                                  .build())
                
                results.append((query_id, query, variables))
            except Exception as e:
                errors.append((query_id, e))
        
        # Build queries concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(build_query, i) for i in range(1, 101)]
            
            for future in as_completed(futures):
                future.result()
        
        # Should have no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 100)
        
        # Verify each query is unique
        queries = set()
        for query_id, query, variables in results:
            self.assertNotIn(query, queries, f"Duplicate query found for ID {query_id}")
            queries.add(query)
            self.assertEqual(variables["first"], query_id)
    
    def test_webhook_handler_concurrency(self):
        """Test webhook handler under concurrent load."""
        handler = WebhookHandler()
        results = []
        errors = []
        
        def process_webhook(event_data):
            results.append(event_data)
            return {"status": "processed", "id": event_data["id"]}
        
        # Register handler
        handler.register_handler("orders/create", process_webhook)
        
        def handle_webhook(webhook_id):
            try:
                payload = f'{{"id": {webhook_id}, "name": "Order #{webhook_id}"}}'
                result = handler.handle_webhook("orders/create", payload)
                results.append(("handled", webhook_id, result))
            except Exception as e:
                errors.append(("error", webhook_id, e))
        
        # Handle webhooks concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(handle_webhook, i) for i in range(100)]
            
            for future in as_completed(futures):
                future.result()
        
        # Should have no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        
        # Should have processed all webhooks
        handled_results = [r for r in results if r[0] == "handled"]
        self.assertEqual(len(handled_results), 100)


class TestMemoryUsage(unittest.TestCase):
    """Memory usage and resource management tests."""
    
    def test_large_query_response_handling(self):
        """Test handling of large query responses."""
        # Create a large mock response
        large_response = {
            "data": {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": f"gid://shopify/Product/{i}",
                                "title": f"Product {i}" * 50,  # Long titles
                                "description": "A" * 1000,  # 1KB description per product
                                "handle": f"product-{i}",
                                "productType": f"Type {i % 100}",
                                "vendor": f"Vendor {i % 50}",
                                "tags": [f"tag{j}" for j in range(20)],  # 20 tags per product
                                "variants": {
                                    "edges": [
                                        {
                                            "node": {
                                                "id": f"gid://shopify/ProductVariant/{i}_{j}",
                                                "title": f"Variant {j}",
                                                "price": f"{j * 10}.00",
                                                "sku": f"SKU-{i}-{j}",
                                                "barcode": f"123456789{i}{j}",
                                            }
                                        } for j in range(10)  # 10 variants per product
                                    ]
                                },
                                "images": {
                                    "edges": [
                                        {
                                            "node": {
                                                "id": f"gid://shopify/ProductImage/{i}_{k}",
                                                "url": f"https://example.com/image_{i}_{k}.jpg",
                                                "altText": f"Image {k} for product {i}",
                                            }
                                        } for k in range(5)  # 5 images per product
                                    ]
                                }
                            },
                            "cursor": f"cursor_{i}"
                        }
                        for i in range(250)  # Maximum page size
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False
                    }
                }
            }
        }
        
        # Test that we can handle this large response
        pagination_helper = PaginationHelper()
        
        # Extract nodes multiple times
        for _ in range(10):
            nodes = pagination_helper.extract_nodes(large_response, "products")
            self.assertEqual(len(nodes), 250)
            
            # Verify data integrity
            self.assertEqual(nodes[0]["id"], "gid://shopify/Product/0")
            self.assertEqual(nodes[249]["id"], "gid://shopify/Product/249")
            self.assertEqual(len(nodes[0]["variants"]["edges"]), 10)
            self.assertEqual(len(nodes[0]["images"]["edges"]), 5)
        
        # Force garbage collection
        gc.collect()
    
    def test_memory_cleanup_after_operations(self):
        """Test that memory is properly cleaned up after operations."""
        initial_objects = len(gc.get_objects())
        
        # Perform many operations
        for i in range(100):
            client = ShopifyClient(f"shop{i}.myshopify.com", f"key{i}")
            products = Products(client)
            
            builder = QueryBuilder()
            query, variables = builder.add_field("products { edges { node { id } } }").build()
            
            # Reset builder
            builder.reset()
        
        # Force garbage collection
        gc.collect()
        
        final_objects = len(gc.get_objects())
        
        # The number of objects shouldn't grow excessively
        # Allow for some growth but not proportional to the loop count
        object_growth = final_objects - initial_objects
        self.assertLess(object_growth, 1000, f"Memory leak detected: {object_growth} new objects")
    
    def test_configuration_memory_usage(self):
        """Test memory usage of configuration objects."""
        configs = []
        
        # Create many configuration instances
        for i in range(1000):
            config = ShopifyConfig(
                timeout=30 + (i % 10),
                max_retries=i % 5,
                page_size=10 + (i % 20)
            )
            configs.append(config)
        
        # Should be able to create many configs without excessive memory usage
        self.assertEqual(len(configs), 1000)
        
        # Verify configurations are independent
        for i, config in enumerate(configs[:100]):  # Check first 100
            expected_timeout = 30 + (i % 10)
            self.assertEqual(config.timeout, expected_timeout)


class TestStressScenarios(unittest.TestCase):
    """Stress tests for edge cases and high load scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ShopifyConfig(max_retries=1, retry_delay=1)  # Fast for testing
        self.retry_handler = RetryHandler(self.config)
    
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_retry_handler_stress(self, mock_sleep):
        """Test retry handler under stress conditions."""
        call_counts = []
        
        def failing_function(attempt_id):
            if attempt_id not in call_counts:
                call_counts.append(attempt_id)
            
            # Fail on first attempt, succeed on second
            if len([c for c in call_counts if c == attempt_id]) == 1:
                raise requests.exceptions.Timeout("Timeout")
            return f"success_{attempt_id}"
        
        results = []
        errors = []
        
        def test_retry(attempt_id):
            try:
                result = self.retry_handler.execute_with_retry(failing_function, attempt_id)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Test many concurrent retry operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(test_retry, i) for i in range(50)]
            
            for future in as_completed(futures):
                future.result()
        
        # Should have no errors (all should succeed on retry)
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 50)
        
        # All should be successful
        for i, result in enumerate(sorted(results)):
            self.assertEqual(result, f"success_{i}")
    
    def test_deep_nested_data_processing(self):
        """Test processing of deeply nested data structures."""
        # Create deeply nested structure
        deep_structure = {
            "data": {
                "products": {
                    "edges": []
                }
            }
        }
        
        # Add products with deep nesting
        for i in range(50):
            product = {
                "node": {
                    "id": f"gid://shopify/Product/{i}",
                    "title": f"Product {i}",
                    "variants": {
                        "edges": []
                    },
                    "metafields": {
                        "edges": []
                    }
                },
                "cursor": f"cursor_{i}"
            }
            
            # Add nested variants
            for j in range(10):
                variant = {
                    "node": {
                        "id": f"gid://shopify/ProductVariant/{i}_{j}",
                        "title": f"Variant {j}",
                        "metafields": {
                            "edges": [
                                {
                                    "node": {
                                        "id": f"gid://shopify/Metafield/{i}_{j}_{k}",
                                        "key": f"key_{k}",
                                        "value": f"value_{k}" * 100  # Long values
                                    }
                                }
                                for k in range(5)  # 5 metafields per variant
                            ]
                        }
                    },
                    "cursor": f"variant_cursor_{i}_{j}"
                }
                product["node"]["variants"]["edges"].append(variant)
            
            # Add product metafields
            for m in range(3):
                metafield = {
                    "node": {
                        "id": f"gid://shopify/Metafield/{i}_{m}",
                        "key": f"product_key_{m}",
                        "value": {
                            "nested": {
                                "deeply": {
                                    "buried": {
                                        "data": f"value_{i}_{m}" * 50
                                    }
                                }
                            }
                        }
                    },
                    "cursor": f"metafield_cursor_{i}_{m}"
                }
                product["node"]["metafields"]["edges"].append(metafield)
            
            deep_structure["data"]["products"]["edges"].append(product)
        
        # Test that pagination helper can handle deep structures
        pagination_helper = PaginationHelper()
        nodes = pagination_helper.extract_nodes(deep_structure, "products")
        
        self.assertEqual(len(nodes), 50)
        self.assertEqual(len(nodes[0]["variants"]["edges"]), 10)
        self.assertEqual(len(nodes[0]["metafields"]["edges"]), 3)
        self.assertEqual(len(nodes[0]["variants"]["edges"][0]["node"]["metafields"]["edges"]), 5)
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        special_data = {
            "data": {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": f"gid://shopify/Product/{i}",
                                "title": f"Product {i} 🛍️ 中文 العربية ñoño",
                                "description": "Special chars: !@#$%^&*(){}[]|\\:;\"'<>,.?/~`",
                                "handle": f"product-{i}-émojis-🚀",
                                "tags": ["tag with spaces", "中文标签", "العربية", "emoji🎉"],
                                "variants": {
                                    "edges": [
                                        {
                                            "node": {
                                                "id": f"gid://shopify/ProductVariant/{i}_0",
                                                "title": "Variant with unicode: αβγδε ∑∞≠≈π",
                                                "sku": f"SKU-{i}-πα",
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                        for i in range(20)
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False
                    }
                }
            }
        }
        
        # Test that special characters are handled correctly
        pagination_helper = PaginationHelper()
        nodes = pagination_helper.extract_nodes(special_data, "products")
        
        self.assertEqual(len(nodes), 20)
        self.assertIn("🛍️", nodes[0]["title"])
        self.assertIn("中文", nodes[0]["title"])
        self.assertIn("العربية", nodes[0]["title"])
        self.assertIn("Special chars:", nodes[0]["description"])
        self.assertIn("emoji🎉", nodes[0]["tags"])


if __name__ == '__main__':
    unittest.main()
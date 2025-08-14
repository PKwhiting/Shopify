"""
Test Product Class

Unit tests for the simplified Product interface.
"""

import unittest
from unittest.mock import Mock, patch
from shopify.product import Product
from shopify.client import ShopifyClient


class TestProduct(unittest.TestCase):
    """Test cases for Product class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=ShopifyClient)
        # Clear the publications cache before each test
        Product._publications_cache.clear()
        self.sample_product_data = {
            'id': 'gid://shopify/Product/123456789',
            'title': 'Test Product',
            'handle': 'test-product',
            'status': 'DRAFT',
            'createdAt': '2023-01-01T00:00:00Z',
            'updatedAt': '2023-01-01T00:00:00Z',
            'productType': 'Test Type',
            'vendor': 'Test Vendor',
            'tags': ['test', 'sample'],
            'description': 'Test description',
            'variants': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/ProductVariant/987654321',
                            'title': 'Default Title',
                            'sku': 'TEST-001',
                            'price': '10.00',
                            'inventoryQuantity': 100
                        }
                    }
                ]
            },
            'images': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/ProductImage/111111111',
                            'src': 'https://example.com/image.jpg',
                            'altText': 'Test image'
                        }
                    }
                ]
            }
        }
    
    def tearDown(self):
        """Clean up after each test."""
        # Clear the publications cache after each test
        Product._publications_cache.clear()
    
    def test_product_initialization(self):
        """Test product initialization."""
        product = Product(self.mock_client, self.sample_product_data)
        
        self.assertEqual(product.id, 'gid://shopify/Product/123456789')
        self.assertEqual(product.title, 'Test Product')
        self.assertEqual(product.handle, 'test-product')
        self.assertEqual(product.status, 'DRAFT')
        self.assertEqual(product.description, 'Test description')
        self.assertEqual(product.product_type, 'Test Type')
        self.assertEqual(product.vendor, 'Test Vendor')
        self.assertEqual(product.tags, ['test', 'sample'])
        self.assertFalse(product.is_published)
        self.assertFalse(product._dirty)
    
    def test_product_properties(self):
        """Test product property getters and setters."""
        product = Product(self.mock_client, self.sample_product_data)
        
        # Test setters mark product as dirty
        product.title = 'Updated Title'
        self.assertTrue(product._dirty)
        self.assertEqual(product.title, 'Updated Title')
        
        product.description = 'Updated description'
        self.assertEqual(product.description, 'Updated description')
        
        product.tags = ['updated', 'tags']
        self.assertEqual(product.tags, ['updated', 'tags'])
    
    def test_product_variants_and_images(self):
        """Test variants and images properties."""
        product = Product(self.mock_client, self.sample_product_data)
        
        variants = product.variants
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0]['id'], 'gid://shopify/ProductVariant/987654321')
        
        images = product.images
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['src'], 'https://example.com/image.jpg')
    
    def test_product_is_published(self):
        """Test is_published property."""
        # Test draft product
        product = Product(self.mock_client, self.sample_product_data)
        self.assertFalse(product.is_published)
        
        # Test active product
        active_data = self.sample_product_data.copy()
        active_data['status'] = 'ACTIVE'
        active_product = Product(self.mock_client, active_data)
        self.assertTrue(active_product.is_published)
    
    def test_search_classmethod(self):
        """Test Product.search() classmethod."""
        mock_response = {
            'products': {
                'edges': [
                    {'node': self.sample_product_data}
                ]
            }
        }
        self.mock_client.execute_query.return_value = mock_response
        
        products = Product.search(self.mock_client, query="test", first=5)
        
        self.assertEqual(len(products), 1)
        self.assertIsInstance(products[0], Product)
        self.assertEqual(products[0].title, 'Test Product')
        
        # Verify query was called correctly
        self.mock_client.execute_query.assert_called_once()
        call_args = self.mock_client.execute_query.call_args
        self.assertIn('searchProducts', call_args[0][0])
        self.assertEqual(call_args[0][1]['first'], 5)
        self.assertEqual(call_args[0][1]['query'], 'test')
    
    def test_search_with_filters(self):
        """Test Product.search() with filters."""
        mock_response = {
            'data': {
                'products': {
                    'edges': [
                        {'node': self.sample_product_data}
                    ]
                }
            }
        }
        self.mock_client.execute_query.return_value = mock_response
        
        filters = {
            'product_type': 'Electronics',
            'vendor': 'Apple',
            'status': 'active'
        }
        
        products = Product.search(self.mock_client, filters=filters)
        
        # Verify the query includes the filters
        call_args = self.mock_client.execute_query.call_args
        query_string = call_args[0][1]['query']
        self.assertIn('product_type:Electronics', query_string)
        self.assertIn('vendor:Apple', query_string)
        self.assertIn('status:active', query_string)
    
    def test_search_validation_errors(self):
        """Test Product.search() validation errors."""
        with self.assertRaises(ValueError):
            Product.search(self.mock_client, first=0)
        
        with self.assertRaises(ValueError):
            Product.search(self.mock_client, first=300)
    
    def test_get_classmethod(self):
        """Test Product.get() classmethod."""
        mock_response = {
            'product': self.sample_product_data
        }
        self.mock_client.execute_query.return_value = mock_response
        
        product = Product.get(self.mock_client, 'gid://shopify/Product/123456789')
        
        self.assertIsInstance(product, Product)
        self.assertEqual(product.id, 'gid://shopify/Product/123456789')
        
        # Verify query was called correctly
        self.mock_client.execute_query.assert_called_once()
        call_args = self.mock_client.execute_query.call_args
        self.assertIn('getProduct', call_args[0][0])
        self.assertEqual(call_args[0][1]['id'], 'gid://shopify/Product/123456789')
    
    def test_get_not_found(self):
        """Test Product.get() when product not found."""
        mock_response = {
            'data': {
                'product': None
            }
        }
        self.mock_client.execute_query.return_value = mock_response
        
        product = Product.get(self.mock_client, 'gid://shopify/Product/nonexistent')
        
        self.assertIsNone(product)
    
    def test_get_validation_errors(self):
        """Test Product.get() validation errors."""
        with self.assertRaises(ValueError):
            Product.get(self.mock_client, "")
        
        with self.assertRaises(ValueError):
            Product.get(self.mock_client, None)
    
    def test_get_by_handle_classmethod(self):
        """Test Product.get_by_handle() classmethod."""
        mock_response = {
            'productByHandle': self.sample_product_data
        }
        self.mock_client.execute_query.return_value = mock_response
        
        product = Product.get_by_handle(self.mock_client, 'test-product')
        
        self.assertIsInstance(product, Product)
        self.assertEqual(product.handle, 'test-product')
        
        # Verify query was called correctly
        self.mock_client.execute_query.assert_called_once()
        call_args = self.mock_client.execute_query.call_args
        self.assertIn('getProductByHandle', call_args[0][0])
        self.assertEqual(call_args[0][1]['handle'], 'test-product')
    
    def test_create_classmethod(self):
        """Test Product.create() classmethod."""
        mock_response = {
            'productCreate': {
                'product': self.sample_product_data,
                'userErrors': []
            }
        }
        self.mock_client.execute_mutation.return_value = mock_response
        
        product_data = {
            'title': 'New Product',
            'description': 'New product description'
        }
        
        product = Product.create(self.mock_client, product_data)
        
        self.assertIsInstance(product, Product)
        self.assertEqual(product.title, 'Test Product')
        
        # Verify mutation was called correctly
        self.mock_client.execute_mutation.assert_called_once()
        call_args = self.mock_client.execute_mutation.call_args
        self.assertIn('productCreate', call_args[0][0])
        self.assertEqual(call_args[0][1]['input'], product_data)
    
    def test_create_with_user_errors(self):
        """Test Product.create() with user errors."""
        mock_response = {
            'productCreate': {
                'product': None,
                'userErrors': [
                    {'field': ['title'], 'message': 'Title is required'}
                ]
            }
        }
        self.mock_client.execute_mutation.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            Product.create(self.mock_client, {'description': 'test'})
        
        self.assertIn('Title is required', str(context.exception))
    
    def test_create_validation_errors(self):
        """Test Product.create() validation errors."""
        with self.assertRaises(ValueError):
            Product.create(self.mock_client, "not a dict")
        
        with self.assertRaises(ValueError):
            Product.create(self.mock_client, {})
    
    def test_save_method(self):
        """Test product.save() method."""
        product = Product(self.mock_client, self.sample_product_data)
        
        # Modify product
        product.title = 'Updated Title'
        product.description = 'Updated description'
        
        mock_response = {
            'data': {
                'productUpdate': {
                    'product': {
                        'id': 'gid://shopify/Product/123456789',
                        'title': 'Updated Title',
                        'description': 'Updated description',
                        'updatedAt': '2023-01-02T00:00:00Z'
                    },
                    'userErrors': []
                }
            }
        }
        self.mock_client.execute_mutation.return_value = mock_response
        
        updated_product = product.save()
        
        self.assertEqual(updated_product, product)
        self.assertEqual(product.title, 'Updated Title')
        self.assertFalse(product._dirty)
        
        # Verify mutation was called correctly
        self.mock_client.execute_mutation.assert_called_once()
        call_args = self.mock_client.execute_mutation.call_args
        self.assertIn('productUpdate', call_args[0][0])
        
        input_data = call_args[0][1]['input']
        self.assertEqual(input_data['id'], 'gid://shopify/Product/123456789')
        self.assertEqual(input_data['title'], 'Updated Title')
        self.assertEqual(input_data['description'], 'Updated description')
    
    def test_save_no_changes(self):
        """Test product.save() when no changes made."""
        product = Product(self.mock_client, self.sample_product_data)
        
        result = product.save()
        
        self.assertEqual(result, product)
        self.mock_client.execute_mutation.assert_not_called()
    
    def test_save_without_id(self):
        """Test product.save() without ID."""
        data_without_id = self.sample_product_data.copy()
        del data_without_id['id']
        product = Product(self.mock_client, data_without_id)
        
        with self.assertRaises(ValueError):
            product.save()
    
    def test_delete_method(self):
        """Test product.delete() method."""
        product = Product(self.mock_client, self.sample_product_data)
        
        mock_response = {
            'productDelete': {
                'deletedProductId': 'gid://shopify/Product/123456789',
                'userErrors': []
            }
        }
        self.mock_client.execute_mutation.return_value = mock_response
        
        result = product.delete()
        
        self.assertTrue(result)
        
        # Verify mutation was called correctly
        self.mock_client.execute_mutation.assert_called_once()
        call_args = self.mock_client.execute_mutation.call_args
        self.assertIn('productDelete', call_args[0][0])
        self.assertEqual(call_args[0][1]['input']['id'], 'gid://shopify/Product/123456789')
    
    def test_delete_without_id(self):
        """Test product.delete() without ID."""
        data_without_id = self.sample_product_data.copy()
        del data_without_id['id']
        product = Product(self.mock_client, data_without_id)
        
        with self.assertRaises(ValueError):
            product.delete()
    
    def test_publish_method(self):
        """Test product.publish() method."""
        product = Product(self.mock_client, self.sample_product_data)
        
        mock_response = {
            'data': {
                'publishablePublish': {
                    'publishable': {
                        'id': 'gid://shopify/Product/123456789',
                        'status': 'ACTIVE',
                        'publishedAt': '2023-01-01T00:00:00Z'
                    },
                    'userErrors': []
                }
            }
        }
        self.mock_client.execute_mutation.return_value = mock_response
        
        result = product.publish()
        
        self.assertEqual(result, product)
        self.assertEqual(product.status, 'ACTIVE')
        
        # Verify mutation was called correctly
        self.mock_client.execute_mutation.assert_called_once()
        call_args = self.mock_client.execute_mutation.call_args
        self.assertIn('publishablePublish', call_args[0][0])
        self.assertEqual(call_args[0][1]['id'], 'gid://shopify/Product/123456789')
    
    def test_unpublish_method(self):
        """Test product.unpublish() method."""
        active_data = self.sample_product_data.copy()
        active_data['status'] = 'ACTIVE'
        product = Product(self.mock_client, active_data)
        
        mock_response = {
            'data': {
                'publishableUnpublish': {
                    'publishable': {
                        'id': 'gid://shopify/Product/123456789',
                        'status': 'DRAFT'
                    },
                    'userErrors': []
                }
            }
        }
        self.mock_client.execute_mutation.return_value = mock_response
        
        result = product.unpublish()
        
        self.assertEqual(result, product)
        self.assertEqual(product.status, 'DRAFT')
        
        # Verify mutation was called correctly
        self.mock_client.execute_mutation.assert_called_once()
        call_args = self.mock_client.execute_mutation.call_args
        self.assertIn('publishableUnpublish', call_args[0][0])
        self.assertEqual(call_args[0][1]['id'], 'gid://shopify/Product/123456789')
    
    def test_get_store_publications(self):
        """Test _get_store_publications method."""
        product = Product(self.mock_client, self.sample_product_data)
        self.mock_client.shop_url = 'test-shop.myshopify.com'
        
        mock_response = {
            'publications': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/123',
                            'name': 'Online Store',
                            'supportsFuturePublishing': True
                        }
                    },
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/456',
                            'name': 'Point of Sale',
                            'supportsFuturePublishing': False
                        }
                    }
                ]
            }
        }
        self.mock_client.execute_query.return_value = mock_response
        
        publications = product._get_store_publications()
        
        self.assertEqual(len(publications), 2)
        # Check that both publications are present (order doesn't matter)
        pub_ids = [pub['id'] for pub in publications]
        self.assertIn('gid://shopify/Publication/123', pub_ids)
        self.assertIn('gid://shopify/Publication/456', pub_ids)
        
        # Verify query was called correctly
        self.mock_client.execute_query.assert_called_once()
        call_args = self.mock_client.execute_query.call_args
        self.assertIn('getPublications', call_args[0][0])
    
    def test_get_store_publications_caching(self):
        """Test that publications are cached properly."""
        product = Product(self.mock_client, self.sample_product_data)
        self.mock_client.shop_url = 'test-shop.myshopify.com'
        
        mock_response = {
            'publications': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/123',
                            'name': 'Online Store',
                            'supportsFuturePublishing': True
                        }
                    }
                ]
            }
        }
        self.mock_client.execute_query.return_value = mock_response
        
        # First call
        publications1 = product._get_store_publications()
        # Second call should use cache
        publications2 = product._get_store_publications()
        
        self.assertEqual(publications1, publications2)
        # Should only be called once due to caching
        self.mock_client.execute_query.assert_called_once()
    
    def test_get_default_publication_web(self):
        """Test _get_default_publication returns web publication."""
        product = Product(self.mock_client, self.sample_product_data)
        self.mock_client.shop_url = 'test-shop.myshopify.com'
        
        mock_response = {
            'publications': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/456',
                            'name': 'Point of Sale',
                            'supportsFuturePublishing': False
                        }
                    },
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/123',
                            'name': 'Online Store Web',
                            'supportsFuturePublishing': True
                        }
                    }
                ]
            }
        }
        self.mock_client.execute_query.return_value = mock_response
        
        default_pub = product._get_default_publication()
        
        # Should prefer the web publication
        self.assertIsNotNone(default_pub)
        self.assertEqual(default_pub['id'], 'gid://shopify/Publication/123')
        self.assertIn('web', default_pub['name'].lower())
    
    def test_get_default_publication_first_available(self):
        """Test _get_default_publication returns first publication when no web found."""
        product = Product(self.mock_client, self.sample_product_data)
        self.mock_client.shop_url = 'test-shop.myshopify.com'
        
        mock_response = {
            'publications': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/456',
                            'name': 'Point of Sale',
                            'supportsFuturePublishing': False
                        }
                    },
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/789',
                            'name': 'Facebook',
                            'supportsFuturePublishing': True
                        }
                    }
                ]
            }
        }
        self.mock_client.execute_query.return_value = mock_response
        
        default_pub = product._get_default_publication()
        
        # Should return first publication since no web publication found
        self.assertIsNotNone(default_pub)
        self.assertEqual(default_pub['id'], 'gid://shopify/Publication/456')
    
    def test_publish_with_dynamic_publication_lookup(self):
        """Test publish method uses dynamic publication lookup when none specified."""
        product = Product(self.mock_client, self.sample_product_data)
        self.mock_client.shop_url = 'test-shop.myshopify.com'
        
        # Mock publications query response
        publications_response = {
            'publications': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/123',
                            'name': 'Online Store',
                            'supportsFuturePublishing': True
                        }
                    }
                ]
            }
        }
        
        # Mock publish mutation response
        publish_response = {
            'data': {
                'publishablePublish': {
                    'publishable': {
                        'id': 'gid://shopify/Product/123456789',
                        'status': 'ACTIVE',
                        'publishedAt': '2023-01-01T00:00:00Z'
                    },
                    'userErrors': []
                }
            }
        }
        
        self.mock_client.execute_query.return_value = publications_response
        self.mock_client.execute_mutation.return_value = publish_response
        
        result = product.publish()
        
        self.assertEqual(result, product)
        self.assertEqual(product.status, 'ACTIVE')
        
        # Verify both queries were called
        self.mock_client.execute_query.assert_called_once()
        self.mock_client.execute_mutation.assert_called_once()
        
        # Check that the dynamic publication ID was used
        mutation_call_args = self.mock_client.execute_mutation.call_args
        publication_input = mutation_call_args[0][1]['input']
        self.assertEqual(publication_input[0]['publicationId'], 'gid://shopify/Publication/123')
    
    def test_unpublish_with_dynamic_publication_lookup(self):
        """Test unpublish method uses dynamic publication lookup when none specified."""
        active_data = self.sample_product_data.copy()
        active_data['status'] = 'ACTIVE'
        product = Product(self.mock_client, active_data)
        self.mock_client.shop_url = 'test-shop.myshopify.com'
        
        # Mock publications query response
        publications_response = {
            'publications': {
                'edges': [
                    {
                        'node': {
                            'id': 'gid://shopify/Publication/123',
                            'name': 'Online Store',
                            'supportsFuturePublishing': True
                        }
                    }
                ]
            }
        }
        
        # Mock unpublish mutation response
        unpublish_response = {
            'data': {
                'publishableUnpublish': {
                    'publishable': {
                        'id': 'gid://shopify/Product/123456789',
                        'status': 'DRAFT'
                    },
                    'userErrors': []
                }
            }
        }
        
        self.mock_client.execute_query.return_value = publications_response
        self.mock_client.execute_mutation.return_value = unpublish_response
        
        result = product.unpublish()
        
        self.assertEqual(result, product)
        self.assertEqual(product.status, 'DRAFT')
        
        # Verify both queries were called
        self.mock_client.execute_query.assert_called_once()
        self.mock_client.execute_mutation.assert_called_once()
        
        # Check that the dynamic publication ID was used
        mutation_call_args = self.mock_client.execute_mutation.call_args
        publication_input = mutation_call_args[0][1]['input']
        self.assertEqual(publication_input[0]['publicationId'], 'gid://shopify/Publication/123')
    
    def test_duplicate_method(self):
        """Test product.duplicate() method."""
        product = Product(self.mock_client, self.sample_product_data)
        
        duplicate_data = self.sample_product_data.copy()
        duplicate_data['id'] = 'gid://shopify/Product/987654321'
        duplicate_data['title'] = 'Duplicate Product'
        
        mock_response = {
            'data': {
                'productDuplicate': {
                    'newProduct': duplicate_data,
                    'userErrors': []
                }
            }
        }
        self.mock_client.execute_mutation.return_value = mock_response
        
        duplicate = product.duplicate('Duplicate Product')
        
        self.assertIsInstance(duplicate, Product)
        self.assertEqual(duplicate.id, 'gid://shopify/Product/987654321')
        self.assertEqual(duplicate.title, 'Duplicate Product')
        self.assertNotEqual(duplicate.id, product.id)
        
        # Verify mutation was called correctly
        self.mock_client.execute_mutation.assert_called_once()
        call_args = self.mock_client.execute_mutation.call_args
        self.assertIn('productDuplicate', call_args[0][0])
        self.assertEqual(call_args[0][1]['productId'], 'gid://shopify/Product/123456789')
        self.assertEqual(call_args[0][1]['newTitle'], 'Duplicate Product')
    
    def test_string_representations(self):
        """Test string representations of product."""
        product = Product(self.mock_client, self.sample_product_data)
        
        str_repr = str(product)
        self.assertIn('Test Product', str_repr)
        self.assertIn('DRAFT', str_repr)
        
        repr_str = repr(product)
        self.assertIn('test-product', repr_str)
        self.assertIn('gid://shopify/Product/123456789', repr_str)
    
    def test_to_dict_method(self):
        """Test to_dict() method."""
        product = Product(self.mock_client, self.sample_product_data)
        
        product_dict = product.to_dict()
        
        self.assertEqual(product_dict, self.sample_product_data)
        # Ensure it's a copy, not the original
        self.assertIsNot(product_dict, product._data)


if __name__ == '__main__':
    unittest.main()
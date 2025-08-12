"""
Products Resource

Handles product-related operations via Shopify GraphQL API.
"""

from typing import Dict, Any, Optional, List
from ..query_builder import QueryBuilder


class Products:
    """Resource class for handling Shopify products."""
    
    def __init__(self, client):
        """
        Initialize Products resource.
        
        Args:
            client: ShopifyClient instance
        """
        self.client = client
    
    def list(self, first: int = 10, after: Optional[str] = None) -> Dict[str, Any]:
        """
        List products from the store.
        
        Args:
            first (int): Number of products to fetch (max 250)
            after (str, optional): Cursor for pagination
            
        Returns:
            dict: Products data with pagination info
        """
        query, variables = QueryBuilder.build_product_query(first, after)
        return self.client.execute_query(query, variables)
    
    def get(self, product_id: str) -> Dict[str, Any]:
        """
        Get a specific product by ID.
        
        Args:
            product_id (str): The product ID
            
        Returns:
            dict: Product data
        """
        query = """
        query getProduct($id: ID!) {
            product(id: $id) {
                id
                title
                handle
                status
                createdAt
                updatedAt
                productType
                vendor
                tags
                description
                variants(first: 250) {
                    edges {
                        node {
                            id
                            title
                            sku
                            price
                            inventoryQuantity
                            weight
                            weightUnit
                        }
                    }
                }
                images(first: 10) {
                    edges {
                        node {
                            id
                            src
                            altText
                            width
                            height
                        }
                    }
                }
            }
        }
        """
        variables = {"id": product_id}
        return self.client.execute_query(query, variables)
    
    def create(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product.
        
        Args:
            product_data (dict): Product data for creation
            
        Returns:
            dict: Created product data
        """
        mutation = """
        mutation productCreate($input: ProductInput!) {
            productCreate(input: $input) {
                product {
                    id
                    title
                    handle
                    status
                    createdAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {"input": product_data}
        return self.client.execute_mutation(mutation, variables)
    
    def update(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product.
        
        Args:
            product_id (str): The product ID to update
            product_data (dict): Updated product data
            
        Returns:
            dict: Updated product data
        """
        product_data["id"] = product_id
        
        mutation = """
        mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
                product {
                    id
                    title
                    handle
                    status
                    updatedAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {"input": product_data}
        return self.client.execute_mutation(mutation, variables)
    
    def delete(self, product_id: str) -> Dict[str, Any]:
        """
        Delete a product.
        
        Args:
            product_id (str): The product ID to delete
            
        Returns:
            dict: Deletion result
        """
        mutation = """
        mutation productDelete($input: ProductDeleteInput!) {
            productDelete(input: $input) {
                deletedProductId
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {"input": {"id": product_id}}
        return self.client.execute_mutation(mutation, variables)
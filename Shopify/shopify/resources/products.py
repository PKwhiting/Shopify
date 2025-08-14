"""
Products Resource

Handles product-related operations via Shopify GraphQL API.
"""

from typing import Dict, Any, Optional, List
from ..query_builder import QueryBuilder
from .base import BaseResource


class Products(BaseResource):
    """Resource class for handling Shopify products."""

    def get_resource_name(self) -> str:
        """Get the singular resource name."""
        return "product"

    def get_plural_resource_name(self) -> str:
        """Get the plural resource name."""
        return "products"

    def list(self, first: int = 10, after: Optional[str] = None) -> Dict[str, Any]:
        """
        List products from the store.

        Args:
            first (int): Number of products to fetch (max 250)
            after (str, optional): Cursor for pagination

        Returns:
            dict: Products data with pagination info

        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_pagination_params(first, after)
        query, variables = QueryBuilder.build_product_query(first, after)
        return self._execute_query_with_validation(query, variables)

    def get(self, product_id: str) -> Dict[str, Any]:
        """
        Get a specific product by ID.

        Args:
            product_id (str): The product ID

        Returns:
            dict: Product data

        Raises:
            ValueError: If product_id is invalid
        """
        product_id = self._validate_id(product_id)

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
        return self._execute_query_with_validation(query, variables)

    def create(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product.

        Args:
            product_data (dict): Product data for creation

        Returns:
            dict: Created product data

        Raises:
            ValueError: If product_data is invalid or operation fails
        """
        if not isinstance(product_data, dict):
            raise ValueError("Product data must be a dictionary")
        if not product_data:
            raise ValueError("Product data cannot be empty")

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
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Product creation")

    def update(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product.

        Args:
            product_id (str): The product ID to update
            product_data (dict): Updated product data

        Returns:
            dict: Updated product data

        Raises:
            ValueError: If parameters are invalid or operation fails
        """
        product_id = self._validate_id(product_id)

        if not isinstance(product_data, dict):
            raise ValueError("Product data must be a dictionary")
        if not product_data:
            raise ValueError("Product data cannot be empty")

        # Create a copy to avoid modifying the original
        update_data = product_data.copy()
        update_data["id"] = product_id

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
        variables = {"input": update_data}
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Product update")

    def delete(self, product_id: str) -> Dict[str, Any]:
        """
        Delete a product.

        Args:
            product_id (str): The product ID to delete

        Returns:
            dict: Deletion result

        Raises:
            ValueError: If product_id is invalid or operation fails
        """
        product_id = self._validate_id(product_id)

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
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Product deletion")

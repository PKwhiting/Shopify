"""
Base Resource Class

Provides common functionality for all Shopify resources to eliminate code duplication
and establish consistent patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import ShopifyClient


class BaseResource(ABC):
    """Base class for all Shopify resource classes."""

    def __init__(self, client: "ShopifyClient"):
        """
        Initialize base resource.

        Args:
            client: ShopifyClient instance
        """
        self.client = client
        self._validate_client()

    def _validate_client(self) -> None:
        """Validate that client is properly configured."""
        if not self.client:
            raise ValueError("Client is required")
        if not hasattr(self.client, "execute_query"):
            raise ValueError("Invalid client: missing execute_query method")

    @abstractmethod
    def get_resource_name(self) -> str:
        """
        Get the resource name for GraphQL operations.

        Returns:
            str: Resource name (e.g., 'product', 'customer', 'order')
        """
        pass

    @abstractmethod
    def get_plural_resource_name(self) -> str:
        """
        Get the plural resource name for GraphQL operations.

        Returns:
            str: Plural resource name (e.g., 'products', 'customers', 'orders')
        """
        pass

    def _execute_query_with_validation(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute query with validation.

        Args:
            query (str): GraphQL query
            variables (dict, optional): Query variables

        Returns:
            dict: Query result

        Raises:
            ValueError: If query or variables are invalid
        """
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if variables is not None and not isinstance(variables, dict):
            raise ValueError("Variables must be a dictionary")

        return self.client.execute_query(query, variables)

    def _execute_mutation_with_validation(
        self, mutation: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute mutation with validation.

        Args:
            mutation (str): GraphQL mutation
            variables (dict, optional): Mutation variables

        Returns:
            dict: Mutation result

        Raises:
            ValueError: If mutation or variables are invalid
        """
        if not mutation or not isinstance(mutation, str):
            raise ValueError("Mutation must be a non-empty string")

        if variables is not None and not isinstance(variables, dict):
            raise ValueError("Variables must be a dictionary")

        return self.client.execute_mutation(mutation, variables)

    def _validate_id(self, resource_id: str) -> str:
        """
        Validate resource ID format.

        Args:
            resource_id (str): Resource ID to validate

        Returns:
            str: Validated resource ID

        Raises:
            ValueError: If ID is invalid
        """
        if not resource_id or not isinstance(resource_id, str):
            raise ValueError(
                f"{self.get_resource_name().capitalize()} ID must be a non-empty string"
            )

        resource_id = resource_id.strip()
        if not resource_id:
            raise ValueError(
                f"{self.get_resource_name().capitalize()} ID cannot be empty or whitespace"
            )

        return resource_id

    def _validate_pagination_params(self, first: int, after: Optional[str] = None) -> None:
        """
        Validate pagination parameters.

        Args:
            first (int): Number of items to fetch
            after (str, optional): Cursor for pagination

        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(first, int) or first < 1:
            raise ValueError("'first' parameter must be a positive integer")

        if first > 250:
            raise ValueError("'first' parameter cannot exceed 250 (Shopify API limit)")

        if after is not None and (not isinstance(after, str) or not after.strip()):
            raise ValueError("'after' parameter must be a non-empty string if provided")

    def _process_user_errors(self, result: Dict[str, Any], operation_name: str) -> Dict[str, Any]:
        """
        Process and handle user errors from GraphQL mutations.

        Args:
            result (dict): GraphQL operation result
            operation_name (str): Name of the operation for error reporting

        Returns:
            dict: Processed result

        Raises:
            ValueError: If there are user errors in the result
        """
        if not isinstance(result, dict):
            return result

        # Look for user errors in the result
        for key, value in result.items():
            if isinstance(value, dict) and "userErrors" in value:
                user_errors = value["userErrors"]
                if user_errors:
                    error_messages = []
                    for error in user_errors:
                        field = error.get("field", ["unknown"])
                        message = error.get("message", "Unknown error")
                        if isinstance(field, list):
                            field_str = ".".join(field)
                        else:
                            field_str = str(field)
                        error_messages.append(f"{field_str}: {message}")

                    raise ValueError(f"{operation_name} failed: {'; '.join(error_messages)}")

        return result

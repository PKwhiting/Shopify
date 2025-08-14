"""
Pagination helper for GraphQL API

Handles cursor-based pagination for Shopify GraphQL API responses.
"""

from typing import Dict, Any, Optional, List, Iterator


class PaginationHelper:
    """Helper class for handling GraphQL cursor-based pagination."""

    def __init__(self):
        """Initialize pagination helper."""
        pass

    def get_page_info(self, data: Dict[str, Any], connection_key: str) -> Dict[str, Any]:
        """
        Extract page info from GraphQL response.

        Args:
            data (dict): GraphQL response data
            connection_key (str): Key for the connection (e.g., 'products', 'customers')

        Returns:
            dict: Page info with pagination details
        """
        if connection_key not in data:
            return {}

        connection = data[connection_key]
        return connection.get("pageInfo", {})

    def has_next_page(self, data: Dict[str, Any], connection_key: str) -> bool:
        """
        Check if there is a next page.

        Args:
            data (dict): GraphQL response data
            connection_key (str): Key for the connection

        Returns:
            bool: True if there is a next page
        """
        page_info = self.get_page_info(data, connection_key)
        return page_info.get("hasNextPage", False)

    def has_previous_page(self, data: Dict[str, Any], connection_key: str) -> bool:
        """
        Check if there is a previous page.

        Args:
            data (dict): GraphQL response data
            connection_key (str): Key for the connection

        Returns:
            bool: True if there is a previous page
        """
        page_info = self.get_page_info(data, connection_key)
        return page_info.get("hasPreviousPage", False)

    def get_next_cursor(self, data: Dict[str, Any], connection_key: str) -> Optional[str]:
        """
        Get cursor for the next page.

        Args:
            data (dict): GraphQL response data
            connection_key (str): Key for the connection

        Returns:
            str or None: Cursor for next page
        """
        page_info = self.get_page_info(data, connection_key)
        if self.has_next_page(data, connection_key):
            return page_info.get("endCursor")
        return None

    def get_previous_cursor(self, data: Dict[str, Any], connection_key: str) -> Optional[str]:
        """
        Get cursor for the previous page.

        Args:
            data (dict): GraphQL response data
            connection_key (str): Key for the connection

        Returns:
            str or None: Cursor for previous page
        """
        page_info = self.get_page_info(data, connection_key)
        if self.has_previous_page(data, connection_key):
            return page_info.get("startCursor")
        return None

    def extract_nodes(self, data: Dict[str, Any], connection_key: str) -> List[Dict[str, Any]]:
        """
        Extract node data from GraphQL edges.

        Args:
            data (dict): GraphQL response data
            connection_key (str): Key for the connection

        Returns:
            list: List of node objects
        """
        if connection_key not in data:
            return []

        connection = data[connection_key]
        edges = connection.get("edges", [])
        return [edge.get("node", {}) for edge in edges]

    def paginate_all(
        self, client, query_builder_func, connection_key: str, page_size: int = 50, **query_kwargs
    ) -> Iterator[Dict[str, Any]]:
        """
        Generator that automatically paginates through all pages.

        Args:
            client: Shopify client instance
            query_builder_func: Function to build query (e.g., QueryBuilder.build_product_query)
            connection_key (str): Key for the connection (e.g., 'products', 'customers')
            page_size (int): Number of items per page
            **query_kwargs: Additional arguments for the query builder function

        Yields:
            dict: Individual node objects

        Raises:
            ValueError: If parameters are invalid
        """
        if not client or not hasattr(client, "execute_query"):
            raise ValueError("Invalid client: must have execute_query method")

        if not callable(query_builder_func):
            raise ValueError("query_builder_func must be callable")

        if not isinstance(connection_key, str) or not connection_key.strip():
            raise ValueError("connection_key must be a non-empty string")

        if not isinstance(page_size, int) or page_size < 1:
            raise ValueError("page_size must be a positive integer")
        if page_size > 250:
            raise ValueError("page_size cannot exceed 250")

        connection_key = connection_key.strip()
        cursor = None

        while True:
            try:
                # Build query with current parameters
                query, variables = query_builder_func(first=page_size, after=cursor, **query_kwargs)

                # Execute query
                data = client.execute_query(query, variables)

                # Extract and yield nodes
                nodes = self.extract_nodes(data, connection_key)
                for node in nodes:
                    yield node

                # Check if there are more pages
                if not self.has_next_page(data, connection_key):
                    break

                # Get cursor for next page
                cursor = self.get_next_cursor(data, connection_key)
                if not cursor:
                    break

            except Exception as e:
                # Add context to any errors
                raise RuntimeError(f"Pagination error for {connection_key}: {str(e)}") from e

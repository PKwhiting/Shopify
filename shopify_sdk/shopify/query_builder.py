"""
GraphQL Query Builder

Helper class for building GraphQL queries for Shopify API.
"""

import threading
from typing import List, Dict, Any, Optional


class QueryBuilder:
    """Helper class for building GraphQL queries."""

    def __init__(self):
        """Initialize query builder."""
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> "QueryBuilder":
        """Reset the query builder to start a new query."""
        with self._lock:
            self._query_type = "query"
            self._fields = []
            self._variables = {}
            self._variable_definitions = []
        return self

    def mutation(self) -> "QueryBuilder":
        """Set the query type to mutation."""
        with self._lock:
            self._query_type = "mutation"
        return self

    def add_variable(self, name: str, var_type: str, value: Any) -> "QueryBuilder":
        """
        Add a variable to the query.

        Args:
            name (str): Variable name
            var_type (str): GraphQL type (e.g., 'String!', 'Int')
            value (Any): Variable value

        Returns:
            QueryBuilder: Self for method chaining

        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Variable name must be a non-empty string")
        if not isinstance(var_type, str) or not var_type.strip():
            raise ValueError("Variable type must be a non-empty string")

        name = name.strip()
        var_type = var_type.strip()

        with self._lock:
            self._variable_definitions.append(f"${name}: {var_type}")
            self._variables[name] = value
        return self

    def add_field(self, field: str) -> "QueryBuilder":
        """
        Add a field to the query.

        Args:
            field (str): GraphQL field

        Returns:
            QueryBuilder: Self for method chaining

        Raises:
            ValueError: If field is invalid
        """
        if not isinstance(field, str) or not field.strip():
            raise ValueError("Field must be a non-empty string")

        with self._lock:
            self._fields.append(field.strip())
        return self

    def build(self) -> tuple[str, Dict[str, Any]]:
        """
        Build the complete GraphQL query.

        Returns:
            tuple: (query_string, variables_dict)
        """
        with self._lock:
            if not self._fields:
                raise ValueError("Query must have at least one field")

            query_parts = [self._query_type]

            if self._variable_definitions:
                variables_str = ", ".join(self._variable_definitions)
                query_parts.append(f"({variables_str})")

            query_parts.append("{")
            query_parts.extend(self._fields)
            query_parts.append("}")

            query = " ".join(query_parts)
            return query, self._variables.copy()

    # Static methods for common queries (kept for backward compatibility)
    @staticmethod
    def build_product_query(
        first: int = 10, after: Optional[str] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a query to fetch products.

        Args:
            first (int): Number of products to fetch
            after (str, optional): Cursor for pagination

        Returns:
            tuple: (query_string, variables_dict)

        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(first, int) or first < 1:
            raise ValueError("'first' parameter must be a positive integer")
        if first > 250:
            raise ValueError("'first' parameter cannot exceed 250")
        if after is not None and (not isinstance(after, str) or not after.strip()):
            raise ValueError("'after' parameter must be a non-empty string if provided")

        variables = {"first": first}
        if after:
            variables["after"] = after.strip()

        query = """
        query getProducts($first: Int!, $after: String) {
            products(first: $first, after: $after) {
                edges {
                    node {
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
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """
        return query.strip(), variables

    @staticmethod
    def build_customer_query(
        first: int = 10, after: Optional[str] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a query to fetch customers.

        Args:
            first (int): Number of customers to fetch
            after (str, optional): Cursor for pagination

        Returns:
            tuple: (query_string, variables_dict)

        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(first, int) or first < 1:
            raise ValueError("'first' parameter must be a positive integer")
        if first > 250:
            raise ValueError("'first' parameter cannot exceed 250")
        if after is not None and (not isinstance(after, str) or not after.strip()):
            raise ValueError("'after' parameter must be a non-empty string if provided")

        variables = {"first": first}
        if after:
            variables["after"] = after.strip()

        query = """
        query getCustomers($first: Int!, $after: String) {
            customers(first: $first, after: $after) {
                edges {
                    node {
                        id
                        firstName
                        lastName
                        email
                        phone
                        createdAt
                        updatedAt
                        acceptsMarketing
                        state
                        note
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """
        return query.strip(), variables

    @staticmethod
    def build_order_query(
        first: int = 10, after: Optional[str] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a query to fetch orders.

        Args:
            first (int): Number of orders to fetch
            after (str, optional): Cursor for pagination

        Returns:
            tuple: (query_string, variables_dict)

        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(first, int) or first < 1:
            raise ValueError("'first' parameter must be a positive integer")
        if first > 250:
            raise ValueError("'first' parameter cannot exceed 250")
        if after is not None and (not isinstance(after, str) or not after.strip()):
            raise ValueError("'after' parameter must be a non-empty string if provided")

        variables = {"first": first}
        if after:
            variables["after"] = after.strip()

        query = """
        query getOrders($first: Int!, $after: String) {
            orders(first: $first, after: $after) {
                edges {
                    node {
                        id
                        name
                        email
                        createdAt
                        updatedAt
                        processedAt
                        financialStatus
                        fulfillmentStatus
                        totalPriceSet {
                            presentmentMoney {
                                amount
                                currencyCode
                            }
                        }
                        customer {
                            id
                            firstName
                            lastName
                            email
                        }
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """
        return query.strip(), variables

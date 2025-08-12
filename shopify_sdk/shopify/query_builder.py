"""
GraphQL Query Builder

Helper class for building GraphQL queries for Shopify API.
"""

from typing import List, Dict, Any, Optional


class QueryBuilder:
    """Helper class for building GraphQL queries."""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> 'QueryBuilder':
        """Reset the query builder to start a new query."""
        self._query_type = "query"
        self._fields = []
        self._variables = {}
        self._variable_definitions = []
        return self
    
    def mutation(self) -> 'QueryBuilder':
        """Set the query type to mutation."""
        self._query_type = "mutation"
        return self
    
    def add_variable(self, name: str, var_type: str, value: Any) -> 'QueryBuilder':
        """
        Add a variable to the query.
        
        Args:
            name (str): Variable name
            var_type (str): GraphQL type (e.g., 'String!', 'Int')
            value (Any): Variable value
        """
        self._variable_definitions.append(f"${name}: {var_type}")
        self._variables[name] = value
        return self
    
    def add_field(self, field: str) -> 'QueryBuilder':
        """Add a field to the query."""
        self._fields.append(field)
        return self
    
    def build(self) -> tuple[str, Dict[str, Any]]:
        """
        Build the complete GraphQL query.
        
        Returns:
            tuple: (query_string, variables_dict)
        """
        query_parts = [self._query_type]
        
        if self._variable_definitions:
            variables_str = ", ".join(self._variable_definitions)
            query_parts.append(f"({variables_str})")
        
        query_parts.append("{")
        query_parts.extend(self._fields)
        query_parts.append("}")
        
        query = " ".join(query_parts)
        return query, self._variables
    
    @staticmethod
    def build_product_query(first: int = 10, after: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Build a query to fetch products.
        
        Args:
            first (int): Number of products to fetch
            after (str, optional): Cursor for pagination
            
        Returns:
            tuple: (query_string, variables_dict)
        """
        variables = {"first": first}
        if after:
            variables["after"] = after
        
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
    def build_customer_query(first: int = 10, after: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Build a query to fetch customers.
        
        Args:
            first (int): Number of customers to fetch  
            after (str, optional): Cursor for pagination
            
        Returns:
            tuple: (query_string, variables_dict)
        """
        variables = {"first": first}
        if after:
            variables["after"] = after
        
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
    def build_order_query(first: int = 10, after: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Build a query to fetch orders.
        
        Args:
            first (int): Number of orders to fetch
            after (str, optional): Cursor for pagination
            
        Returns:
            tuple: (query_string, variables_dict)
        """
        variables = {"first": first}
        if after:
            variables["after"] = after
        
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
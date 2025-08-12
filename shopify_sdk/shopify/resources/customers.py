"""
Customers Resource

Handles customer-related operations via Shopify GraphQL API.
"""

from typing import Dict, Any, Optional
from ..query_builder import QueryBuilder


class Customers:
    """Resource class for handling Shopify customers."""
    
    def __init__(self, client):
        """
        Initialize Customers resource.
        
        Args:
            client: ShopifyClient instance
        """
        self.client = client
    
    def list(self, first: int = 10, after: Optional[str] = None) -> Dict[str, Any]:
        """
        List customers from the store.
        
        Args:
            first (int): Number of customers to fetch (max 250)
            after (str, optional): Cursor for pagination
            
        Returns:
            dict: Customers data with pagination info
        """
        query, variables = QueryBuilder.build_customer_query(first, after)
        return self.client.execute_query(query, variables)
    
    def get(self, customer_id: str) -> Dict[str, Any]:
        """
        Get a specific customer by ID.
        
        Args:
            customer_id (str): The customer ID
            
        Returns:
            dict: Customer data
        """
        query = """
        query getCustomer($id: ID!) {
            customer(id: $id) {
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
                addresses(first: 10) {
                    edges {
                        node {
                            id
                            address1
                            address2
                            city
                            province
                            country
                            zip
                            firstName
                            lastName
                            phone
                        }
                    }
                }
                orders(first: 10) {
                    edges {
                        node {
                            id
                            name
                            createdAt
                            financialStatus
                            totalPriceSet {
                                presentmentMoney {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {"id": customer_id}
        return self.client.execute_query(query, variables)
    
    def create(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new customer.
        
        Args:
            customer_data (dict): Customer data for creation
            
        Returns:
            dict: Created customer data
        """
        mutation = """
        mutation customerCreate($input: CustomerInput!) {
            customerCreate(input: $input) {
                customer {
                    id
                    firstName
                    lastName
                    email
                    phone
                    createdAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {"input": customer_data}
        return self.client.execute_mutation(mutation, variables)
    
    def update(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing customer.
        
        Args:
            customer_id (str): The customer ID to update
            customer_data (dict): Updated customer data
            
        Returns:
            dict: Updated customer data
        """
        customer_data["id"] = customer_id
        
        mutation = """
        mutation customerUpdate($input: CustomerInput!) {
            customerUpdate(input: $input) {
                customer {
                    id
                    firstName
                    lastName
                    email
                    phone
                    updatedAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {"input": customer_data}
        return self.client.execute_mutation(mutation, variables)
    
    def delete(self, customer_id: str) -> Dict[str, Any]:
        """
        Delete a customer.
        
        Args:
            customer_id (str): The customer ID to delete
            
        Returns:
            dict: Deletion result
        """
        mutation = """
        mutation customerDelete($input: CustomerDeleteInput!) {
            customerDelete(input: $input) {
                deletedCustomerId
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {"input": {"id": customer_id}}
        return self.client.execute_mutation(mutation, variables)
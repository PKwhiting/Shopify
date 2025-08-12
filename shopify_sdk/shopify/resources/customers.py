"""
Customers Resource

Handles customer-related operations via Shopify GraphQL API.
"""

from typing import Dict, Any, Optional
from ..query_builder import QueryBuilder
from .base import BaseResource


class Customers(BaseResource):
    """Resource class for handling Shopify customers."""
    
    def get_resource_name(self) -> str:
        """Get the singular resource name."""
        return "customer"
    
    def get_plural_resource_name(self) -> str:
        """Get the plural resource name."""
        return "customers"
    
    def list(self, first: int = 10, after: Optional[str] = None) -> Dict[str, Any]:
        """
        List customers from the store.
        
        Args:
            first (int): Number of customers to fetch (max 250)
            after (str, optional): Cursor for pagination
            
        Returns:
            dict: Customers data with pagination info
            
        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_pagination_params(first, after)
        query, variables = QueryBuilder.build_customer_query(first, after)
        return self._execute_query_with_validation(query, variables)
    
    def get(self, customer_id: str) -> Dict[str, Any]:
        """
        Get a specific customer by ID.
        
        Args:
            customer_id (str): The customer ID
            
        Returns:
            dict: Customer data
            
        Raises:
            ValueError: If customer_id is invalid
        """
        customer_id = self._validate_id(customer_id)
        
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
        return self._execute_query_with_validation(query, variables)
    
    def create(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new customer.
        
        Args:
            customer_data (dict): Customer data for creation
            
        Returns:
            dict: Created customer data
            
        Raises:
            ValueError: If customer_data is invalid or operation fails
        """
        if not isinstance(customer_data, dict):
            raise ValueError("Customer data must be a dictionary")
        if not customer_data:
            raise ValueError("Customer data cannot be empty")
        
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
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Customer creation")
    
    def update(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing customer.
        
        Args:
            customer_id (str): The customer ID to update
            customer_data (dict): Updated customer data
            
        Returns:
            dict: Updated customer data
            
        Raises:
            ValueError: If parameters are invalid or operation fails
        """
        customer_id = self._validate_id(customer_id)
        
        if not isinstance(customer_data, dict):
            raise ValueError("Customer data must be a dictionary")
        if not customer_data:
            raise ValueError("Customer data cannot be empty")
        
        # Create a copy to avoid modifying the original
        update_data = customer_data.copy()
        update_data["id"] = customer_id
        
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
        variables = {"input": update_data}
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Customer update")
    
    def delete(self, customer_id: str) -> Dict[str, Any]:
        """
        Delete a customer.
        
        Args:
            customer_id (str): The customer ID to delete
            
        Returns:
            dict: Deletion result
            
        Raises:
            ValueError: If customer_id is invalid or operation fails
        """
        customer_id = self._validate_id(customer_id)
        
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
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Customer deletion")
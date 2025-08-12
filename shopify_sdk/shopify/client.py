"""
Shopify GraphQL API Client

Main client for interacting with Shopify's GraphQL API.
"""

import json
from typing import Dict, Any, Optional
import requests

from .auth.api_key import ApiKeyAuth
from .utils.error_handler import ErrorHandler
from .utils.pagination import PaginationHelper


class ShopifyClient:
    """Main client for Shopify GraphQL API interactions."""
    
    def __init__(self, shop_url: str, api_key: str, api_version: str = "2024-01"):
        """
        Initialize the Shopify client.
        
        Args:
            shop_url (str): The shop URL (e.g., 'myshop.myshopify.com')
            api_key (str): The API access token
            api_version (str): The API version to use
        """
        self.shop_url = shop_url.rstrip('/')
        self.api_version = api_version
        self.auth = ApiKeyAuth(api_key)
        self.error_handler = ErrorHandler()
        self.pagination = PaginationHelper()
        
        self.base_url = f"https://{self.shop_url}/admin/api/{api_version}/graphql.json"
    
    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Shopify's API.
        
        Args:
            query (str): The GraphQL query string
            variables (dict, optional): Variables for the GraphQL query
            
        Returns:
            dict: The response data from the API
            
        Raises:
            ShopifyAPIError: If the API returns an error
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        headers = self.auth.get_headers()
        headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(
                self.base_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Handle GraphQL errors
            if "errors" in result:
                self.error_handler.handle_graphql_errors(result["errors"])
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            self.error_handler.handle_request_error(e)
    
    def execute_mutation(self, mutation: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation against Shopify's API.
        
        Args:
            mutation (str): The GraphQL mutation string
            variables (dict, optional): Variables for the GraphQL mutation
            
        Returns:
            dict: The response data from the API
        """
        return self.execute_query(mutation, variables)
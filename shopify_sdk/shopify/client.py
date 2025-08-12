"""
Shopify GraphQL API Client

Main client for interacting with Shopify's GraphQL API.
"""

import json
import threading
from typing import Dict, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth.api_key import ApiKeyAuth
from .utils.error_handler import ErrorHandler
from .utils.pagination import PaginationHelper
from .utils.retry import RetryHandler
from .config import ShopifyConfig


class ShopifyClient:
    """Main client for Shopify GraphQL API interactions."""
    
    def __init__(self, 
                 shop_url: str, 
                 api_key: str, 
                 api_version: str = "2024-01",
                 config: Optional[ShopifyConfig] = None,
                 enable_retry: bool = True,
                 **config_kwargs):
        """
        Initialize the Shopify client.
        
        Args:
            shop_url (str): The shop URL (e.g., 'myshop.myshopify.com')
            api_key (str): The API access token
            api_version (str): The API version to use (deprecated, use config instead)
            config (ShopifyConfig, optional): Configuration instance
            enable_retry (bool): Whether to enable automatic retries
            **config_kwargs: Additional configuration options
            
        Raises:
            ValueError: If required parameters are invalid
        """
        self.shop_url = self._validate_shop_url(shop_url)
        
        # Initialize configuration
        if config is None:
            # Use api_version parameter for backward compatibility
            config_kwargs.setdefault('api_version', api_version)
            self.config = ShopifyConfig(**config_kwargs)
        else:
            self.config = config
        
        # Initialize authentication
        self.auth = ApiKeyAuth(api_key)
        if not self.auth.is_valid():
            raise ValueError("Invalid API key provided")
        
        # Initialize helpers
        self.error_handler = ErrorHandler()
        self.pagination = PaginationHelper()
        
        # Initialize retry handler if enabled
        if enable_retry:
            self.retry_handler = RetryHandler(self.config)
        else:
            self.retry_handler = None
        
        # Generate base URL using configuration
        self.base_url = self.config.get_base_url(self.shop_url)
        
        # For backward compatibility
        self.api_version = self.config.api_version
        
        # Initialize HTTP session with connection pooling and retry configuration
        self._session_lock = threading.Lock()
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with connection pooling and retry strategy.
        
        Returns:
            requests.Session: Configured session
        """
        session = requests.Session()
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection pools to cache
            pool_maxsize=20,      # Maximum number of connections in the pool
            max_retries=0,        # We handle retries ourselves
            pool_block=False      # Don't block when pool is full
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def _validate_shop_url(self, shop_url: str) -> str:
        """
        Validate and normalize shop URL.
        
        Args:
            shop_url (str): Shop URL to validate
            
        Returns:
            str: Validated shop URL
            
        Raises:
            ValueError: If shop URL is invalid
        """
        if not isinstance(shop_url, str) or not shop_url.strip():
            raise ValueError("Shop URL must be a non-empty string")
        
        shop_url = shop_url.strip().rstrip('/')
        
        # Remove protocol if present for consistency
        if shop_url.startswith(('http://', 'https://')):
            shop_url = shop_url.split('://', 1)[1]
        
        # Basic validation
        if '.' not in shop_url:
            raise ValueError("Invalid shop URL format")
        
        return shop_url
    
    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Shopify's API with automatic retries.
        
        Args:
            query (str): The GraphQL query string
            variables (dict, optional): Variables for the GraphQL query
            
        Returns:
            dict: The response data from the API
            
        Raises:
            ShopifyAPIError: If the API returns an error
            ValueError: If query parameters are invalid
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string")
        
        if variables is not None and not isinstance(variables, dict):
            raise ValueError("Variables must be a dictionary")
        
        # Execute with retry if retry handler is available
        if self.retry_handler:
            return self.retry_handler.execute_with_retry(self._execute_query, query, variables)
        else:
            return self._execute_query(query, variables)
    
    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal method to execute a GraphQL query.
        
        Args:
            query (str): The GraphQL query string
            variables (dict, optional): Variables for the GraphQL query
            
        Returns:
            dict: The response data from the API
        """
        payload = {
            "query": query.strip(),
            "variables": variables or {}
        }
        
        headers = self.auth.get_headers()
        headers["Content-Type"] = "application/json"
        
        try:
            with self._session_lock:
                response = self._session.post(
                    self.base_url,
                    data=json.dumps(payload),
                    headers=headers,
                    timeout=self.config.timeout
                )
            
            response.raise_for_status()
            
            # Parse JSON with better error handling
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response from API: {str(e)}") from e
            
            # Handle GraphQL errors
            if "errors" in result:
                self.error_handler.handle_graphql_errors(result["errors"])
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            self.error_handler.handle_request_error(e)
        except (ValueError, json.JSONDecodeError) as e:
            # Re-raise JSON parsing errors with better context
            raise RuntimeError(f"Invalid response format from API: {str(e)}") from e
    
    def execute_mutation(self, mutation: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation against Shopify's API.
        
        Args:
            mutation (str): The GraphQL mutation string
            variables (dict, optional): Variables for the GraphQL mutation
            
        Returns:
            dict: The response data from the API
            
        Raises:
            ValueError: If mutation parameters are invalid
        """
        if not isinstance(mutation, str) or not mutation.strip():
            raise ValueError("Mutation must be a non-empty string")
        
        return self.execute_query(mutation, variables)
    
    def close(self) -> None:
        """
        Close the HTTP session to free up connections.
        Should be called when done with the client.
        """
        with self._session_lock:
            if hasattr(self, '_session') and self._session:
                self._session.close()
                self._session = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up resources."""
        self.close()
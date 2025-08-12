"""
API Key Authentication for Shopify API

Handles authentication using API access tokens (no OAuth functionality).
"""

from typing import Dict


class ApiKeyAuth:
    """Handles API key authentication for Shopify API."""
    
    def __init__(self, api_key: str):
        """
        Initialize API key authentication.
        
        Args:
            api_key (str): The Shopify API access token
        """
        self.api_key = api_key
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            dict: Headers dict with authentication information
        """
        return {
            "X-Shopify-Access-Token": self.api_key
        }
    
    def is_valid(self) -> bool:
        """
        Check if the API key is valid (basic validation).
        
        Returns:
            bool: True if API key appears valid
        """
        return bool(self.api_key and len(self.api_key.strip()) > 0)
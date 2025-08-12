"""
Authentication module for Shopify SDK

Contains API key authentication (no OAuth).
"""

from .api_key import ApiKeyAuth

def from_environment():
    """
    Create an ApiKeyAuth instance using environment variables.
    
    Returns:
        ApiKeyAuth: Configured authentication instance
        
    Raises:
        ValueError: If required environment variables are not set
    """
    return ApiKeyAuth(_from_env=True)

__all__ = ["ApiKeyAuth", "from_environment"]
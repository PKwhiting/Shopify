"""
API Key Authentication for Shopify API

Handles authentication using API access tokens (no OAuth functionality).
"""

import os
from typing import Dict, Optional

try:
    from dotenv import load_dotenv

    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    # python-dotenv not installed, environment variables will still work
    # but .env file won't be automatically loaded
    pass


class ApiKeyAuth:
    """Handles API key authentication for Shopify API."""

    def __init__(self, api_key: Optional[str] = None, _from_env: bool = False):
        """
        Initialize API key authentication.

        Args:
            api_key (str, optional): The Shopify API access token.
                                   If None and _from_env is True, will try to load from
                                   SHOPIFY_ACCESS_TOKEN environment variable.
                                   If None and _from_env is False, will accept None for
                                   backward compatibility with tests.
            _from_env (bool): Internal parameter to distinguish between
                            explicit None and loading from environment.
        """
        if api_key is not None or not _from_env:
            self.api_key = api_key
        else:
            # Try to load from environment variables
            self.api_key = os.getenv("SHOPIFY_ACCESS_TOKEN")

            # If still no API key found or empty, raise error
            if not self.api_key:
                raise ValueError(
                    "API key is required. Provide it as a parameter or set the "
                    "SHOPIFY_ACCESS_TOKEN environment variable."
                )

    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            dict: Headers dict with authentication information
        """
        return {"X-Shopify-Access-Token": self.api_key}

    def is_valid(self) -> bool:
        """
        Check if the API key is valid (basic validation).

        Returns:
            bool: True if API key appears valid
        """
        return bool(self.api_key and len(self.api_key.strip()) > 0)

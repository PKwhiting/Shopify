"""
Authentication module for Shopify SDK

Contains API key authentication (no OAuth).
"""

from .api_key import ApiKeyAuth

__all__ = ["ApiKeyAuth"]
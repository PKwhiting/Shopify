"""
Shopify GraphQL API SDK

A Python SDK for interacting with Shopify's GraphQL API.
Supports API key authentication, resource querying, pagination, error handling, and webhooks.
"""

from .client import ShopifyClient
from .query_builder import QueryBuilder
from .config import ShopifyConfig
from .product import Product

__version__ = "1.1.0"
__author__ = "PKwhiting"

__all__ = ["ShopifyClient", "QueryBuilder", "ShopifyConfig", "Product"]
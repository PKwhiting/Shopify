"""
Shopify GraphQL API SDK

A Python SDK for interacting with Shopify's GraphQL API.
Supports API key authentication, resource querying, pagination, error handling, and webhooks.
"""

from .client import ShopifyClient
from .query_builder import QueryBuilder

__version__ = "1.0.0"
__author__ = "PKwhiting"

__all__ = ["ShopifyClient", "QueryBuilder"]
"""
Shopify Resources module

Contains resource classes for products, customers, and orders.
"""

from .base import BaseResource
from .products import Products
from .customers import Customers  
from .orders import Orders

__all__ = ["BaseResource", "Products", "Customers", "Orders"]
import pytest
import os
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from shopify_sdk.shopify import ShopifyClient
from shopify_sdk.shopify.order import Order

@pytest.mark.integration
def test_order_get_and_buyer_info():
    client = ShopifyClient()
    for order in Order.list(client):
        assert order.id
        assert order.name
        assert order.email
        assert order.created_at
        buyer_info = Order.get_buyer_info(client, order.id)
        assert buyer_info is not None
        assert buyer_info["id"] == order.id
        assert "customer" in buyer_info
        assert "billingAddress" in buyer_info
        assert "shippingAddress" in buyer_info
        order_dict = order.to_dict()
        assert isinstance(order_dict, dict)
        assert str(order).startswith("Order(")
        break
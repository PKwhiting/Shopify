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

    # NOTE: This test assumes there is at least one order in the store.
    # If not, it will skip.
    # 1. List orders using the Orders resource (not public interface)
    from shopify_sdk.shopify.resources.orders import Orders
    orders_resource = Orders(client)
    orders_data = orders_resource.list(first=1)
    orders_list = orders_data.get("orders", {}).get("edges", [])
    if not orders_list:
        pytest.skip("No orders available in the store to test.")
    order_node = orders_list[0]["node"] if "node" in orders_list[0] else orders_list[0]
    order_id = order_node["id"]

    # 2. Get order using public Order interface
    print("TACOBELL")
    order = Order.get(client, order_id)
    print(order)
    assert order is not None
    assert order.id == order_id
    assert order.name
    assert order.email
    assert order.created_at

    # 3. Get buyer info using public Order interface
    buyer_info = Order.get_buyer_info(client, order_id)
    assert buyer_info is not None
    assert buyer_info["id"] == order_id
    assert "customer" in buyer_info
    assert "billingAddress" in buyer_info
    assert "shippingAddress" in buyer_info

    # 4. to_dict and __str__
    order_dict = order.to_dict()
    assert isinstance(order_dict, dict)
    assert str(order).startswith("Order(")

"""
Orders Resource

Handles order-related operations via Shopify GraphQL API.
"""

from typing import Dict, Any, Optional
from ..query_builder import QueryBuilder


class Orders:
    """Resource class for handling Shopify orders."""
    
    def __init__(self, client):
        """
        Initialize Orders resource.
        
        Args:
            client: ShopifyClient instance
        """
        self.client = client
    
    def list(self, first: int = 10, after: Optional[str] = None) -> Dict[str, Any]:
        """
        List orders from the store.
        
        Args:
            first (int): Number of orders to fetch (max 250)
            after (str, optional): Cursor for pagination
            
        Returns:
            dict: Orders data with pagination info
        """
        query, variables = QueryBuilder.build_order_query(first, after)
        return self.client.execute_query(query, variables)
    
    def get(self, order_id: str) -> Dict[str, Any]:
        """
        Get a specific order by ID.
        
        Args:
            order_id (str): The order ID
            
        Returns:
            dict: Order data
        """
        query = """
        query getOrder($id: ID!) {
            order(id: $id) {
                id
                name
                email
                createdAt
                updatedAt
                processedAt
                financialStatus
                fulfillmentStatus
                totalPriceSet {
                    presentmentMoney {
                        amount
                        currencyCode
                    }
                }
                customer {
                    id
                    firstName
                    lastName
                    email
                }
                shippingAddress {
                    address1
                    address2
                    city
                    province
                    country
                    zip
                    firstName
                    lastName
                    phone
                }
                lineItems(first: 250) {
                    edges {
                        node {
                            id
                            title
                            quantity
                            originalUnitPriceSet {
                                presentmentMoney {
                                    amount
                                    currencyCode
                                }
                            }
                            variant {
                                id
                                title
                                sku
                            }
                            product {
                                id
                                title
                                handle
                            }
                        }
                    }
                }
                fulfillments(first: 10) {
                    edges {
                        node {
                            id
                            status
                            createdAt
                            trackingCompany
                            trackingNumbers
                        }
                    }
                }
            }
        }
        """
        variables = {"id": order_id}
        return self.client.execute_query(query, variables)
    
    def update(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order.
        
        Args:
            order_id (str): The order ID to update
            order_data (dict): Updated order data
            
        Returns:
            dict: Updated order data
        """
        order_data["id"] = order_id
        
        mutation = """
        mutation orderUpdate($input: OrderInput!) {
            orderUpdate(input: $input) {
                order {
                    id
                    name
                    email
                    updatedAt
                    financialStatus
                    fulfillmentStatus
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {"input": order_data}
        return self.client.execute_mutation(mutation, variables)
    
    def cancel(self, order_id: str, reason: str = "other", notify_customer: bool = False) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id (str): The order ID to cancel
            reason (str): Reason for cancellation
            notify_customer (bool): Whether to notify customer
            
        Returns:
            dict: Cancellation result
        """
        mutation = """
        mutation orderCancel($orderId: ID!, $reason: OrderCancelReason!, $notifyCustomer: Boolean!) {
            orderCancel(orderId: $orderId, reason: $reason, notifyCustomer: $notifyCustomer) {
                order {
                    id
                    name
                    cancelled
                    cancelledAt
                    cancelReason
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "orderId": order_id,
            "reason": reason.upper(),
            "notifyCustomer": notify_customer
        }
        return self.client.execute_mutation(mutation, variables)
    
    def fulfill(self, order_id: str, line_items: list, notify_customer: bool = True) -> Dict[str, Any]:
        """
        Create a fulfillment for an order.
        
        Args:
            order_id (str): The order ID
            line_items (list): List of line items to fulfill
            notify_customer (bool): Whether to notify customer
            
        Returns:
            dict: Fulfillment result
        """
        mutation = """
        mutation fulfillmentCreate($input: FulfillmentInput!) {
            fulfillmentCreate(input: $input) {
                fulfillment {
                    id
                    status
                    createdAt
                    trackingCompany
                    trackingNumbers
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "input": {
                "orderId": order_id,
                "lineItems": line_items,
                "notifyCustomer": notify_customer
            }
        }
        return self.client.execute_mutation(mutation, variables)
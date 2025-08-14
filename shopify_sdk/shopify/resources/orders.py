"""
Orders Resource

Handles order-related operations via Shopify GraphQL API.
"""

from typing import Dict, Any, Optional
from ..query_builder import QueryBuilder
from .base import BaseResource


class Orders(BaseResource):
    """Resource class for handling Shopify orders."""

    def get_resource_name(self) -> str:
        """Get the singular resource name."""
        return "order"

    def get_plural_resource_name(self) -> str:
        """Get the plural resource name."""
        return "orders"

    def list(self, first: int = 10, after: Optional[str] = None) -> Dict[str, Any]:
        """
        List orders from the store.

        Args:
            first (int): Number of orders to fetch (max 250)
            after (str, optional): Cursor for pagination

        Returns:
            dict: Orders data with pagination info

        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_pagination_params(first, after)
        # Inline query to match latest Shopify schema (remove deprecated fields)
        query = """
        query getOrders($first: Int!, $after: String) {
            orders(first: $first, after: $after) {
                edges {
                    node {
                        id
                        name
                        email
                        createdAt
                        updatedAt
                        processedAt
                        displayFinancialStatus
                        displayFulfillmentStatus
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
                            phone
                            state
                            tags
                            note
                            createdAt
                            updatedAt
                            defaultAddress {
                                id
                                address1
                                address2
                                city
                                province
                                country
                                zip
                                firstName
                                lastName
                                phone
                                company
                            }
                            addresses(first: 10) {
                                id
                                address1
                                address2
                                city
                                province
                                country
                                zip
                                firstName
                                lastName
                                phone
                                company
                            }
                        }
                        billingAddress {
                            address1
                            address2
                            city
                            province
                            country
                            zip
                            firstName
                            lastName
                            phone
                            company
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
                            company
                        }
                        lineItems(first: 10) {
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
                        fulfillments(first: 1) {
                            id
                            status
                            createdAt
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        variables = {"first": first}
        if after:
            variables["after"] = after
        return self._execute_query_with_validation(query, variables)

    def get(self, order_id: str) -> Dict[str, Any]:
        """
        Get a specific order by ID.

        Args:
            order_id (str): The order ID

        Returns:
            dict: Order data

        Raises:
            ValueError: If order_id is invalid
        """
        order_id = self._validate_id(order_id)

        query = """
        query getOrder($id: ID!) {
            order(id: $id) {
                id
                name
                email
                createdAt
                updatedAt
                processedAt
                displayFinancialStatus
                displayFulfillmentStatus
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
                    phone
                    state
                    tags
                    note
                    createdAt
                    updatedAt
                    defaultAddress {
                        id
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        firstName
                        lastName
                        phone
                        company
                    }
                    addresses(first: 10) {
                        id
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        firstName
                        lastName
                        phone
                        company
                    }
                }
                billingAddress {
                    address1
                    address2
                    city
                    province
                    country
                    zip
                    firstName
                    lastName
                    phone
                    company
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
                    company
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
                    id
                    status
                    createdAt
                }
            }
        }
        """
        variables = {"id": order_id}
        return self._execute_query_with_validation(query, variables)

    def get_buyer_info(self, order_id: str) -> Dict[str, Any]:
        """
        Get comprehensive buyer information for a specific order.

        Args:
            order_id (str): The order ID

        Returns:
            dict: Comprehensive buyer information including customer details,
                  billing address, shipping address, and order contact info

        Raises:
            ValueError: If order_id is invalid
        """
        order_id = self._validate_id(order_id)

        query = """
        query getBuyerInfo($id: ID!) {
            order(id: $id) {
                id
                name
                email
                phone
                customer {
                    id
                    firstName
                    lastName
                    email
                    phone
                    state
                    tags
                    note
                    createdAt
                    updatedAt
                    lifetimeDuration
                    defaultAddress {
                        id
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        firstName
                        lastName
                        phone
                        company
                    }
                    addresses(first: 10) {
                        id
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        firstName
                        lastName
                        phone
                        company
                    }
                    orders(first: 1) {
                        edges {
                            node {
                                id
                                createdAt
                                totalPriceSet {
                                    presentmentMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                            }
                        }
                    }
                }
                billingAddress {
                    address1
                    address2
                    city
                    province
                    country
                    zip
                    firstName
                    lastName
                    phone
                    company
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
                    company
                }
            }
        }
        """
        variables = {"id": order_id}
        return self._execute_query_with_validation(query, variables)

    def update(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order.

        Args:
            order_id (str): The order ID to update
            order_data (dict): Updated order data

        Returns:
            dict: Updated order data

        Raises:
            ValueError: If parameters are invalid or operation fails
        """
        order_id = self._validate_id(order_id)

        if not isinstance(order_data, dict):
            raise ValueError("Order data must be a dictionary")
        if not order_data:
            raise ValueError("Order data cannot be empty")

        # Create a copy to avoid modifying the original
        update_data = order_data.copy()
        update_data["id"] = order_id

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
        variables = {"input": update_data}
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Order update")

    def cancel(
        self, order_id: str, reason: str = "other", notify_customer: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            order_id (str): The order ID to cancel
            reason (str): Reason for cancellation
            notify_customer (bool): Whether to notify customer

        Returns:
            dict: Cancellation result

        Raises:
            ValueError: If parameters are invalid or operation fails
        """
        order_id = self._validate_id(order_id)

        # Validate reason
        valid_reasons = ["customer", "declined", "fraud", "inventory", "other"]
        if reason not in valid_reasons:
            raise ValueError(f"Invalid cancel reason. Must be one of: {', '.join(valid_reasons)}")

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
            "notifyCustomer": notify_customer,
        }
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Order cancellation")

    def fulfill(
        self, order_id: str, line_items: list, notify_customer: bool = True
    ) -> Dict[str, Any]:
        """
        Create a fulfillment for an order.

        Args:
            order_id (str): The order ID
            line_items (list): List of line items to fulfill
            notify_customer (bool): Whether to notify customer

        Returns:
            dict: Fulfillment result

        Raises:
            ValueError: If parameters are invalid or operation fails
        """
        order_id = self._validate_id(order_id)

        if not isinstance(line_items, list):
            raise ValueError("Line items must be a list")
        if not line_items:
            raise ValueError("Line items cannot be empty")

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
                "notifyCustomer": notify_customer,
            }
        }
        result = self._execute_mutation_with_validation(mutation, variables)
        return self._process_user_errors(result, "Order fulfillment")

"""
Order Class

Simplified interface for dealing with individual Shopify orders.
Provides classmethods for factory operations and instance methods for order operations.
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
	from .client import ShopifyClient


class Order:
	@classmethod
	def list(cls, client: Optional["ShopifyClient"] = None):
		"""
		Yield all orders from the store, paginating automatically.

		Args:
			client: ShopifyClient instance. If None, will be created from environment variables.

		Yields:
			Order instances
			
		Raises:
			ValueError: If client is None and environment variables are not properly set
		"""
		if client is None:
			from .client import create_client_from_environment
			client = create_client_from_environment()
			
		from .resources.orders import Orders
		resource = Orders(client)
		after = None
		while True:
			result = resource.list(first=250, after=after)
			orders_data = result.get("orders", {})
			edges = orders_data.get("edges", [])
			for edge in edges:
				node = edge.get("node")
				if node:
					yield cls(client, node)
			page_info = orders_data.get("pageInfo", {})
			if not page_info.get("hasNextPage") or not edges:
				break
			after = page_info.get("endCursor")
			if not after:
				break
	"""
	Simplified Order class representing an individual Shopify order.

	Provides classmethods for operations like search, get, and
	instance methods for order operations.
	"""

	def __init__(self, client: "ShopifyClient", data: Dict[str, Any]):
		"""
		Initialize an Order instance.

		Args:
			client: ShopifyClient instance
			data: Order data from GraphQL response
		"""
		self.client = client
		self._data = data.copy()
		self._original_data = data.copy()

	@property
	def id(self) -> Optional[str]:
		"""Get order ID."""
		return self._data.get("id")

	@property
	def name(self) -> Optional[str]:
		"""Get order name."""
		return self._data.get("name")

	@property
	def email(self) -> Optional[str]:
		"""Get order email."""
		return self._data.get("email")

	@property
	def created_at(self) -> Optional[str]:
		"""Get order creation timestamp."""
		return self._data.get("createdAt")

	@property
	def updated_at(self) -> Optional[str]:
		"""Get order update timestamp."""
		return self._data.get("updatedAt")

	@property
	def processed_at(self) -> Optional[str]:
		"""Get order processed timestamp."""
		return self._data.get("processedAt")

	@property
	def financial_status(self) -> Optional[str]:
		"""Get order financial status (displayFinancialStatus)."""
		return self._data.get("displayFinancialStatus")

	@property
	def fulfillment_status(self) -> Optional[str]:
		"""Get order fulfillment status (displayFulfillmentStatus)."""
		return self._data.get("displayFulfillmentStatus")

	@property
	def total_price(self) -> Optional[float]:
		"""Get order total price as float."""
		price_set = self._data.get("totalPriceSet", {})
		presentment = price_set.get("presentmentMoney", {})
		amount = presentment.get("amount")
		try:
			return float(amount) if amount is not None else None
		except Exception:
			return None

	@property
	def currency(self) -> Optional[str]:
		"""Get order currency code."""
		price_set = self._data.get("totalPriceSet", {})
		presentment = price_set.get("presentmentMoney", {})
		return presentment.get("currencyCode")

	@property
	def customer(self) -> Optional[Dict[str, Any]]:
		"""Get customer info for the order."""
		return self._data.get("customer")

	@property
	def billing_address(self) -> Optional[Dict[str, Any]]:
		"""Get billing address for the order."""
		return self._data.get("billingAddress")

	@property
	def shipping_address(self) -> Optional[Dict[str, Any]]:
		"""Get shipping address for the order."""
		return self._data.get("shippingAddress")

	@property
	def line_items(self) -> List[Dict[str, Any]]:
		"""Get line items for the order."""
		items = self._data.get("lineItems", {})
		if isinstance(items, dict) and "edges" in items:
			return [edge["node"] for edge in items["edges"]]
		return items if isinstance(items, list) else []

	@property
	def fulfillments(self) -> List[Dict[str, Any]]:
		"""Get fulfillments for the order."""
		fulfillments = self._data.get("fulfillments", {})
		if isinstance(fulfillments, dict) and "edges" in fulfillments:
			return [edge["node"] for edge in fulfillments["edges"]]
		return fulfillments if isinstance(fulfillments, list) else []

	@classmethod
	def get(cls, client_or_order_id: Union["ShopifyClient", str], order_id: Optional[str] = None) -> Optional["Order"]:
		"""
		Get an order by ID.

		Args:
			client_or_order_id: ShopifyClient instance OR order ID (when using environment variables)
			order_id: Order ID (when client is provided as first arg)

		Returns:
			Order instance or None if not found

		Raises:
			ValueError: If order_id is invalid or environment variables are not properly set
		"""
		# Handle both call patterns:
		# 1. Order.get(client, order_id) - traditional
		# 2. Order.get(order_id) - new environment variable style
		
		if isinstance(client_or_order_id, str) and order_id is None:
			# New style: Order.get(order_id)
			order_id = client_or_order_id
			from .client import create_client_from_environment
			client = create_client_from_environment()
		else:
			# Traditional style: Order.get(client, order_id)
			client = client_or_order_id
			if not order_id:
				raise ValueError("Order ID must be provided")
				
		if not order_id or not isinstance(order_id, str):
			raise ValueError("Order ID must be a non-empty string")

		# Use Orders resource to fetch order
		from .resources.orders import Orders
		resource = Orders(client)
		result = resource.get(order_id)
		order_data = result.get("order") if result else None
		if order_data:
			return cls(client, order_data)
		return None

	@classmethod
	def get_buyer_info(cls, client_or_order_id: Union["ShopifyClient", str], order_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
		"""
		Get comprehensive buyer information for an order by ID.

		Args:
			client_or_order_id: ShopifyClient instance OR order ID (when using environment variables)
			order_id: Order ID (when client is provided as first arg)

		Returns:
			Buyer info dict or None if not found

		Raises:
			ValueError: If order_id is invalid or environment variables are not properly set
		"""
		# Handle both call patterns:
		# 1. Order.get_buyer_info(client, order_id) - traditional
		# 2. Order.get_buyer_info(order_id) - new environment variable style
		
		if isinstance(client_or_order_id, str) and order_id is None:
			# New style: Order.get_buyer_info(order_id)
			order_id = client_or_order_id
			from .client import create_client_from_environment
			client = create_client_from_environment()
		else:
			# Traditional style: Order.get_buyer_info(client, order_id)
			client = client_or_order_id
			if not order_id:
				raise ValueError("Order ID must be provided")
				
		if not order_id or not isinstance(order_id, str):
			raise ValueError("Order ID must be a non-empty string")

		from .resources.orders import Orders
		resource = Orders(client)
		result = resource.get_buyer_info(order_id)
		order_data = result.get("order") if result else None
		if order_data:
			return order_data
		return None

	def to_dict(self) -> Dict[str, Any]:
		"""Convert order to dictionary."""
		return self._data.copy()

	def __str__(self) -> str:
		"""String representation of the order."""
		return f"Order(id={self.id}, name='{self.name}', status={self.financial_status})"

	def __repr__(self) -> str:
		"""Developer representation of the order."""
		return (
			f"Order(id='{self.id}', name='{self.name}', email='{self.email}', status='{self.financial_status}')"
		)
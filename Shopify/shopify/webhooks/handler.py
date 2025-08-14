"""
Webhook event handler

Handles processing of different Shopify webhook events with signature verification.
"""

import json
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone
from .verifier import WebhookVerifier


class WebhookHandler:
    """Handles processing of Shopify webhook events with security verification."""

    def __init__(self, webhook_secret: Optional[str] = None, verify_signature: bool = False):
        """
        Initialize webhook handler.

        Args:
            webhook_secret (str, optional): Secret for signature verification
            verify_signature (bool): Whether to verify webhook signatures (default: False for backward compatibility)
        """
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._handlers_lock = threading.RLock()  # Reentrant lock for thread safety
        self.verify_signature = verify_signature

        if webhook_secret:
            self.verifier = WebhookVerifier(webhook_secret)
        else:
            self.verifier = None
            if verify_signature:
                raise ValueError(
                    "Webhook secret is required when signature verification is enabled"
                )

    def set_webhook_secret(self, webhook_secret: str) -> None:
        """
        Set webhook secret for signature verification.

        Args:
            webhook_secret (str): The webhook secret from Shopify

        Raises:
            ValueError: If webhook secret is invalid
        """
        if not isinstance(webhook_secret, str) or not webhook_secret.strip():
            raise ValueError("Webhook secret must be a non-empty string")

        self.verifier = WebhookVerifier(webhook_secret.strip())

    def register_handler(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a handler for a specific webhook topic.

        Args:
            topic (str): The webhook topic (e.g., 'orders/create', 'products/update')
            handler (callable): Function to handle the webhook event
        """
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("Topic must be a non-empty string")
        if not callable(handler):
            raise ValueError("Handler must be callable")

        topic = topic.strip()

        with self._handlers_lock:
            if topic not in self._event_handlers:
                self._event_handlers[topic] = []
            self._event_handlers[topic].append(handler)

    def unregister_handler(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Unregister a handler for a specific webhook topic.

        Args:
            topic (str): The webhook topic
            handler (callable): Function to remove from handlers

        Returns:
            bool: True if handler was removed
        """
        if not isinstance(topic, str) or not topic.strip():
            return False

        topic = topic.strip()

        with self._handlers_lock:
            if topic in self._event_handlers:
                try:
                    self._event_handlers[topic].remove(handler)
                    # Clean up empty topic lists
                    if not self._event_handlers[topic]:
                        del self._event_handlers[topic]
                    return True
                except ValueError:
                    pass
        return False

    def handle_webhook(
        self, topic: str, payload: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle a webhook event with optional signature verification.

        Args:
            topic (str): The webhook topic
            payload (str): The webhook payload (JSON string)
            headers (dict, optional): HTTP headers from the webhook request

        Returns:
            dict: Processing result

        Raises:
            ValueError: If signature verification fails
        """
        if not isinstance(topic, str) or not topic.strip():
            return {
                "topic": topic if isinstance(topic, str) else str(topic),
                "processed": False,
                "error": "Topic must be a non-empty string",
            }

        if not isinstance(payload, str):
            return {"topic": topic, "processed": False, "error": "Payload must be a string"}

        # Verify signature if enabled and verifier is available
        if self.verify_signature and self.verifier:
            if not headers:
                return {
                    "topic": topic,
                    "processed": False,
                    "error": "Signature verification enabled but no headers provided",
                }

            if not self.verifier.verify_request(payload, headers):
                return {
                    "topic": topic,
                    "processed": False,
                    "error": "Webhook signature verification failed",
                }

        try:
            # Parse JSON payload
            data = json.loads(payload) if isinstance(payload, str) else payload

            # Create event context
            event = {
                "topic": topic,
                "data": data,
                "headers": headers or {},
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "verified": self.verify_signature and self.verifier is not None,
            }

            # Process event through registered handlers
            results = []
            with self._handlers_lock:
                handlers = self._event_handlers.get(
                    topic, []
                ).copy()  # Copy to avoid race conditions

            # Execute handlers outside the lock to prevent deadlocks
            for handler in handlers:
                try:
                    result = handler(event)
                    results.append({"handler": handler.__name__, "success": True, "result": result})
                except Exception as e:
                    results.append({"handler": handler.__name__, "success": False, "error": str(e)})

            return {
                "topic": topic,
                "processed": True,
                "verified": event["verified"],
                "handlers_executed": len(results),
                "results": results,
            }

        except json.JSONDecodeError as e:
            return {"topic": topic, "processed": False, "error": f"Invalid JSON payload: {str(e)}"}
        except Exception as e:
            return {"topic": topic, "processed": False, "error": f"Processing error: {str(e)}"}

    def get_registered_topics(self) -> List[str]:
        """
        Get list of topics with registered handlers.

        Returns:
            list: List of topic names
        """
        with self._handlers_lock:
            return list(self._event_handlers.keys())

    def get_handler_count(self, topic: str) -> int:
        """
        Get number of handlers registered for a topic.

        Args:
            topic (str): The webhook topic

        Returns:
            int: Number of registered handlers
        """
        if not isinstance(topic, str) or not topic.strip():
            return 0

        topic = topic.strip()
        with self._handlers_lock:
            return len(self._event_handlers.get(topic, []))

    # Pre-defined handler methods for common webhook events

    def handle_order_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default handler for order created webhooks.

        Args:
            event (dict): Webhook event data

        Returns:
            dict: Processing result
        """
        order = event["data"]
        return {
            "order_id": order.get("id"),
            "order_number": order.get("order_number"),
            "customer_email": order.get("email"),
            "total_price": order.get("total_price"),
            "processed": True,
        }

    def handle_order_updated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default handler for order updated webhooks.

        Args:
            event (dict): Webhook event data

        Returns:
            dict: Processing result
        """
        order = event["data"]
        return {
            "order_id": order.get("id"),
            "order_number": order.get("order_number"),
            "financial_status": order.get("financial_status"),
            "fulfillment_status": order.get("fulfillment_status"),
            "processed": True,
        }

    def handle_product_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default handler for product created webhooks.

        Args:
            event (dict): Webhook event data

        Returns:
            dict: Processing result
        """
        product = event["data"]
        return {
            "product_id": product.get("id"),
            "title": product.get("title"),
            "handle": product.get("handle"),
            "product_type": product.get("product_type"),
            "processed": True,
        }

    def handle_product_updated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default handler for product updated webhooks.

        Args:
            event (dict): Webhook event data

        Returns:
            dict: Processing result
        """
        product = event["data"]
        return {
            "product_id": product.get("id"),
            "title": product.get("title"),
            "handle": product.get("handle"),
            "status": product.get("status"),
            "processed": True,
        }

    def handle_customer_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default handler for customer created webhooks.

        Args:
            event (dict): Webhook event data

        Returns:
            dict: Processing result
        """
        customer = event["data"]
        return {
            "customer_id": customer.get("id"),
            "email": customer.get("email"),
            "first_name": customer.get("first_name"),
            "last_name": customer.get("last_name"),
            "processed": True,
        }

"""
Webhook signature verification

Verifies the authenticity of Shopify webhook requests.
"""

import hashlib
import hmac
import base64
from typing import Dict, Any


class WebhookVerifier:
    """Handles verification of Shopify webhook signatures."""
    
    def __init__(self, webhook_secret: str):
        """
        Initialize webhook verifier.
        
        Args:
            webhook_secret (str): The webhook secret from Shopify
        """
        self.webhook_secret = webhook_secret
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify the webhook signature.
        
        Args:
            payload (str): The raw webhook payload
            signature (str): The X-Shopify-Hmac-Sha256 header value
            
        Returns:
            bool: True if signature is valid
        """
        if not signature:
            return False
        
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Compute expected signature
            expected_signature = self._compute_signature(payload)
            
            # Compare signatures using constant-time comparison
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception:
            return False
    
    def verify_request(self, payload: str, headers: dict) -> bool:
        """
        Verify webhook request using headers.
        
        Args:
            payload (str): The raw webhook payload
            headers (dict): HTTP headers from the request
            
        Returns:
            bool: True if request is valid
        """
        signature = headers.get('X-Shopify-Hmac-Sha256', '')
        return self.verify_signature(payload, signature)
    
    def _compute_signature(self, payload: str) -> str:
        """
        Compute HMAC-SHA256 signature for payload.
        
        Args:
            payload (str): The raw webhook payload
            
        Returns:
            str: Base64-encoded signature
        """
        # Create HMAC-SHA256 hash
        mac = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        )
        
        # Return base64-encoded digest
        return base64.b64encode(mac.digest()).decode('utf-8')
    
    def is_webhook_authentic(self, payload: bytes, signature: str) -> bool:
        """
        Check if webhook is authentic (alternative method for bytes payload).
        
        Args:
            payload (bytes): The raw webhook payload as bytes
            signature (str): The signature to verify
            
        Returns:
            bool: True if webhook is authentic
        """
        if not signature:
            return False
        
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Compute expected signature
            mac = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            )
            expected_signature = base64.b64encode(mac.digest()).decode('utf-8')
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception:
            return False
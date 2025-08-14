"""
Configuration management for Shopify SDK

Centralized configuration settings and validation.
"""

import threading
from typing import Optional, Dict, Any
import os


class ShopifyConfig:
    """Configuration management for Shopify SDK."""

    # Default configuration values
    DEFAULT_API_VERSION = "2025-07"
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 250

    def __init__(
        self,
        api_version: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        page_size: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize configuration.

        Args:
            api_version (str, optional): Shopify API version
            timeout (int, optional): Request timeout in seconds
            max_retries (int, optional): Maximum retry attempts
            retry_delay (int, optional): Base delay between retries in seconds
            page_size (int, optional): Default page size for pagination
            **kwargs: Additional configuration options
        """
        # Use defaults if None provided, but validate if explicitly provided
        self.api_version = self._validate_api_version(
            api_version if api_version is not None else self.DEFAULT_API_VERSION
        )
        self.timeout = self._validate_timeout(
            timeout if timeout is not None else self.DEFAULT_TIMEOUT
        )
        self.max_retries = self._validate_max_retries(
            max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        )
        self.retry_delay = self._validate_retry_delay(
            retry_delay if retry_delay is not None else self.DEFAULT_RETRY_DELAY
        )
        self.page_size = self._validate_page_size(
            page_size if page_size is not None else self.DEFAULT_PAGE_SIZE
        )

        # Store additional configuration
        self.extra_config = kwargs

        # Thread safety for configuration updates
        self._config_lock = threading.Lock()

    def _validate_api_version(self, version: str) -> str:
        """Validate API version format."""
        if not isinstance(version, str) or not version.strip():
            raise ValueError("API version must be a non-empty string")

        version = version.strip()

        # Basic format validation (YYYY-MM)
        if len(version.split("-")) != 2:
            raise ValueError(f"Invalid API version format: {version}. Expected format: YYYY-MM")

        return version

    def _validate_timeout(self, timeout: int) -> int:
        """Validate timeout value."""
        if not isinstance(timeout, int) or timeout < 1:
            raise ValueError("Timeout must be a positive integer")
        if timeout > 300:  # 5 minutes max
            raise ValueError("Timeout cannot exceed 300 seconds")
        return timeout

    def _validate_max_retries(self, max_retries: int) -> int:
        """Validate max retries value."""
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("Max retries must be a non-negative integer")
        if max_retries > 10:
            raise ValueError("Max retries cannot exceed 10")
        return max_retries

    def _validate_retry_delay(self, retry_delay: int) -> int:
        """Validate retry delay value."""
        if not isinstance(retry_delay, int) or retry_delay < 0:
            raise ValueError("Retry delay must be a non-negative integer")
        if retry_delay > 60:
            raise ValueError("Retry delay cannot exceed 60 seconds")
        return retry_delay

    def _validate_page_size(self, page_size: int) -> int:
        """Validate page size value."""
        if not isinstance(page_size, int) or page_size < 1:
            raise ValueError("Page size must be a positive integer")
        if page_size > self.MAX_PAGE_SIZE:
            raise ValueError(f"Page size cannot exceed {self.MAX_PAGE_SIZE}")
        return page_size

    def get_base_url(self, shop_url: str) -> str:
        """
        Generate base GraphQL API URL.

        Args:
            shop_url (str): Shop URL

        Returns:
            str: Complete GraphQL API URL
        """
        if not isinstance(shop_url, str) or not shop_url.strip():
            raise ValueError("Shop URL must be a non-empty string")

        shop_url = shop_url.strip().rstrip("/")

        # Add protocol if missing
        if not shop_url.startswith(("http://", "https://")):
            shop_url = f"https://{shop_url}"

        return f"{shop_url}/admin/api/{self.api_version}/graphql.json"

    def update(self, **kwargs) -> None:
        """
        Update configuration values.

        Args:
            **kwargs: Configuration values to update
        """
        with self._config_lock:
            for key, value in kwargs.items():
                if hasattr(self, f"_validate_{key}"):
                    # Use validation method if available
                    validator = getattr(self, f"_validate_{key}")
                    setattr(self, key, validator(value))
                elif hasattr(self, key):
                    # Set directly if attribute exists
                    setattr(self, key, value)
                else:
                    # Store in extra config
                    self.extra_config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key (str): Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        with self._config_lock:
            if hasattr(self, key):
                return getattr(self, key)
            return self.extra_config.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            dict: Configuration as dictionary
        """
        with self._config_lock:
            config = {
                "api_version": self.api_version,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay,
                "page_size": self.page_size,
            }
            config.update(self.extra_config.copy())
            return config

    @classmethod
    def from_environment(cls, prefix: str = "SHOPIFY_") -> "ShopifyConfig":
        """
        Create configuration from environment variables.

        Args:
            prefix (str): Environment variable prefix

        Returns:
            ShopifyConfig: Configuration instance
        """
        config = {}

        # Map environment variables to config keys
        env_mappings = {
            f"{prefix}API_VERSION": "api_version",
            f"{prefix}TIMEOUT": "timeout",
            f"{prefix}MAX_RETRIES": "max_retries",
            f"{prefix}RETRY_DELAY": "retry_delay",
            f"{prefix}PAGE_SIZE": "page_size",
        }

        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                # Convert string values to appropriate types
                if config_key in ["timeout", "max_retries", "retry_delay", "page_size"]:
                    try:
                        config[config_key] = int(env_value)
                    except ValueError:
                        raise ValueError(f"Invalid integer value for {env_key}: {env_value}")
                else:
                    config[config_key] = env_value

        return cls(**config)

    def __str__(self) -> str:
        """String representation of configuration."""
        return f"ShopifyConfig(api_version={self.api_version}, timeout={self.timeout})"

    def __repr__(self) -> str:
        """Detailed string representation of configuration."""
        return (
            f"ShopifyConfig(api_version='{self.api_version}', "
            f"timeout={self.timeout}, max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay}, page_size={self.page_size})"
        )

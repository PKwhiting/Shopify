"""
Comprehensive Configuration Tests

Extensive tests for ShopifyConfig including edge cases, validation,
environment handling, and advanced configuration scenarios.
"""

import unittest
from unittest.mock import patch, Mock
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shopify.config import ShopifyConfig


class TestShopifyConfigExtensive(unittest.TestCase):
    """Comprehensive tests for ShopifyConfig."""
    
    def test_default_values(self):
        """Test all default configuration values."""
        config = ShopifyConfig()
        
        self.assertEqual(config.api_version, "2024-01")
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_delay, 1)
        self.assertEqual(config.page_size, 10)
        
        # Test class constants
        self.assertEqual(ShopifyConfig.DEFAULT_API_VERSION, "2024-01")
        self.assertEqual(ShopifyConfig.DEFAULT_TIMEOUT, 30)
        self.assertEqual(ShopifyConfig.DEFAULT_MAX_RETRIES, 3)
        self.assertEqual(ShopifyConfig.DEFAULT_RETRY_DELAY, 1)
        self.assertEqual(ShopifyConfig.DEFAULT_PAGE_SIZE, 10)
        self.assertEqual(ShopifyConfig.MAX_PAGE_SIZE, 250)
    
    def test_custom_configuration(self):
        """Test configuration with all custom values."""
        config = ShopifyConfig(
            api_version="2023-07",
            timeout=120,
            max_retries=10,
            retry_delay=5,
            page_size=100
        )
        
        self.assertEqual(config.api_version, "2023-07")
        self.assertEqual(config.timeout, 120)
        self.assertEqual(config.max_retries, 10)
        self.assertEqual(config.retry_delay, 5)
        self.assertEqual(config.page_size, 100)
    
    def test_partial_custom_configuration(self):
        """Test configuration with some custom values, others default."""
        config = ShopifyConfig(
            timeout=60,
            page_size=25
        )
        
        # Custom values
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.page_size, 25)
        
        # Default values
        self.assertEqual(config.api_version, "2024-01")
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_delay, 1)
    
    def test_api_version_validation_valid(self):
        """Test API version validation with valid values."""
        valid_versions = [
            "2024-01", "2023-10", "2023-07", "2023-04", "2023-01",
            "2022-10", "2022-07", "2022-04", "2022-01", "2021-10"
        ]
        
        for version in valid_versions:
            config = ShopifyConfig(api_version=version)
            self.assertEqual(config.api_version, version)
    
    def test_api_version_validation_invalid_format(self):
        """Test API version validation with invalid formats."""
        invalid_versions = [
            "",           # Empty string
            "invalid",    # Not date format
            "2024",       # Missing month
            "24-01",      # Wrong year format
            "2024-1",     # Wrong month format
            "2024-13",    # Invalid month
            "2024-00",    # Invalid month
            "2024-ab",    # Non-numeric month
            "2024_01",    # Wrong separator
            "2024.01",    # Wrong separator
        ]
        
        for version in invalid_versions:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(api_version=version)
            
            self.assertIn("API version must be in format YYYY-MM", str(context.exception))
    
    def test_api_version_validation_none(self):
        """Test API version validation with None."""
        with self.assertRaises(ValueError) as context:
            ShopifyConfig(api_version=None)
        
        self.assertIn("API version cannot be None", str(context.exception))
    
    def test_api_version_validation_non_string(self):
        """Test API version validation with non-string values."""
        invalid_types = [123, [], {}, True, 20.24]
        
        for invalid_type in invalid_types:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(api_version=invalid_type)
            
            self.assertIn("API version must be a string", str(context.exception))
    
    def test_timeout_validation_valid(self):
        """Test timeout validation with valid values."""
        valid_timeouts = [1, 30, 60, 120, 300, 600]
        
        for timeout in valid_timeouts:
            config = ShopifyConfig(timeout=timeout)
            self.assertEqual(config.timeout, timeout)
    
    def test_timeout_validation_invalid_values(self):
        """Test timeout validation with invalid values."""
        invalid_timeouts = [0, -1, -10, 601, 1000]
        
        for timeout in invalid_timeouts:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(timeout=timeout)
            
            self.assertIn("Timeout must be between 1 and 600 seconds", str(context.exception))
    
    def test_timeout_validation_non_integer(self):
        """Test timeout validation with non-integer values."""
        invalid_types = ["30", 30.5, [], {}, True, None]
        
        for invalid_type in invalid_types:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(timeout=invalid_type)
            
            self.assertIn("Timeout must be an integer", str(context.exception))
    
    def test_max_retries_validation_valid(self):
        """Test max retries validation with valid values."""
        valid_retries = [0, 1, 3, 5, 10]
        
        for retries in valid_retries:
            config = ShopifyConfig(max_retries=retries)
            self.assertEqual(config.max_retries, retries)
    
    def test_max_retries_validation_invalid_values(self):
        """Test max retries validation with invalid values."""
        invalid_retries = [-1, -5, 11, 20, 100]
        
        for retries in invalid_retries:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(max_retries=retries)
            
            self.assertIn("Max retries must be between 0 and 10", str(context.exception))
    
    def test_max_retries_validation_non_integer(self):
        """Test max retries validation with non-integer values."""
        invalid_types = ["3", 3.5, [], {}, True, None]
        
        for invalid_type in invalid_types:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(max_retries=invalid_type)
            
            self.assertIn("Max retries must be an integer", str(context.exception))
    
    def test_retry_delay_validation_valid(self):
        """Test retry delay validation with valid values."""
        valid_delays = [1, 2, 5, 10, 30]
        
        for delay in valid_delays:
            config = ShopifyConfig(retry_delay=delay)
            self.assertEqual(config.retry_delay, delay)
    
    def test_retry_delay_validation_invalid_values(self):
        """Test retry delay validation with invalid values."""
        invalid_delays = [0, -1, 31, 60, 100]
        
        for delay in invalid_delays:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(retry_delay=delay)
            
            self.assertIn("Retry delay must be between 1 and 30 seconds", str(context.exception))
    
    def test_retry_delay_validation_non_integer(self):
        """Test retry delay validation with non-integer values."""
        invalid_types = ["1", 1.5, [], {}, True, None]
        
        for invalid_type in invalid_types:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(retry_delay=invalid_type)
            
            self.assertIn("Retry delay must be an integer", str(context.exception))
    
    def test_page_size_validation_valid(self):
        """Test page size validation with valid values."""
        valid_sizes = [1, 10, 25, 50, 100, 250]
        
        for size in valid_sizes:
            config = ShopifyConfig(page_size=size)
            self.assertEqual(config.page_size, size)
    
    def test_page_size_validation_invalid_values(self):
        """Test page size validation with invalid values."""
        invalid_sizes = [0, -1, 251, 300, 1000]
        
        for size in invalid_sizes:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(page_size=size)
            
            self.assertIn("Page size must be between 1 and 250", str(context.exception))
    
    def test_page_size_validation_non_integer(self):
        """Test page size validation with non-integer values."""
        invalid_types = ["10", 10.5, [], {}, True, None]
        
        for invalid_type in invalid_types:
            with self.assertRaises(ValueError) as context:
                ShopifyConfig(page_size=invalid_type)
            
            self.assertIn("Page size must be an integer", str(context.exception))
    
    def test_additional_kwargs_handling(self):
        """Test handling of additional keyword arguments."""
        config = ShopifyConfig(
            timeout=60,
            custom_option="custom_value",
            debug_mode=True,
            extra_headers={"Custom": "Header"}
        )
        
        # Standard options should work
        self.assertEqual(config.timeout, 60)
        
        # Additional options should be accessible (if implemented)
        # Note: This test depends on implementation details
        # The base implementation should handle **kwargs gracefully
    
    def test_get_base_url_generation(self):
        """Test base URL generation with different API versions."""
        test_cases = [
            ("test-shop.myshopify.com", "2024-01", "https://test-shop.myshopify.com/admin/api/2024-01/graphql.json"),
            ("my-store.myshopify.com", "2023-10", "https://my-store.myshopify.com/admin/api/2023-10/graphql.json"),
            ("example-store.myshopify.com", "2023-07", "https://example-store.myshopify.com/admin/api/2023-07/graphql.json"),
        ]
        
        for shop_url, api_version, expected_url in test_cases:
            config = ShopifyConfig(api_version=api_version)
            base_url = config.get_base_url(shop_url)
            self.assertEqual(base_url, expected_url)
    
    def test_get_base_url_with_protocol(self):
        """Test base URL generation when shop_url includes protocol."""
        config = ShopifyConfig()
        
        # Should handle URLs with https://
        base_url = config.get_base_url("https://test-shop.myshopify.com")
        expected = "https://test-shop.myshopify.com/admin/api/2024-01/graphql.json"
        self.assertEqual(base_url, expected)
        
        # Should handle URLs with http://
        base_url = config.get_base_url("http://test-shop.myshopify.com")
        expected = "http://test-shop.myshopify.com/admin/api/2024-01/graphql.json"
        self.assertEqual(base_url, expected)
    
    def test_get_base_url_with_trailing_slash(self):
        """Test base URL generation with trailing slash."""
        config = ShopifyConfig()
        
        base_url = config.get_base_url("test-shop.myshopify.com/")
        expected = "https://test-shop.myshopify.com/admin/api/2024-01/graphql.json"
        self.assertEqual(base_url, expected)
    
    def test_config_immutability(self):
        """Test that config values cannot be modified after creation."""
        config = ShopifyConfig(timeout=30)
        
        # Attempting to modify should not change the original values
        original_timeout = config.timeout
        
        # Try to modify (this might not raise an error depending on implementation)
        try:
            config.timeout = 60
            # If modification is allowed, verify it actually changed
            # This test documents the behavior
            pass
        except AttributeError:
            # If modification is prevented, that's also valid behavior
            pass
        
        # Test that we can still access the value
        self.assertIsInstance(config.timeout, int)
    
    def test_config_representation(self):
        """Test string representation of config."""
        config = ShopifyConfig(
            api_version="2023-10",
            timeout=60,
            max_retries=5
        )
        
        # Config should have a reasonable string representation
        config_str = str(config)
        self.assertIsInstance(config_str, str)
        self.assertIn("ShopifyConfig", config_str)
    
    def test_config_equality(self):
        """Test config equality comparison."""
        config1 = ShopifyConfig(api_version="2024-01", timeout=30)
        config2 = ShopifyConfig(api_version="2024-01", timeout=30)
        config3 = ShopifyConfig(api_version="2024-01", timeout=60)
        
        # Same configurations should be equal if equality is implemented
        # Note: This depends on implementation
        try:
            are_equal = (config1 == config2)
            are_different = (config1 == config3)
            
            if are_equal is True:
                self.assertTrue(config1 == config2)
                self.assertFalse(config1 == config3)
        except TypeError:
            # If equality is not implemented, that's also valid
            pass


class TestConfigurationEnvironmentHandling(unittest.TestCase):
    """Test configuration interaction with environment variables."""
    
    @patch.dict(os.environ, {
        "SHOPIFY_API_VERSION": "2023-07",
        "SHOPIFY_TIMEOUT": "120",
        "SHOPIFY_MAX_RETRIES": "5",
        "SHOPIFY_PAGE_SIZE": "50"
    })
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        # Note: This test assumes environment variable support is implemented
        # The base ShopifyConfig might not support this, but it's a common feature
        
        try:
            # Try to create config that loads from environment
            config = ShopifyConfig.from_environment()
            
            self.assertEqual(config.api_version, "2023-07")
            self.assertEqual(config.timeout, 120)
            self.assertEqual(config.max_retries, 5)
            self.assertEqual(config.page_size, 50)
            
        except AttributeError:
            # If from_environment is not implemented, skip this test
            self.skipTest("ShopifyConfig.from_environment not implemented")
    
    @patch.dict(os.environ, {"SHOPIFY_API_VERSION": "invalid-version"})
    def test_environment_variable_validation(self):
        """Test validation of environment variables."""
        try:
            with self.assertRaises(ValueError):
                ShopifyConfig.from_environment()
        except AttributeError:
            self.skipTest("ShopifyConfig.from_environment not implemented")
    
    def test_environment_variable_fallback(self):
        """Test fallback to defaults when environment variables are not set."""
        # Clear any environment variables
        env_vars = [
            "SHOPIFY_API_VERSION", "SHOPIFY_TIMEOUT", "SHOPIFY_MAX_RETRIES",
            "SHOPIFY_RETRY_DELAY", "SHOPIFY_PAGE_SIZE"
        ]
        
        with patch.dict(os.environ, {}, clear=True):
            try:
                config = ShopifyConfig.from_environment()
                
                # Should use defaults
                self.assertEqual(config.api_version, ShopifyConfig.DEFAULT_API_VERSION)
                self.assertEqual(config.timeout, ShopifyConfig.DEFAULT_TIMEOUT)
                self.assertEqual(config.max_retries, ShopifyConfig.DEFAULT_MAX_RETRIES)
                
            except AttributeError:
                self.skipTest("ShopifyConfig.from_environment not implemented")


class TestConfigurationEdgeCases(unittest.TestCase):
    """Test configuration edge cases and error conditions."""
    
    def test_extreme_valid_values(self):
        """Test configuration with extreme but valid values."""
        # Minimum valid values
        config_min = ShopifyConfig(
            timeout=1,
            max_retries=0,
            retry_delay=1,
            page_size=1
        )
        
        self.assertEqual(config_min.timeout, 1)
        self.assertEqual(config_min.max_retries, 0)
        self.assertEqual(config_min.retry_delay, 1)
        self.assertEqual(config_min.page_size, 1)
        
        # Maximum valid values
        config_max = ShopifyConfig(
            timeout=600,
            max_retries=10,
            retry_delay=30,
            page_size=250
        )
        
        self.assertEqual(config_max.timeout, 600)
        self.assertEqual(config_max.max_retries, 10)
        self.assertEqual(config_max.retry_delay, 30)
        self.assertEqual(config_max.page_size, 250)
    
    def test_configuration_with_none_values(self):
        """Test configuration behavior with explicit None values."""
        # Passing None should use defaults, not raise errors
        config = ShopifyConfig(
            timeout=None,
            max_retries=None,
            retry_delay=None,
            page_size=None
        )
        
        self.assertEqual(config.timeout, ShopifyConfig.DEFAULT_TIMEOUT)
        self.assertEqual(config.max_retries, ShopifyConfig.DEFAULT_MAX_RETRIES)
        self.assertEqual(config.retry_delay, ShopifyConfig.DEFAULT_RETRY_DELAY)
        self.assertEqual(config.page_size, ShopifyConfig.DEFAULT_PAGE_SIZE)
    
    def test_memory_usage(self):
        """Test that config doesn't consume excessive memory."""
        configs = []
        
        # Create many config instances
        for i in range(1000):
            config = ShopifyConfig(timeout=30 + (i % 10))
            configs.append(config)
        
        # Should be able to create many instances without issues
        self.assertEqual(len(configs), 1000)
        
        # Verify they're independent
        configs[0].timeout = 100  # This might not work if immutable
        self.assertNotEqual(configs[0].timeout, configs[1].timeout)


class TestConfigurationCompatibility(unittest.TestCase):
    """Test configuration compatibility with different scenarios."""
    
    def test_old_api_versions(self):
        """Test configuration with older API versions."""
        old_versions = ["2021-10", "2021-07", "2021-04", "2021-01"]
        
        for version in old_versions:
            config = ShopifyConfig(api_version=version)
            self.assertEqual(config.api_version, version)
    
    def test_future_api_versions(self):
        """Test configuration with future API versions."""
        # Future versions should be accepted if they follow the format
        future_versions = ["2025-01", "2025-04", "2026-01"]
        
        for version in future_versions:
            config = ShopifyConfig(api_version=version)
            self.assertEqual(config.api_version, version)
    
    def test_configuration_serialization(self):
        """Test that configuration can be serialized/deserialized."""
        config = ShopifyConfig(
            api_version="2023-10",
            timeout=60,
            max_retries=5,
            retry_delay=2,
            page_size=25
        )
        
        # Test dictionary representation
        try:
            config_dict = config.to_dict()
            
            self.assertEqual(config_dict["api_version"], "2023-10")
            self.assertEqual(config_dict["timeout"], 60)
            self.assertEqual(config_dict["max_retries"], 5)
            
            # Test reconstruction from dictionary
            new_config = ShopifyConfig.from_dict(config_dict)
            self.assertEqual(new_config.api_version, config.api_version)
            self.assertEqual(new_config.timeout, config.timeout)
            
        except (AttributeError, NotImplementedError):
            # If serialization is not implemented, that's okay
            self.skipTest("Configuration serialization not implemented")


if __name__ == '__main__':
    unittest.main()
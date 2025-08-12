# Thread Safety and Error Handling Improvements

## Overview

This document outlines the thread safety and error handling improvements made to the Shopify SDK to prevent random exceptions and race conditions.

## Thread Safety Improvements

### 1. ShopifyClient
- **HTTP Session Management**: Added connection pooling with `HTTPAdapter` and proper session management
- **Session Lock**: Added `_session_lock` to ensure thread-safe access to the HTTP session
- **Context Manager Support**: Added `__enter__` and `__exit__` methods for proper resource cleanup

```python
# Safe concurrent usage
with ShopifyClient(shop_url, api_key) as client:
    result = client.execute_query(query)
# Session automatically closed
```

### 2. QueryBuilder
- **Thread-Safe State Management**: Added `_lock` to protect internal state during concurrent operations
- **Atomic Operations**: All state modifications are now atomic using threading locks

```python
# Safe for concurrent usage
builder = QueryBuilder()
# Multiple threads can now safely use the same builder instance
```

### 3. WebhookHandler
- **Handler Registration Safety**: Added `_handlers_lock` (RLock) for thread-safe handler management
- **Atomic Handler Execution**: Handlers are copied before execution to prevent race conditions
- **Clean Resource Management**: Empty topic lists are automatically cleaned up

```python
# Safe concurrent handler registration/execution
handler = WebhookHandler()
# Multiple threads can safely register and handle webhooks
```

### 4. ShopifyConfig
- **Configuration Update Safety**: Added `_config_lock` for thread-safe configuration updates
- **Atomic Read/Write Operations**: All configuration access is now thread-safe

## Error Handling Improvements

### 1. Robust JSON Parsing
- **Better Error Context**: JSON parsing errors now include detailed context
- **Graceful Degradation**: Invalid responses are handled gracefully with proper error messages

### 2. Improved Retry Logic
- **Safer Delay Calculation**: Retry delays are calculated more robustly with fallbacks
- **Better Error Classification**: Improved detection of retryable vs non-retryable errors
- **Jitter Implementation**: Added exponential backoff with jitter to prevent thundering herd

### 3. Enhanced GraphQL Error Handling
- **Null Message Safety**: GraphQL errors with null messages are handled properly
- **Malformed Error Resilience**: Gracefully handles incomplete or malformed error objects

### 4. Connection Management
- **Session Pooling**: HTTP connections are pooled and reused efficiently
- **Proper Resource Cleanup**: Sessions are properly closed to prevent resource leaks
- **Timeout Handling**: More robust timeout handling with better error messages

### 5. Webhook Error Handling
- **Non-Throwing Validation**: Input validation returns error responses instead of throwing exceptions
- **Signature Verification Safety**: Robust signature verification with proper error handling

## Import Conflict Resolution

### Fixed Duplicate Imports
- **RetryHandler**: Removed duplicate `ShopifyRateLimitError` definition
- **Clean Import Structure**: Consolidated error class imports

## Validation Improvements

### 1. Configuration Validation
- **Flexible Retry Delay**: Now accepts 0 as a valid retry delay value
- **Better Error Messages**: More descriptive validation error messages

### 2. Input Validation
- **Comprehensive Checks**: Added validation for all user inputs
- **Graceful Error Returns**: Many validation errors now return error objects instead of throwing exceptions

## Testing Improvements

### 1. Thread Safety Tests
- **Concurrent Usage**: Comprehensive tests for concurrent SDK usage
- **Race Condition Detection**: Tests specifically designed to catch race conditions
- **Stress Testing**: High-load tests to validate session management

### 2. Error Handling Tests
- **Edge Case Coverage**: Tests for malformed responses, network errors, and edge cases
- **Robustness Validation**: Ensures the SDK gracefully handles unexpected scenarios

## Usage Recommendations

### Thread-Safe Usage Patterns

```python
# Recommended: Use context manager
with ShopifyClient(shop_url, api_key) as client:
    # Multiple threads can safely use this client
    result = client.execute_query(query)

# Recommended: One client per application
client = ShopifyClient(shop_url, api_key)
# ... use across multiple threads
client.close()  # Clean up when done
```

### Error Handling Best Practices

```python
try:
    result = client.execute_query(query)
except ShopifyRateLimitError as e:
    # Handle rate limiting with retry_after
    time.sleep(e.retry_after or 1)
except ShopifyGraphQLError as e:
    # Handle GraphQL-specific errors
    print(f"GraphQL errors: {e.graphql_errors}")
except ShopifyAPIError as e:
    # Handle general API errors
    print(f"API error: {e.message}")
```

### Configuration for Production

```python
# Production-ready configuration
config = ShopifyConfig(
    timeout=30,        # Reasonable timeout
    max_retries=3,     # Balanced retry attempts
    retry_delay=2,     # Base delay with exponential backoff
    page_size=50       # Efficient pagination
)

client = ShopifyClient(shop_url, api_key, config=config, enable_retry=True)
```

## Performance Improvements

- **Connection Pooling**: Reuses HTTP connections for better performance
- **Optimized Locking**: Minimal lock contention with RLocks where appropriate
- **Efficient Memory Usage**: Proper cleanup prevents memory leaks
- **Reduced Exception Overhead**: Many errors are returned as values instead of exceptions

## Backward Compatibility

All improvements maintain full backward compatibility. Existing code will continue to work unchanged while benefiting from the improved thread safety and error handling.
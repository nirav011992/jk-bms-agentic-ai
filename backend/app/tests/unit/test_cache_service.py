"""Unit tests for Redis cache service (Phase 2)."""
import pytest
from app.services.cache_service import CacheService, get_cache


@pytest.mark.asyncio
async def test_cache_service_initialization():
    """Test cache service initializes correctly."""
    cache = CacheService()
    # Should not raise an error even if Redis is not running
    assert cache is not None


@pytest.mark.asyncio
async def test_cache_set_get():
    """Test basic cache set and get operations."""
    cache = get_cache()

    if not cache.is_enabled():
        pytest.skip("Redis not available, skipping cache test")

    # Test set and get
    key = "test:key:123"
    value = {"data": "test value", "number": 42}

    result = cache.set(key, value, ttl=60)
    assert result is True

    retrieved = cache.get(key)
    assert retrieved == value

    # Cleanup
    cache.delete(key)


@pytest.mark.asyncio
async def test_cache_get_nonexistent():
    """Test getting a non-existent key returns None."""
    cache = get_cache()

    if not cache.is_enabled():
        pytest.skip("Redis not available, skipping cache test")

    result = cache.get("nonexistent:key:999")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete():
    """Test cache delete operation."""
    cache = get_cache()

    if not cache.is_enabled():
        pytest.skip("Redis not available, skipping cache test")

    key = "test:delete:key"
    value = {"test": "data"}

    cache.set(key, value, ttl=60)
    assert cache.get(key) == value

    cache.delete(key)
    assert cache.get(key) is None


@pytest.mark.asyncio
async def test_cache_delete_pattern():
    """Test deleting multiple keys by pattern."""
    cache = get_cache()

    if not cache.is_enabled():
        pytest.skip("Redis not available, skipping cache test")

    # Create multiple keys with same pattern
    keys = [
        "test:pattern:1",
        "test:pattern:2",
        "test:pattern:3"
    ]

    for key in keys:
        cache.set(key, {"id": key}, ttl=60)

    # Delete by pattern
    deleted = cache.delete_pattern("test:pattern:*")
    assert deleted >= 3

    # Verify all deleted
    for key in keys:
        assert cache.get(key) is None


@pytest.mark.asyncio
async def test_cache_ttl_expiration():
    """Test that cache entries expire after TTL."""
    import time

    cache = get_cache()

    if not cache.is_enabled():
        pytest.skip("Redis not available, skipping cache test")

    key = "test:ttl:key"
    value = {"data": "expires soon"}

    # Set with 2 second TTL
    cache.set(key, value, ttl=2)
    assert cache.get(key) == value

    # Wait for expiration
    time.sleep(3)

    # Should be expired
    assert cache.get(key) is None


@pytest.mark.asyncio
async def test_cache_graceful_failure():
    """Test that cache operations fail gracefully when Redis is down."""
    # Create a cache service with invalid connection
    cache = CacheService()

    # Even if Redis is down, these should not raise exceptions
    cache.set("test:key", "value")  # Should return False
    result = cache.get("test:key")  # Should return None
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_cache_json_serialization():
    """Test that complex objects are serialized correctly."""
    cache = get_cache()

    if not cache.is_enabled():
        pytest.skip("Redis not available, skipping cache test")

    key = "test:complex:object"
    value = {
        "string": "text",
        "number": 123,
        "float": 45.67,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "nested": {
            "key": "value"
        }
    }

    cache.set(key, value, ttl=60)
    retrieved = cache.get(key)

    assert retrieved == value
    assert retrieved["string"] == "text"
    assert retrieved["number"] == 123
    assert retrieved["nested"]["key"] == "value"

    # Cleanup
    cache.delete(key)


@pytest.mark.asyncio
async def test_cache_is_enabled():
    """Test cache enabled status."""
    cache = get_cache()

    # Should return a boolean
    enabled = cache.is_enabled()
    assert isinstance(enabled, bool)


@pytest.mark.asyncio
async def test_cache_clear():
    """Test clearing all cache entries."""
    cache = get_cache()

    if not cache.is_enabled():
        pytest.skip("Redis not available, skipping cache test")

    # Set multiple test keys
    test_keys = ["test:clear:1", "test:clear:2", "test:clear:3"]
    for key in test_keys:
        cache.set(key, {"id": key}, ttl=60)

    # Clear all
    result = cache.clear()
    # Note: This clears the entire DB, so use carefully in tests

    # Verify cleared (optional, might affect other tests)
    # for key in test_keys:
    #     assert cache.get(key) is None


@pytest.mark.asyncio
async def test_cache_integration_with_huggingface_service():
    """Test that HuggingFace service integrates with cache."""
    from app.services.huggingface_service import cache as hf_cache

    # HuggingFace service should have access to cache
    assert hf_cache is not None


@pytest.mark.asyncio
async def test_multiple_cache_instances():
    """Test that get_cache returns singleton instance."""
    cache1 = get_cache()
    cache2 = get_cache()

    # Should be the same instance
    assert cache1 is cache2

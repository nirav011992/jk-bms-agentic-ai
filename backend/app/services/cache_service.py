"""Redis caching service for application-wide caching."""
import json
import logging
from typing import Any, Optional
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service for caching expensive operations."""

    def __init__(self):
        """Initialize Redis connection."""
        self._redis: Optional[Redis] = None
        self._enabled = True
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis server."""
        try:
            self._redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self._redis.ping()
            logger.info(f"Successfully connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except RedisError as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
            self._redis = None
            self._enabled = False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._redis = None
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled and self._redis is not None

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or cache disabled
        """
        if not self.is_enabled():
            return None

        try:
            value = self._redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error getting value from cache for key '{key}': {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default from settings)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            ttl = ttl or settings.CACHE_TTL
            serialized = json.dumps(value)
            self._redis.setex(key, ttl, serialized)
            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.warning(f"Error setting value in cache for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            self._redis.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Error deleting value from cache for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_enabled():
            return 0

        try:
            keys = self._redis.keys(pattern)
            if keys:
                return self._redis.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Error deleting keys with pattern '{pattern}': {e}")
            return 0

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            self._redis.flushdb()
            return True
        except RedisError as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            try:
                self._redis.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")


# Global cache instance
cache_service = CacheService()


def get_cache() -> CacheService:
    """Get the global cache service instance."""
    return cache_service

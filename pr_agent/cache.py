"""
Redis-based caching layer for PR Agent System.

Provides caching for expensive operations including:
- Full comment responses (1 hour TTL)
- Search results (24 hour TTL)
- Media research results (24 hour TTL)
"""

import json
import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import timedelta

logger = logging.getLogger(__name__)


class PRAgentCache:
    """Redis cache for PR agent responses and search results."""

    def __init__(self, redis_url: str = "redis://localhost:6379", enabled: bool = True):
        """
        Initialize the cache.

        Args:
            redis_url: Redis connection URL
            enabled: Whether caching is enabled (graceful degradation if False)
        """
        self.enabled = enabled
        self.redis_client = None

        if self.enabled:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info(f"Redis cache initialized successfully: {redis_url}")
            except ImportError:
                logger.warning(
                    "Redis not installed. Install with: pip install redis. "
                    "Cache will be disabled."
                )
                self.enabled = False
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis at {redis_url}: {e}. "
                    f"Cache will be disabled. Ensure Redis is running."
                )
                self.enabled = False

    def _make_key(self, prefix: str, **kwargs) -> str:
        """
        Create cache key from parameters.

        Args:
            prefix: Key prefix (e.g., "comment", "search")
            **kwargs: Key-value pairs to hash

        Returns:
            Cache key string
        """
        # Sort keys for consistency
        data = json.dumps(kwargs, sort_keys=True)
        hash_val = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"pr_agent:{prefix}:{hash_val}"

    def get_cached_response(
        self,
        executive_name: str,
        journalist_question: str,
        media_outlet: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached comment if available.

        Args:
            executive_name: Executive name
            journalist_question: Journalist's question
            media_outlet: Media outlet name

        Returns:
            Cached response dict or None if not found
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key(
                "comment",
                executive=executive_name.lower(),
                question=journalist_question.lower()[:200],  # Truncate for key size
                outlet=media_outlet.lower()
            )
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit for comment: {key}")
                return json.loads(cached)
            logger.debug(f"Cache miss for comment: {key}")
            return None
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {e}")
            return None

    def cache_response(
        self,
        response: Dict[str, Any],
        ttl: int = 3600  # 1 hour
    ) -> bool:
        """
        Cache generated comment.

        Args:
            response: Response dictionary containing executive_name, journalist_question, etc.
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            executive_name = response.get("executive_name", "")
            journalist_question = response.get("journalist_question", "")
            media_outlet = response.get("media_outlet", "")

            if not all([executive_name, journalist_question, media_outlet]):
                logger.warning("Cannot cache response: missing required fields")
                return False

            key = self._make_key(
                "comment",
                executive=executive_name.lower(),
                question=journalist_question.lower()[:200],
                outlet=media_outlet.lower()
            )

            # Store response
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(response)
            )
            logger.info(f"Cached comment response: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.warning(f"Error caching response: {e}")
            return False

    def get_cached_search_results(self, query: str) -> Optional[list]:
        """
        Retrieve cached search results.

        Args:
            query: Search query string

        Returns:
            Cached search results or None if not found
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key("search", query=query.lower()[:200])
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit for search: {key}")
                return json.loads(cached)
            logger.debug(f"Cache miss for search: {key}")
            return None
        except Exception as e:
            logger.warning(f"Error retrieving search from cache: {e}")
            return None

    def cache_search_results(
        self,
        query: str,
        results: list,
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """
        Cache search results.

        Args:
            query: Search query string
            results: Search results list
            ttl: Time-to-live in seconds (default: 24 hours)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            key = self._make_key("search", query=query.lower()[:200])
            self.redis_client.setex(key, ttl, json.dumps(results))
            logger.info(f"Cached search results: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Error caching search results: {e}")
            return False

    def get_cached_media_research(
        self,
        media_outlet: str,
        journalist_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached media research.

        Args:
            media_outlet: Media outlet name
            journalist_name: Optional journalist name

        Returns:
            Cached media research or None if not found
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key(
                "media",
                outlet=media_outlet.lower(),
                journalist=(journalist_name or "").lower()
            )
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit for media research: {key}")
                return json.loads(cached)
            logger.debug(f"Cache miss for media research: {key}")
            return None
        except Exception as e:
            logger.warning(f"Error retrieving media research from cache: {e}")
            return None

    def cache_media_research(
        self,
        media_outlet: str,
        journalist_name: Optional[str],
        research: Dict[str, Any],
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """
        Cache media research results.

        Args:
            media_outlet: Media outlet name
            journalist_name: Optional journalist name
            research: Research results
            ttl: Time-to-live in seconds (default: 24 hours)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            key = self._make_key(
                "media",
                outlet=media_outlet.lower(),
                journalist=(journalist_name or "").lower()
            )
            self.redis_client.setex(key, ttl, json.dumps(research))
            logger.info(f"Cached media research: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Error caching media research: {e}")
            return False

    def clear_cache(self, pattern: str = "pr_agent:*") -> int:
        """
        Clear cache entries matching pattern.

        Args:
            pattern: Redis key pattern (default: all pr_agent keys)

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries matching '{pattern}'")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Cache is disabled"
            }

        try:
            info = self.redis_client.info("stats")
            keys = self.redis_client.keys("pr_agent:*")
            return {
                "enabled": True,
                "total_keys": len(keys),
                "total_connections": info.get("total_connections_received", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                )
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }

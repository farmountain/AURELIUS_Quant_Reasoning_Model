"""
Redis cache manager for performance optimization
Provides caching utilities for strategies, backtests, and user data
"""
import os
import json
import redis
from typing import Optional, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"

# Cache TTL settings (in seconds)
CACHE_TTL = {
    "strategy": 300,  # 5 minutes
    "backtest": 600,  # 10 minutes
    "validation": 600,  # 10 minutes
    "user": 300,  # 5 minutes
    "gates": 300,  # 5 minutes
    "reflexion": 300,  # 5 minutes
}


class CacheManager:
    """Redis cache manager with fallback to no-op if Redis unavailable"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = REDIS_ENABLED
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Redis cache connected: {REDIS_HOST}:{REDIS_PORT}")
            except Exception as e:
                logger.warning(f"Redis unavailable, caching disabled: {e}")
                self.redis_client = None
                self.enabled = False
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create cache key with prefix"""
        return f"aurelius:{prefix}:{identifier}"
    
    def get(self, prefix: str, identifier: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            key = self._make_key(prefix, identifier)
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, prefix: str, identifier: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._make_key(prefix, identifier)
            ttl_seconds = ttl or CACHE_TTL.get(prefix, 300)
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl_seconds, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, prefix: str, identifier: str) -> bool:
        """Delete value from cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._make_key(prefix, identifier)
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(f"aurelius:{pattern}")
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.debug(f"Cache DELETE pattern: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache (use with caution)"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys("aurelius:*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cache CLEAR: {len(keys)} keys deleted")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
cache = CacheManager()


# Cache decorators for common patterns
def cache_strategy(func):
    """Decorator to cache strategy results"""
    async def wrapper(strategy_id: str, *args, **kwargs):
        cached = cache.get("strategy", strategy_id)
        if cached:
            return cached
        
        result = await func(strategy_id, *args, **kwargs)
        if result:
            cache.set("strategy", strategy_id, result)
        return result
    return wrapper


def cache_backtest(func):
    """Decorator to cache backtest results"""
    async def wrapper(backtest_id: str, *args, **kwargs):
        cached = cache.get("backtest", backtest_id)
        if cached:
            return cached
        
        result = await func(backtest_id, *args, **kwargs)
        if result:
            cache.set("backtest", backtest_id, result)
        return result
    return wrapper


def invalidate_strategy_cache(strategy_id: str):
    """Invalidate all cache related to a strategy"""
    cache.delete("strategy", strategy_id)
    cache.delete_pattern(f"backtest:*:{strategy_id}")
    cache.delete_pattern(f"validation:*:{strategy_id}")
    cache.delete_pattern(f"gates:*:{strategy_id}")
    logger.info(f"Invalidated cache for strategy: {strategy_id}")


def invalidate_user_cache(user_id: str):
    """Invalidate all cache related to a user"""
    cache.delete("user", user_id)
    logger.info(f"Invalidated cache for user: {user_id}")

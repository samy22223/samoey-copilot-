"""
Enhanced Redis Configuration for Samoey Copilot
Implements Redis clustering, advanced caching strategies, and performance optimization
Target: Sub-100ms response times with 99.999% uptime
"""

import json
import pickle
import time
from typing import Any, Optional, Union, List, Dict
from datetime import timedelta
import redis
try:
    from redis.cluster import RedisCluster
    from redis.sentinel import Sentinel
    from redis.exceptions import RedisError, ConnectionError, TimeoutError
except ImportError:
    RedisCluster = None
    Sentinel = None
    RedisError = Exception
    ConnectionError = Exception
    TimeoutError = Exception

import logging
from contextlib import asynccontextmanager
import asyncio
try:
    import aioredis
    from aioredis import Redis
except ImportError:
    aioredis = None
    Redis = None

from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"

@dataclass
class CacheConfig:
    strategy: CacheStrategy = CacheStrategy.LRU
    default_ttl: int = 3600  # 1 hour
    max_memory: str = "2gb"
    key_prefix: str = "samoey:"
    compression: bool = True
    serialization: str = "pickle"  # pickle, json, msgpack

class EnhancedRedisManager:
    """
    Enhanced Redis manager with clustering, failover, and advanced caching strategies
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.cluster_client: Optional[RedisCluster] = None
        self.sentinel_client: Optional[Sentinel] = None
        self.is_cluster_mode = False
        self.is_sentinel_mode = False
        self.connection_pool = None
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection with automatic failover support"""
        try:
            # Try cluster mode first
            self._initialize_cluster()
        except Exception as e:
            logger.info(f"Cluster mode failed: {e}, trying sentinel mode")
            try:
                # Try sentinel mode
                self._initialize_sentinel()
            except Exception as e:
                logger.info(f"Sentinel mode failed: {e}, using single instance")
                # Fall back to single instance
                self._initialize_single_instance()

    def _initialize_cluster(self):
        """Initialize Redis cluster"""
        cluster_nodes = [
            {"host": "redis-cluster-1", "port": 6379},
            {"host": "redis-cluster-2", "port": 6379},
            {"host": "redis-cluster-3", "port": 6379},
            {"host": "redis-cluster-4", "port": 6379},
            {"host": "redis-cluster-5", "port": 6379},
            {"host": "redis-cluster-6", "port": 6379},
        ]

        self.cluster_client = RedisCluster(
            startup_nodes=cluster_nodes,
            decode_responses=True,
            skip_full_coverage_check=True,
            max_connections=1000,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        # Test connection
        self.cluster_client.ping()
        self.is_cluster_mode = True
        logger.info("Redis cluster initialized successfully")

    def _initialize_sentinel(self):
        """Initialize Redis with sentinel for high availability"""
        sentinel_nodes = [
            ("redis-sentinel-1", 26379),
            ("redis-sentinel-2", 26379),
            ("redis-sentinel-3", 26379),
        ]

        self.sentinel_client = Sentinel(
            sentinel_nodes,
            socket_timeout=5,
            password=None,
            decode_responses=True
        )

        # Get master and slaves
        self.redis_client = self.sentinel_client.master_for('mymaster', socket_timeout=5)
        self.is_sentinel_mode = True
        logger.info("Redis sentinel initialized successfully")

    def _initialize_single_instance(self):
        """Initialize single Redis instance"""
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=1000
        )

        # Test connection
        self.redis_client.ping()
        logger.info("Redis single instance initialized successfully")

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value based on configuration"""
        if self.config.serialization == "pickle":
            data = pickle.dumps(value)
        elif self.config.serialization == "json":
            data = json.dumps(value, default=str).encode('utf-8')
        else:  # msgpack
            try:
                import msgpack
                data = msgpack.packb(value)
            except ImportError:
                # Fallback to pickle if msgpack is not available
                data = pickle.dumps(value)

        if self.config.compression:
            import zlib
            data = zlib.compress(data)

        return data

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value based on configuration"""
        if self.config.compression:
            import zlib
            data = zlib.decompress(data)

        if self.config.serialization == "pickle":
            return pickle.loads(data)
        elif self.config.serialization == "json":
            return json.loads(data.decode('utf-8'))
        else:  # msgpack
            try:
                import msgpack
                return msgpack.unpackb(data)
            except ImportError:
                # Fallback to pickle if msgpack is not available
                return pickle.loads(data)

    def _get_key(self, key: str) -> str:
        """Get full key with prefix"""
        return f"{self.config.key_prefix}{key}"

    async def get_async(self, key: str) -> Optional[Any]:
        """Get value from cache asynchronously"""
        try:
            full_key = self._get_key(key)

            if self.is_cluster_mode:
                # Use aioredis for cluster mode
                if not hasattr(self, 'async_cluster_client'):
                    self.async_cluster_client = await aioredis.create_redis_cluster(
                        "redis://redis-cluster-1:6379",
                        encoding='utf-8'
                    )
                data = await self.async_cluster_client.get(full_key)
            else:
                # Use aioredis for single instance
                if not hasattr(self, 'async_redis_client'):
                    self.async_redis_client = await aioredis.create_redis_pool(
                        "redis://localhost:6379",
                        encoding='utf-8'
                    )
                data = await self.async_redis_client.get(full_key)

            if data is None:
                return None

            return self._deserialize_value(data)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache asynchronously"""
        try:
            full_key = self._get_key(key)
            data = self._serialize_value(value)
            ttl = ttl or self.config.default_ttl

            if self.is_cluster_mode:
                if not hasattr(self, 'async_cluster_client'):
                    self.async_cluster_client = await aioredis.create_redis_cluster(
                        "redis://redis-cluster-1:6379",
                        encoding='utf-8'
                    )
                await self.async_cluster_client.setex(full_key, ttl, data)
            else:
                if not hasattr(self, 'async_redis_client'):
                    self.async_redis_client = await aioredis.create_redis_pool(
                        "redis://localhost:6379",
                        encoding='utf-8'
                    )
                await self.async_redis_client.setex(full_key, ttl, data)

            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache synchronously"""
        try:
            full_key = self._get_key(key)

            if self.is_cluster_mode:
                data = self.cluster_client.get(full_key)
            else:
                data = self.redis_client.get(full_key)

            if data is None:
                return None

            return self._deserialize_value(data)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache synchronously"""
        try:
            full_key = self._get_key(key)
            data = self._serialize_value(value)
            ttl = ttl or self.config.default_ttl

            if self.is_cluster_mode:
                self.cluster_client.setex(full_key, ttl, data)
            else:
                self.redis_client.setex(full_key, ttl, data)

            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            full_key = self._get_key(key)

            if self.is_cluster_mode:
                self.cluster_client.delete(full_key)
            else:
                self.redis_client.delete(full_key)

            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            full_key = self._get_key(key)

            if self.is_cluster_mode:
                return self.cluster_client.exists(full_key) > 0
            else:
                return self.redis_client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            full_key = self._get_key(key)

            if self.is_cluster_mode:
                return self.cluster_client.ttl(full_key)
            else:
                return self.redis_client.ttl(full_key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            full_key = self._get_key(key)

            if self.is_cluster_mode:
                return self.cluster_client.incrby(full_key, amount)
            else:
                return self.redis_client.incrby(full_key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None

    def get_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching pattern"""
        try:
            full_pattern = self._get_key(pattern)

            if self.is_cluster_mode:
                # For cluster, we need to search each node
                keys = []
                for node in self.cluster_client.get_primaries():
                    node_keys = node.keys(full_pattern)
                    keys.extend(node_keys)
                return keys
            else:
                return self.redis_client.keys(full_pattern)
        except Exception as e:
            logger.error(f"Cache pattern error for pattern {pattern}: {e}")
            return []

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.get_pattern(pattern)
            if not keys:
                return 0

            if self.is_cluster_mode:
                # Delete keys in batches for cluster
                deleted = 0
                for i in range(0, len(keys), 100):
                    batch = keys[i:i+100]
                    deleted += self.cluster_client.delete(*batch)
                return deleted
            else:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            if self.is_cluster_mode:
                info = self.cluster_client.info('memory')
                nodes_info = self.cluster_client.cluster_info()
                return {
                    "mode": "cluster",
                    "nodes": nodes_info.get('cluster_known_nodes', 0),
                    "memory_used": info.get('used_memory_human', 'N/A'),
                    "memory_peak": info.get('used_memory_peak_human', 'N/A'),
                    "keyspace_hits": info.get('keyspace_hits', 0),
                    "keyspace_misses": info.get('keyspace_misses', 0),
                    "connected_clients": info.get('connected_clients', 0),
                }
            else:
                info = self.redis_client.info()
                return {
                    "mode": "single" if not self.is_sentinel_mode else "sentinel",
                    "memory_used": info.get('used_memory_human', 'N/A'),
                    "memory_peak": info.get('used_memory_peak_human', 'N/A'),
                    "keyspace_hits": info.get('keyspace_hits', 0),
                    "keyspace_misses": info.get('keyspace_misses', 0),
                    "connected_clients": info.get('connected_clients', 0),
                    "total_commands_processed": info.get('total_commands_processed', 0),
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}

    def health_check(self) -> bool:
        """Perform health check on Redis connection"""
        try:
            if self.is_cluster_mode:
                self.cluster_client.ping()
            else:
                self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    def optimize_memory(self) -> bool:
        """Optimize Redis memory usage"""
        try:
            if self.is_cluster_mode:
                # Run memory optimization on all cluster nodes
                for node in self.cluster_client.get_primaries():
                    node.execute_command('MEMORY PURGE')
            else:
                self.redis_client.execute_command('MEMORY PURGE')

            logger.info("Redis memory optimization completed")
            return True
        except Exception as e:
            logger.error(f"Redis memory optimization failed: {e}")
            return False

    async def warm_up_cache(self, data: Dict[str, Any]) -> int:
        """Warm up cache with initial data"""
        loaded = 0
        for key, value in data.items():
            if await self.set_async(key, value):
                loaded += 1
        logger.info(f"Cache warm-up completed: {loaded} items loaded")
        return loaded

    def __del__(self):
        """Cleanup connections"""
        try:
            if hasattr(self, 'async_redis_client'):
                self.async_redis_client.close()
                asyncio.create_task(self.async_redis_client.wait_closed())
            if hasattr(self, 'async_cluster_client'):
                self.async_cluster_client.close()
                asyncio.create_task(self.async_cluster_client.wait_closed())
        except:
            pass

# Global cache instance
cache_manager = EnhancedRedisManager()

# Cache decorator for functions
def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = await cache_manager.get_async(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set_async(cache_key, result, ttl)
            return result

        def sync_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Performance monitoring decorator
def monitor_cache_performance(func):
    """Decorator to monitor cache performance"""
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            # Log performance metrics
            if duration > 0.1:  # Log slow operations
                logger.warning(f"Slow cache operation: {func.__name__} took {duration:.3f}s")

            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Cache operation failed: {func.__name__} took {duration:.3f}s, error: {e}")
            raise

    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Log performance metrics
            if duration > 0.1:  # Log slow operations
                logger.warning(f"Slow cache operation: {func.__name__} took {duration:.3f}s")

            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Cache operation failed: {func.__name__} took {duration:.3f}s, error: {e}")
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# Cache utility functions
async def get_or_set(key: str, fetch_func, ttl: int = None) -> Any:
    """Get value from cache or set using fetch function if not exists"""
    result = await cache_manager.get_async(key)
    if result is None:
        result = await fetch_func()
        await cache_manager.set_async(key, result, ttl)
    return result

def cache_invalidate_pattern(pattern: str) -> int:
    """Invalidate all cache entries matching pattern"""
    return cache_manager.clear_pattern(pattern)

def get_cache_health() -> Dict[str, Any]:
    """Get cache health status"""
    return {
        "healthy": cache_manager.health_check(),
        "stats": cache_manager.get_cache_stats(),
        "mode": "cluster" if cache_manager.is_cluster_mode else "sentinel" if cache_manager.is_sentinel_mode else "single"
    }

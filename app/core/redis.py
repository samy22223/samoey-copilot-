import redis
from typing import Optional
from app.core.config import settings

# Global Redis connection instance
redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """
    Get Redis client instance.
    Creates a new connection if one doesn't exist.
    """
    global redis_client

    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            # Test the connection
            redis_client.ping()
        except Exception as e:
            # If connection fails, try to create a new instance
            redis_client = redis.Redis(
                host=settings.REDIS_URL.split("://")[1].split(":")[0],
                port=int(settings.REDIS_URL.split(":")[-1].split("/")[0]),
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

    return redis_client


def close_redis_connection() -> None:
    """
    Close the Redis connection.
    """
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None


def init_redis() -> bool:
    """
    Initialize Redis connection and check if it's working.
    Returns True if connection is successful, False otherwise.
    """
    try:
        client = get_redis()
        client.ping()
        return True
    except Exception:
        return False


def redis_health_check() -> dict:
    """
    Perform a comprehensive Redis health check.
    Returns a dictionary with health status information.
    """
    try:
        client = get_redis()

        # Test basic operations
        start_time = __import__('time').time()
        client.ping()
        ping_time = (__import__('time').time() - start_time) * 1000

        # Get Redis info
        info = client.info()

        return {
            "status": "healthy",
            "ping_time_ms": round(ping_time, 2),
            "connected_clients": info.get('connected_clients', 0),
            "used_memory_human": info.get('used_memory_human', 'N/A'),
            "total_commands_processed": info.get('total_commands_processed', 0),
            "uptime_in_seconds": info.get('uptime_in_seconds', 0),
            "redis_version": info.get('redis_version', 'N/A')
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


class RedisManager:
    """
    A high-level Redis manager for common operations.
    """

    def __init__(self):
        self.client = get_redis()

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set a key-value pair with optional expiration.
        """
        try:
            return self.client.set(key, value, ex=ex)
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Get value by key.
        """
        try:
            return self.client.get(key)
        except Exception:
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key.
        """
        try:
            return bool(self.client.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        """
        try:
            return bool(self.client.exists(key))
        except Exception:
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        """
        try:
            return bool(self.client.expire(key, seconds))
        except Exception:
            return False

    def ttl(self, key: str) -> int:
        """
        Get time-to-live for a key.
        """
        try:
            return self.client.ttl(key)
        except Exception:
            return -1

    def hset(self, name: str, key: str, value: str) -> bool:
        """
        Set hash field.
        """
        try:
            return bool(self.client.hset(name, key, value))
        except Exception:
            return False

    def hget(self, name: str, key: str) -> Optional[str]:
        """
        Get hash field value.
        """
        try:
            return self.client.hget(name, key)
        except Exception:
            return None

    def hgetall(self, name: str) -> dict:
        """
        Get all hash fields and values.
        """
        try:
            return self.client.hgetall(name)
        except Exception:
            return {}

    def lpush(self, name: str, *values) -> int:
        """
        Push values to the left of a list.
        """
        try:
            return self.client.lpush(name, *values)
        except Exception:
            return 0

    def rpush(self, name: str, *values) -> int:
        """
        Push values to the right of a list.
        """
        try:
            return self.client.rpush(name, *values)
        except Exception:
            return 0

    def lpop(self, name: str) -> Optional[str]:
        """
        Pop value from the left of a list.
        """
        try:
            return self.client.lpop(name)
        except Exception:
            return None

    def rpop(self, name: str) -> Optional[str]:
        """
        Pop value from the right of a list.
        """
        try:
            return self.client.rpop(name)
        except Exception:
            return None

    def llen(self, name: str) -> int:
        """
        Get length of a list.
        """
        try:
            return self.client.llen(name)
        except Exception:
            return 0

    def sadd(self, name: str, *values) -> int:
        """
        Add members to a set.
        """
        try:
            return self.client.sadd(name, *values)
        except Exception:
            return 0

    def srem(self, name: str, *values) -> int:
        """
        Remove members from a set.
        """
        try:
            return self.client.srem(name, *values)
        except Exception:
            return 0

    def smembers(self, name: str) -> set:
        """
        Get all members of a set.
        """
        try:
            return self.client.smembers(name)
        except Exception:
            return set()

    def scard(self, name: str) -> int:
        """
        Get number of members in a set.
        """
        try:
            return self.client.scard(name)
        except Exception:
            return 0


# Convenience functions for backward compatibility
def redis_set(key: str, value: str, ex: Optional[int] = None) -> bool:
    """Set a key-value pair in Redis."""
    return RedisManager().set(key, value, ex)


def redis_get(key: str) -> Optional[str]:
    """Get a value from Redis."""
    return RedisManager().get(key)


def redis_delete(key: str) -> bool:
    """Delete a key from Redis."""
    return RedisManager().delete(key)


def redis_exists(key: str) -> bool:
    """Check if a key exists in Redis."""

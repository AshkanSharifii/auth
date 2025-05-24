from typing import Any
from redis.asyncio import Redis

from src.config import settings
from src.domain.interfaces.cache_client import ICacheClient


# ----------------------------------------------------------------------------
class RedisClient(ICacheClient):
    """
    Redis-based implementation of the ICacheClient interface.

    This class provides asynchronous methods to store and retrieve
    temporary verification codes in a Redis key-value store.

    Attributes:
        _r (Redis): Asynchronous Redis client instance.
    """

    def __init__(self):
        self._r = Redis(host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        decode_responses=True)

    async def store_code(self, key: str, value: str) -> Any:
        """
        Stores a verification code in Redis with an expiration time.

        Args:
            key (str): The key under which the code will be stored (e.g., user's phone number).
            value (str): The verification code to store.

        Returns:
            Any: Result of the Redis `set` operation. Typically, `True` if the key was set,
                 or `None` if the key already exists.

        Raises:
            Exception: If an error occurs while communicating with Redis.
        """
        try:
            response = await self._r.set(name=key, value=value, ex=settings.REDIS_KEY_EXPIRE_SECONDS, nx=True)
            return response
        except Exception as e:
            raise e

    async def retrieve_code(self, key: str) -> Any:
        """
        Retrieves a verification code from Redis by key.

        Args:
            key (str): The key associated with the stored verification code.

        Returns:
            Any: The stored value (e.g., verification code), or `None` if the key does not exist.

        Raises:
            Exception: If an error occurs while communicating with Redis.
        """
        try:
            value = await self._r.get(name=key)
            return value
        except Exception as e:
            raise e

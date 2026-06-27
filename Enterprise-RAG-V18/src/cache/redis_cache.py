# src/cache/redis_cache.py
import hashlib
import json
import logging
from typing import Optional, Any
from upstash_redis.asyncio import Redis
from tenacity import retry, wait_exponential, stop_after_attempt
from configs.settings import settings

logger = logging.getLogger(__name__)

class RedisCacheManager:
    def __init__(self):
        self.redis = None
        if settings.UPSTASH_REDIS_URL and settings.UPSTASH_REDIS_TOKEN:
            try:
                self.redis = Redis(url=settings.UPSTASH_REDIS_URL, token=settings.UPSTASH_REDIS_TOKEN)
            except Exception as e:
                logger.error(f"Failed to initialize Upstash Redis: {e}")
        else:
            logger.warning("Redis credentials not found. Cache will be disabled.")

    def _hash_key(self, key_seed: str) -> str:
        return hashlib.sha256(key_seed.encode("utf-8")).hexdigest()

    def _get_ttl(self, tier: int) -> int:
        ttls = {
            1: settings.CACHE_TTL_EMBEDDING,
            2: settings.CACHE_TTL_INTENT,
            3: settings.CACHE_TTL_SQL,
            4: settings.CACHE_TTL_SQL_RESULT,
            5: settings.CACHE_TTL_ANSWER
        }
        return ttls.get(tier, 3600)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def get(self, tier: int, key_seed: str) -> Optional[Any]:
        if not self.redis:
            return None
        try:
            key_hash = self._hash_key(key_seed)
            key = f"rag:{tier}:{key_hash}"
            val = await self.redis.get(key)
            if val:
                logger.debug(f"Cache HIT for tier {tier}, key {key}")
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return val
            logger.debug(f"Cache MISS for tier {tier}, key {key}")
            return None
        except Exception as e:
            logger.error(f"Redis get error tier {tier}: {e}")
            return None

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def set(self, tier: int, key_seed: str, value: Any) -> bool:
        if not self.redis:
            return False
        try:
            key_hash = self._hash_key(key_seed)
            key = f"rag:{tier}:{key_hash}"
            ttl = self._get_ttl(tier)
            
            if not isinstance(value, str):
                value = json.dumps(value)
                
            await self.redis.set(key, value, ex=ttl)
            logger.debug(f"Cache SET for tier {tier}, key {key}")
            return True
        except Exception as e:
            logger.error(f"Redis set error tier {tier}: {e}")
            return False

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def invalidate(self, tier: int, key_seed: str) -> bool:
        if not self.redis:
            return False
        try:
            key_hash = self._hash_key(key_seed)
            key = f"rag:{tier}:{key_hash}"
            await self.redis.delete(key)
            logger.debug(f"Cache INVALIDATE for tier {tier}, key {key}")
            return True
        except Exception as e:
            logger.error(f"Redis invalidate error tier {tier}: {e}")
            return False
            
    async def health_check(self) -> bool:
        if not self.redis:
            return False
        try:
            return await self.redis.ping() == "PONG"
        except Exception:
            return False

redis_cache = RedisCacheManager()

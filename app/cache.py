import redis.asyncio as aioredis
from redis.exceptions import RedisError

REDIS_URL = "redis://localhost:6379"
CACHE_TTL_SECONDS = 3600

client: aioredis.Redis | None = None

async def init_cache():
    global client
    client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)

async def close_cache():
    global client
    if client:
        await client.aclose()

async def get_cache_url(short_code: str) -> None | bytes | str:
    if client is None:
        return None

    try:
        return await client.get(f"url:{short_code}")

    except RedisError:
        return None

async def set_cache_url(short_code: str, original_url: str):
    if client is None:
        return

    try:
        await client.set(f"url:{short_code}",
                         original_url,
                         ex=CACHE_TTL_SECONDS)

    except RedisError:
        pass
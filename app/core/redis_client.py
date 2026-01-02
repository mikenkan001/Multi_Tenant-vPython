import redis.asyncio as redis
from app.core.config import settings
import json

class RedisClient:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.client = None
    
    async def connect(self):
        if self.redis_url:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self):
        if self.client:
            await self.client.close()
    
    async def get(self, key: str):
        if self.client:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
        return None
    
    async def set(self, key: str, value, expire: int = 300):
        if self.client:
            await self.client.setex(key, expire, json.dumps(value))
    
    async def delete(self, key: str):
        if self.client:
            await self.client.delete(key)

redis_client = RedisClient()
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import redis.asyncio as redis
from loguru import logger

from app.config import settings


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        self.redis_client = None
        self.requests_limit = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW

    async def get_redis_client(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Extract user ID
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        # Check rate limit
        redis_client = await self.get_redis_client()
        key = f"rate_limit:{user_id}"
        
        try:
            # Get current request count
            current_requests = await redis_client.get(key)
            
            if current_requests is None:
                # First request in window
                await redis_client.setex(key, self.window_seconds, 1)
                current_requests = 1
            else:
                current_requests = int(current_requests)
                
                if current_requests >= self.requests_limit:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    
                    # Record rate limit hit
                    from app.utils.metrics import record_rate_limit_hit
                    record_rate_limit_hit(user_id)
                    
                    if isinstance(event, Message):
                        await event.answer(
                            "⚠️ Слишком много запросов. Пожалуйста, подождите немного.",
                            show_alert=True
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "⚠️ Слишком много запросов. Пожалуйста, подождите немного.",
                            show_alert=True
                        )
                    return
                
                # Increment counter
                await redis_client.incr(key)
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # Continue without rate limiting if Redis is unavailable
        
        return await handler(event, data)
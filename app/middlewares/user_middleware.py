from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

from app.database.repositories import user_repo
from app.models import User
from app.utils.metrics import metrics
from app.utils.sentry import capture_error, set_user_context, add_breadcrumb


class UserMiddleware(BaseMiddleware):
    """Middleware to load and update user information"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Extract user info from event
        telegram_user = None
        if isinstance(event, (Message, CallbackQuery)):
            telegram_user = event.from_user

        if not telegram_user:
            return await handler(event, data)

        try:
            # Get or create user
            user = await user_repo.find_by_telegram_id(telegram_user.id)
            
            if not user:
                # Create new user
                user = User(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name or "Пользователь",
                    last_name=telegram_user.last_name,
                    display_name=telegram_user.first_name or "Пользователь",
                    language_code=telegram_user.language_code or "ru"
                )
                user = await user_repo.create(user)
                logger.info(f"Created new user: {user.telegram_id}")
                metrics.record_user_registration()
                add_breadcrumb(f"New user created: {user.telegram_id}", category="user", level="info")
            else:
                # Update user info if changed
                updated = False
                if user.username != telegram_user.username:
                    user.username = telegram_user.username
                    updated = True
                if user.first_name != telegram_user.first_name:
                    user.first_name = telegram_user.first_name or "Пользователь"
                    updated = True
                if user.last_name != telegram_user.last_name:
                    user.last_name = telegram_user.last_name
                    updated = True
                
                # Update activity
                user.update_activity()
                updated = True
                
                if updated:
                    await user_repo.update(user)
            
            # Set user context for Sentry
            set_user_context(
                user_id=user.telegram_id,
                username=user.username,
                display_name=user.display_name,
                is_admin=user.is_admin,
                registration_completed=user.registration_completed
            )
            
            # Add user to data context
            data["user"] = user
            
        except Exception as e:
            logger.error(f"User middleware error: {e}")
            capture_error(e, extra={
                "telegram_user_id": telegram_user.id,
                "context": "user_middleware"
            })
            # Continue without user context if error occurs
        
        return await handler(event, data)
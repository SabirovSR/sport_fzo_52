from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

from app.config import settings
from app.models import User


class AdminMiddleware(BaseMiddleware):
    """Middleware to check admin permissions"""
    
    def __init__(self, admin_only: bool = True, super_admin_only: bool = False):
        self.admin_only = admin_only
        self.super_admin_only = super_admin_only

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user: User = data.get("user")
        
        if not user:
            logger.warning("Admin middleware: No user in context")
            return

        # Check super admin permissions
        if self.super_admin_only:
            if not user.is_super_admin and user.telegram_id not in settings.super_admin_ids_list:
                if isinstance(event, Message):
                    await event.answer("❌ У вас нет прав для выполнения этой команды.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ У вас нет прав для выполнения этого действия.", show_alert=True)
                return

        # Check admin permissions
        elif self.admin_only:
            if not user.is_admin and not user.is_super_admin and user.telegram_id not in settings.super_admin_ids_list:
                if isinstance(event, Message):
                    await event.answer("❌ У вас нет прав для выполнения этой команды.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ У вас нет прав для выполнения этого действия.", show_alert=True)
                return

        return await handler(event, data)
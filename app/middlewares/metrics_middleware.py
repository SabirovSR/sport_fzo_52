"""
Metrics middleware for tracking bot interactions
"""
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineQuery
from loguru import logger

from app.utils.metrics import metrics


class MetricsMiddleware(BaseMiddleware):
    """Middleware to collect metrics from bot interactions"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        start_time = time.time()
        
        # Track update type
        update_type = type(event).__name__.lower()
        metrics.record_telegram_update(update_type)
        
        # Track specific event types
        try:
            if isinstance(event, Message):
                await self._handle_message_metrics(event)
            elif isinstance(event, CallbackQuery):
                await self._handle_callback_query_metrics(event)
            elif isinstance(event, InlineQuery):
                metrics.record_telegram_update('inline_query')
            
            # Execute handler
            result = await handler(event, data)
            
            # Track successful processing
            duration = time.time() - start_time
            logger.debug(f"Processed {update_type} in {duration:.3f}s")
            
            return result
            
        except Exception as e:
            # Track errors
            metrics.record_error(type(e).__name__, 'bot_handler')
            duration = time.time() - start_time
            logger.error(f"Error processing {update_type} in {duration:.3f}s: {e}")
            raise
    
    async def _handle_message_metrics(self, message: Message):
        """Handle message-specific metrics"""
        # Track message type
        if message.text and message.text.startswith('/'):
            # Command
            command = message.text.split()[0][1:]  # Remove '/' and get first part
            metrics.record_command(command)
        elif message.text:
            # Regular text message
            metrics.record_telegram_update('text_message')
        elif message.photo:
            metrics.record_telegram_update('photo_message')
        elif message.document:
            metrics.record_telegram_update('document_message')
        elif message.voice:
            metrics.record_telegram_update('voice_message')
        elif message.video:
            metrics.record_telegram_update('video_message')
        elif message.sticker:
            metrics.record_telegram_update('sticker_message')
        elif message.contact:
            metrics.record_telegram_update('contact_message')
        elif message.location:
            metrics.record_telegram_update('location_message')
        
        # Track chat type
        chat_type = message.chat.type
        metrics.record_message_sent(chat_type)
    
    async def _handle_callback_query_metrics(self, callback_query: CallbackQuery):
        """Handle callback query-specific metrics"""
        if callback_query.data:
            # Extract action from callback data (assuming format like "action:param")
            action = callback_query.data.split(':')[0] if ':' in callback_query.data else callback_query.data
            metrics.record_callback_query(action)
        else:
            metrics.record_callback_query('unknown')
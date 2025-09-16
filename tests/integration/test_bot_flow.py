"""Integration tests for bot flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, User as TelegramUser, Contact

from app.handlers import start_router, catalog_router, applications_router, admin_router, health_router
from app.middlewares import RateLimitMiddleware, UserMiddleware, MetricsMiddleware


class TestBotIntegration:
    """Test bot integration flow."""
    
    @pytest.fixture
    async def bot_and_dispatcher(self, test_settings):
        """Create bot and dispatcher for testing."""
        bot = Bot(
            token=test_settings.BOT_TOKEN,
            default=MagicMock()
        )
        dp = Dispatcher()
        
        # Register middlewares
        dp.message.middleware(MetricsMiddleware())
        dp.callback_query.middleware(MetricsMiddleware())
        dp.message.middleware(RateLimitMiddleware())
        dp.callback_query.middleware(RateLimitMiddleware())
        dp.message.middleware(UserMiddleware())
        dp.callback_query.middleware(UserMiddleware())
        
        # Register routers
        dp.include_router(start_router)
        dp.include_router(catalog_router)
        dp.include_router(applications_router)
        dp.include_router(admin_router)
        dp.include_router(health_router)
        
        yield bot, dp
        
        await bot.session.close()
    
    @pytest.mark.asyncio
    async def test_start_command_flow(self, bot_and_dispatcher, sample_user: User):
        """Test complete start command flow."""
        bot, dp = bot_and_dispatcher
        
        # Mock message
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = sample_user.telegram_id
        message.from_user.username = sample_user.username
        message.from_user.first_name = sample_user.first_name
        message.from_user.last_name = sample_user.last_name
        message.from_user.language_code = sample_user.language_code
        message.text = "/start"
        message.answer = AsyncMock()
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=None)
            user_repo.create = AsyncMock(return_value=sample_user)
            m.setattr("app.handlers.start.user_repo", user_repo)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            # Process message
            await dp.feed_update(bot, message)
            
            # Verify message was sent
            message.answer.assert_called()
    
    @pytest.mark.asyncio
    async def test_registration_flow(self, bot_and_dispatcher, sample_user: User):
        """Test complete registration flow."""
        bot, dp = bot_and_dispatcher
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)
            user_repo.update = AsyncMock()
            m.setattr("app.handlers.start.user_repo", user_repo)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            # Test name input
            message = MagicMock(spec=Message)
            message.from_user = MagicMock(spec=TelegramUser)
            message.from_user.id = sample_user.telegram_id
            message.text = "John Doe"
            message.answer = AsyncMock()
            
            # Process name input
            await dp.feed_update(bot, message)
            
            # Verify user was updated
            user_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_phone_registration_flow(self, bot_and_dispatcher, sample_user: User):
        """Test phone registration flow."""
        bot, dp = bot_and_dispatcher
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)
            user_repo.update = AsyncMock()
            m.setattr("app.handlers.start.user_repo", user_repo)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            # Test phone contact
            message = MagicMock(spec=Message)
            message.from_user = MagicMock(spec=TelegramUser)
            message.from_user.id = sample_user.telegram_id
            message.contact = MagicMock(spec=Contact)
            message.contact.phone_number = "+1234567890"
            message.answer = AsyncMock()
            
            # Process phone contact
            await dp.feed_update(bot, message)
            
            # Verify user was updated
            user_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_callback_query_flow(self, bot_and_dispatcher, sample_user: User):
        """Test callback query flow."""
        bot, dp = bot_and_dispatcher
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            # Mock callback query
            callback = MagicMock(spec=CallbackQuery)
            callback.from_user = MagicMock(spec=TelegramUser)
            callback.from_user.id = sample_user.telegram_id
            callback.data = "main_menu"
            callback.message = MagicMock()
            callback.message.edit_text = AsyncMock()
            callback.answer = AsyncMock()
            
            # Process callback query
            await dp.feed_update(bot, callback)
            
            # Verify callback was processed
            callback.answer.assert_called()


class TestErrorHandling:
    """Test error handling in bot flow."""
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, bot_and_dispatcher, sample_user: User):
        """Test handling of unknown command."""
        bot, dp = bot_and_dispatcher
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            # Mock message with unknown command
            message = MagicMock(spec=Message)
            message.from_user = MagicMock(spec=TelegramUser)
            message.from_user.id = sample_user.telegram_id
            message.text = "/unknown_command"
            message.answer = AsyncMock()
            
            # Process message
            await dp.feed_update(bot, message)
            
            # Bot should handle unknown commands gracefully
            # (no exception should be raised)
    
    @pytest.mark.asyncio
    async def test_invalid_callback_data(self, bot_and_dispatcher, sample_user: User):
        """Test handling of invalid callback data."""
        bot, dp = bot_and_dispatcher
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            # Mock callback query with invalid data
            callback = MagicMock(spec=CallbackQuery)
            callback.from_user = MagicMock(spec=TelegramUser)
            callback.from_user.id = sample_user.telegram_id
            callback.data = "invalid_callback_data"
            callback.message = MagicMock()
            callback.message.edit_text = AsyncMock()
            callback.answer = AsyncMock()
            
            # Process callback query
            await dp.feed_update(bot, callback)
            
            # Bot should handle invalid callbacks gracefully
            # (no exception should be raised)
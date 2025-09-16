"""Unit tests for middlewares."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery, User as TelegramUser
from aiogram.fsm.context import FSMContext

from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.user_middleware import UserMiddleware
from app.middlewares.metrics_middleware import MetricsMiddleware


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create RateLimitMiddleware instance."""
        return RateLimitMiddleware()
    
    @pytest.mark.asyncio
    async def test_rate_limit_allow(self, middleware: RateLimitMiddleware):
        """Test rate limit allows requests within limit."""
        # Mock handler
        handler = AsyncMock()
        
        # Mock message
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        
        # Mock data
        data = {}
        
        # Call middleware
        await middleware(message, handler, data)
        
        # Verify handler was called
        handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_block(self, middleware: RateLimitMiddleware):
        """Test rate limit blocks requests over limit."""
        # Mock handler
        handler = AsyncMock()
        
        # Mock message
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        message.answer = AsyncMock()
        
        # Mock data
        data = {}
        
        # Simulate multiple rapid requests
        for _ in range(35):  # Over the default limit of 30
            await middleware(message, handler, data)
        
        # Verify handler was not called for the last request
        # and rate limit message was sent
        message.answer.assert_called()


class TestUserMiddleware:
    """Test UserMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create UserMiddleware instance."""
        return UserMiddleware()
    
    @pytest.mark.asyncio
    async def test_user_middleware_creates_user(self, middleware: UserMiddleware, sample_user: User):
        """Test user middleware creates user if not exists."""
        # Mock handler
        handler = AsyncMock()
        
        # Mock message
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = sample_user.telegram_id
        message.from_user.username = sample_user.username
        message.from_user.first_name = sample_user.first_name
        message.from_user.last_name = sample_user.last_name
        message.from_user.language_code = sample_user.language_code
        
        # Mock data
        data = {}
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=None)
            user_repo.create = AsyncMock(return_value=sample_user)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            await middleware(message, handler, data)
            
            # Verify user was created
            user_repo.create.assert_called_once()
            # Verify user is in data
            assert "user" in data
            assert data["user"] == sample_user
    
    @pytest.mark.asyncio
    async def test_user_middleware_existing_user(self, middleware: UserMiddleware, sample_user: User):
        """Test user middleware with existing user."""
        # Mock handler
        handler = AsyncMock()
        
        # Mock message
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = sample_user.telegram_id
        
        # Mock data
        data = {}
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.get_by_telegram_id = AsyncMock(return_value=sample_user)
            m.setattr("app.middlewares.user_middleware.user_repo", user_repo)
            
            await middleware(message, handler, data)
            
            # Verify user was retrieved
            user_repo.get_by_telegram_id.assert_called_once_with(sample_user.telegram_id)
            # Verify user is in data
            assert "user" in data
            assert data["user"] == sample_user


class TestMetricsMiddleware:
    """Test MetricsMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create MetricsMiddleware instance."""
        return MetricsMiddleware()
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_message(self, middleware: MetricsMiddleware):
        """Test metrics middleware for message."""
        # Mock handler
        handler = AsyncMock()
        
        # Mock message
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        
        # Mock data
        data = {}
        
        # Mock metrics
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.middlewares.metrics_middleware.metrics", MagicMock())
            
            await middleware(message, handler, data)
            
            # Verify handler was called
            handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_callback(self, middleware: MetricsMiddleware):
        """Test metrics middleware for callback query."""
        # Mock handler
        handler = AsyncMock()
        
        # Mock callback query
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = MagicMock(spec=TelegramUser)
        callback.from_user.id = 123456
        
        # Mock data
        data = {}
        
        # Mock metrics
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.middlewares.metrics_middleware.metrics", MagicMock())
            
            await middleware(callback, handler, data)
            
            # Verify handler was called
            handler.assert_called_once()
"""Unit tests for handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery, User as TelegramUser, Contact
from aiogram.fsm.context import FSMContext

from app.handlers.start import RegistrationStates, start_command, process_name, process_phone_contact, skip_phone
from app.models import User


class TestStartHandlers:
    """Test start handlers."""
    
    @pytest.mark.asyncio
    async def test_start_command_new_user(self, sample_user: User):
        """Test /start command for new user."""
        # Mock message and state
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()
        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.set_state = AsyncMock()
        
        # Set user as not registered
        sample_user.registration_completed = False
        
        await start_command(message, state, sample_user)
        
        # Verify calls
        state.clear.assert_called_once()
        message.answer.assert_called_once()
        state.set_state.assert_called_once_with(RegistrationStates.waiting_for_name)
    
    @pytest.mark.asyncio
    async def test_start_command_registered_user(self, sample_user: User):
        """Test /start command for registered user."""
        # Mock message and state
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()
        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        
        # Set user as registered
        sample_user.registration_completed = True
        
        await start_command(message, state, sample_user)
        
        # Verify calls
        state.clear.assert_called_once()
        message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_name_valid(self, sample_user: User):
        """Test process_name with valid input."""
        # Mock message and state
        message = MagicMock(spec=Message)
        message.text = "John Doe"
        message.answer = AsyncMock()
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.handlers.start.user_repo", MagicMock())
            user_repo = MagicMock()
            user_repo.update = AsyncMock()
            m.setattr("app.handlers.start.user_repo", user_repo)
            
            await process_name(message, state, sample_user)
            
            # Verify calls
            assert sample_user.display_name == "John Doe"
            user_repo.update.assert_called_once_with(sample_user)
            message.answer.assert_called_once()
            state.set_state.assert_called_once_with(RegistrationStates.waiting_for_phone)
    
    @pytest.mark.asyncio
    async def test_process_name_invalid(self, sample_user: User):
        """Test process_name with invalid input."""
        # Mock message and state
        message = MagicMock(spec=Message)
        message.text = "A"  # Too short
        message.answer = AsyncMock()
        state = MagicMock(spec=FSMContext)
        
        await process_name(message, state, sample_user)
        
        # Verify error message
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "корректное имя" in call_args
    
    @pytest.mark.asyncio
    async def test_process_phone_contact(self, sample_user: User):
        """Test process_phone_contact with contact."""
        # Mock message and state
        message = MagicMock(spec=Message)
        contact = MagicMock(spec=Contact)
        contact.phone_number = "+1234567890"
        message.contact = contact
        message.answer = AsyncMock()
        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.update = AsyncMock()
            m.setattr("app.handlers.start.user_repo", user_repo)
            
            await process_phone_contact(message, state, sample_user)
            
            # Verify user data update
            assert sample_user.phone == "+1234567890"
            assert sample_user.phone_shared is True
            assert sample_user.registration_completed is True
            user_repo.update.assert_called_once_with(sample_user)
            state.clear.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skip_phone(self, sample_user: User):
        """Test skip_phone functionality."""
        # Mock message and state
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()
        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        
        # Mock user repository
        with pytest.MonkeyPatch().context() as m:
            user_repo = MagicMock()
            user_repo.update = AsyncMock()
            m.setattr("app.handlers.start.user_repo", user_repo)
            
            await skip_phone(message, state, sample_user)
            
            # Verify user data update
            assert sample_user.phone_shared is False
            assert sample_user.registration_completed is True
            user_repo.update.assert_called_once_with(sample_user)
            state.clear.assert_called_once()


class TestCallbackHandlers:
    """Test callback handlers."""
    
    @pytest.mark.asyncio
    async def test_main_menu_callback(self, sample_user: User):
        """Test main menu callback."""
        # Mock callback query
        callback = MagicMock(spec=CallbackQuery)
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.handlers.start.get_welcome_text", lambda user: "Welcome!")
            m.setattr("app.handlers.start.get_main_menu_keyboard", lambda: None)
            
            from app.handlers.start import main_menu_callback
            await main_menu_callback(callback, sample_user)
            
            # Verify calls
            callback.message.edit_text.assert_called_once()
            callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_help_callback(self, sample_user: User):
        """Test help callback."""
        # Mock callback query
        callback = MagicMock(spec=CallbackQuery)
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.handlers.start.get_main_menu_keyboard", lambda: None)
            
            from app.handlers.start import help_callback
            await help_callback(callback)
            
            # Verify calls
            callback.message.edit_text.assert_called_once()
            callback.answer.assert_called_once()
            # Check that help text contains expected content
            call_args = callback.message.edit_text.call_args[0][0]
            assert "Помощь по использованию бота" in call_args
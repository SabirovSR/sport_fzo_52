from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for requesting phone number"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📱 Поделиться номером телефона", request_contact=True)
    )
    builder.row(
        KeyboardButton(text="❌ Пропустить")
    )
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Simple cancel keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отмена"))
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_admin_action_keyboard() -> ReplyKeyboardMarkup:
    """Admin action keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="✅ Принять"),
        KeyboardButton(text="📤 Передать")
    )
    builder.row(
        KeyboardButton(text="🎉 Выполнено"),
        KeyboardButton(text="❌ Отклонить")
    )
    builder.row(
        KeyboardButton(text="🔙 Назад")
    )
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard"""
    return ReplyKeyboardRemove()
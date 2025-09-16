from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import District, FOK, Application


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🏢 Каталог ФОКов", callback_data="catalog_main")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_applications")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск по видам спорта", callback_data="search_sports")
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
    )
    
    return builder.as_markup()


def get_catalog_districts_keyboard(districts: List[District], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Districts catalog keyboard with pagination"""
    builder = InlineKeyboardBuilder()
    
    # Calculate pagination
    start_idx = page * per_page
    end_idx = start_idx + per_page
    districts_page = districts[start_idx:end_idx]
    
    # Add district buttons (2 per row)
    for i in range(0, len(districts_page), 2):
        row_buttons = []
        for j in range(2):
            if i + j < len(districts_page):
                district = districts_page[i + j]
                row_buttons.append(
                    InlineKeyboardButton(
                        text=f"📍 {district.name}",
                        callback_data=f"district_{district.id}"
                    )
                )
        builder.row(*row_buttons)
    
    # Pagination buttons
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"districts_page_{page-1}")
        )
    if end_idx < len(districts):
        pagination_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"districts_page_{page+1}")
        )
    
    if pagination_buttons:
        builder.row(*pagination_buttons)
    
    # Back to main menu
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_foks_keyboard(foks: List[FOK], district_name: str, page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """FOKs list keyboard with pagination"""
    builder = InlineKeyboardBuilder()
    
    # Calculate pagination
    start_idx = page * per_page
    end_idx = start_idx + per_page
    foks_page = foks[start_idx:end_idx]
    
    # Add FOK buttons
    for fok in foks_page:
        builder.row(
            InlineKeyboardButton(
                text=f"🏢 {fok.name}",
                callback_data=f"fok_{fok.id}"
            )
        )
    
    # Pagination buttons
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"foks_page_{district_name}_{page-1}")
        )
    if end_idx < len(foks):
        pagination_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"foks_page_{district_name}_{page+1}")
        )
    
    if pagination_buttons:
        builder.row(*pagination_buttons)
    
    # Navigation buttons
    builder.row(
        InlineKeyboardButton(text="🔙 К районам", callback_data="catalog_main"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_fok_card_keyboard(fok: FOK, user_has_applied: bool = False, can_apply: bool = True) -> InlineKeyboardMarkup:
    """FOK card keyboard"""
    builder = InlineKeyboardBuilder()
    
    # Application button
    if can_apply:
        if user_has_applied:
            builder.row(
                InlineKeyboardButton(text="✅ Заявка подана", callback_data="application_submitted")
            )
        else:
            builder.row(
                InlineKeyboardButton(text="📝 Оставить заявку", callback_data=f"apply_{fok.id}")
            )
    else:
        builder.row(
            InlineKeyboardButton(
                text="❌ Для подачи заявки нужен номер телефона",
                callback_data="need_phone"
            )
        )
    
    # Navigation buttons
    builder.row(
        InlineKeyboardButton(text="🔙 К ФОКам района", callback_data=f"district_back_{fok.district}"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_applications_keyboard(applications: List[Application], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """User applications keyboard with pagination"""
    builder = InlineKeyboardBuilder()
    
    if not applications:
        builder.row(
            InlineKeyboardButton(text="📝 Подать первую заявку", callback_data="catalog_main")
        )
    else:
        # Calculate pagination
        start_idx = page * per_page
        end_idx = start_idx + per_page
        apps_page = applications[start_idx:end_idx]
        
        # Add application buttons
        for app in apps_page:
            status_emoji = {
                "pending": "⏳",
                "accepted": "✅", 
                "transferred": "📤",
                "completed": "🎉",
                "cancelled": "❌",
                "rejected": "🚫"
            }.get(app.status, "📋")
            
            builder.row(
                InlineKeyboardButton(
                    text=f"{status_emoji} {app.fok_name}",
                    callback_data=f"application_{app.id}"
                )
            )
        
        # Pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"apps_page_{page-1}")
            )
        if end_idx < len(applications):
            pagination_buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"apps_page_{page+1}")
            )
        
        if pagination_buttons:
            builder.row(*pagination_buttons)
    
    # Back to main menu
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_application_card_keyboard(application: Application) -> InlineKeyboardMarkup:
    """Application card keyboard"""
    builder = InlineKeyboardBuilder()
    
    # Cancel button (if applicable)
    if application.can_be_cancelled:
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить заявку",
                callback_data=f"cancel_app_{application.id}"
            )
        )
    
    # Navigation buttons
    builder.row(
        InlineKeyboardButton(text="🔙 К моим заявкам", callback_data="my_applications"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_cancel_confirmation_keyboard(application_id: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard for application cancellation"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да, отменить", callback_data=f"confirm_cancel_{application_id}"),
        InlineKeyboardButton(text="❌ Нет, оставить", callback_data=f"application_{application_id}")
    )
    
    return builder.as_markup()


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users"),
        InlineKeyboardButton(text="🏢 Управление ФОКами", callback_data="admin_foks")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Управление заявками", callback_data="admin_applications"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    builder.row(
        InlineKeyboardButton(text="📁 Районы и спорт", callback_data="admin_references"),
        InlineKeyboardButton(text="📈 Отчеты", callback_data="admin_reports")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_sports_filter_keyboard(sports: List, selected_sports: List[str] = None) -> InlineKeyboardMarkup:
    """Sports filter keyboard"""
    builder = InlineKeyboardBuilder()
    
    if selected_sports is None:
        selected_sports = []
    
    # Add sport buttons (2 per row)
    for i in range(0, len(sports), 2):
        row_buttons = []
        for j in range(2):
            if i + j < len(sports):
                sport = sports[i + j]
                is_selected = sport.name in selected_sports
                prefix = "✅" if is_selected else "⬜"
                row_buttons.append(
                    InlineKeyboardButton(
                        text=f"{prefix} {sport.display_name}",
                        callback_data=f"toggle_sport_{sport.name}"
                    )
                )
        builder.row(*row_buttons)
    
    # Action buttons
    if selected_sports:
        builder.row(
            InlineKeyboardButton(text="🔍 Найти ФОКи", callback_data="search_by_sports"),
            InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_sports")
        )
    
    # Back button
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_back_keyboard(callback_data: str, text: str = "🔙 Назад") -> InlineKeyboardMarkup:
    """Simple back button keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    return builder.as_markup()
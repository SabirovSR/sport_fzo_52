from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, Contact
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from app.models import User
from app.database.repositories import user_repo
from app.keyboards.inline import get_main_menu_keyboard
from app.keyboards.reply import get_phone_request_keyboard, remove_keyboard


router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, user: User):
    """Handle /start command"""
    await state.clear()
    
    if not user.registration_completed:
        await message.answer(
            f"👋 Добро пожаловать в бот каталога физкультурно-оздоровительных комплексов!\n\n"
            f"Я помогу вам найти подходящий ФОК и подать заявку на посещение.\n\n"
            f"Для начала, скажите, как к вам обращаться?",
            reply_markup=remove_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        await show_main_menu(message, user)


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext, user: User):
    """Process user name input"""
    if not message.text or len(message.text.strip()) < 2:
        await message.answer(
            "❌ Пожалуйста, введите корректное имя (минимум 2 символа)."
        )
        return
    
    display_name = message.text.strip()
    user.display_name = display_name
    await user_repo.update(user)
    
    await message.answer(
        f"Приятно познакомиться, {display_name}! 😊\n\n"
        f"Теперь мне нужен ваш номер телефона для возможности подачи заявок в ФОКи.\n\n"
        f"📱 Вы можете поделиться номером телефона или пропустить этот шаг.\n"
        f"⚠️ Без номера телефона вы не сможете подавать заявки.",
        reply_markup=get_phone_request_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext, user: User):
    """Process phone number from contact"""
    contact: Contact = message.contact
    
    user.phone = contact.phone_number
    user.phone_shared = True
    user.registration_completed = True
    await user_repo.update(user)
    
    await message.answer(
        f"✅ Отлично! Регистрация завершена.\n\n"
        f"Теперь вы можете пользоваться всеми функциями бота, включая подачу заявок в ФОКи.",
        reply_markup=remove_keyboard()
    )
    
    await state.clear()
    await show_main_menu(message, user)


@router.message(RegistrationStates.waiting_for_phone, F.text.in_(["❌ Пропустить", "/skip"]))
async def skip_phone(message: Message, state: FSMContext, user: User):
    """Skip phone number input"""
    user.phone_shared = False
    user.registration_completed = True
    await user_repo.update(user)
    
    await message.answer(
        f"📝 Регистрация завершена.\n\n"
        f"⚠️ Вы пропустили указание номера телефона. Вы сможете просматривать каталог ФОКов, "
        f"но не сможете подавать заявки.\n\n"
        f"Вы всегда можете добавить номер телефона в настройках.",
        reply_markup=remove_keyboard()
    )
    
    await state.clear()
    await show_main_menu(message, user)


@router.message(RegistrationStates.waiting_for_phone)
async def invalid_phone_input(message: Message):
    """Handle invalid input during phone registration"""
    await message.answer(
        "❌ Пожалуйста, используйте кнопки ниже для выбора действия или отправьте контакт.",
        reply_markup=get_phone_request_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, user: User):
    """Handle main menu callback"""
    await callback.message.edit_text(
        get_welcome_text(user),
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Show help information"""
    help_text = (
        "🆘 <b>Помощь по использованию бота</b>\n\n"
        "🏢 <b>Каталог ФОКов</b> - просмотр всех физкультурно-оздоровительных комплексов по районам\n\n"
        "📋 <b>Мои заявки</b> - просмотр поданных заявок и их статуса\n\n"
        "🔍 <b>Поиск по видам спорта</b> - поиск ФОКов по интересующим видам спорта\n\n"
        "📱 <b>Подача заявки</b> - для подачи заявки необходимо поделиться номером телефона\n\n"
        "📊 <b>Статусы заявок:</b>\n"
        "⏳ Ожидает обработки - заявка подана и ожидает рассмотрения\n"
        "✅ Принята - заявка одобрена\n"
        "📤 Передана в учреждение - заявка направлена в ФОК\n"
        "🎉 Выполнена - заявка обработана, можете посещать ФОК\n"
        "❌ Отменена - заявка отменена пользователем\n"
        "🚫 Отклонена - заявка отклонена администрацией\n\n"
        "❓ Если у вас есть вопросы, обратитесь к администратору."
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings")
async def settings_callback(callback: CallbackQuery, user: User):
    """Show user settings"""
    settings_text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"👤 <b>Имя:</b> {user.display_name}\n"
        f"📱 <b>Телефон:</b> {'✅ Указан' if user.phone_shared else '❌ Не указан'}\n"
        f"📊 <b>Всего заявок:</b> {user.total_applications}\n"
        f"📅 <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y')}\n\n"
        f"Для изменения настроек обратитесь к администратору."
    )
    
    from app.keyboards.inline import get_back_keyboard
    await callback.message.edit_text(
        settings_text,
        reply_markup=get_back_keyboard("main_menu", "🔙 Назад")
    )
    await callback.answer()


@router.message(Command("menu"))
async def menu_command(message: Message, user: User):
    """Handle /menu command"""
    await show_main_menu(message, user)


async def show_main_menu(message: Message, user: User):
    """Show main menu"""
    await message.answer(
        get_welcome_text(user),
        reply_markup=get_main_menu_keyboard()
    )


def get_welcome_text(user: User) -> str:
    """Get welcome text for user"""
    greeting_time = "день"
    import datetime
    current_hour = datetime.datetime.now().hour
    if 6 <= current_hour < 12:
        greeting_time = "утро"
    elif 12 <= current_hour < 18:
        greeting_time = "день"
    elif 18 <= current_hour < 23:
        greeting_time = "вечер"
    else:
        greeting_time = "ночь"
    
    return (
        f"🏢 <b>Каталог ФОКов</b>\n\n"
        f"Добро{' ' if greeting_time != 'ночь' else 'й'} {greeting_time}, {user.display_name}! 👋\n\n"
        f"Выберите интересующий раздел:"
    )
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bson import ObjectId
from loguru import logger

from app.models import User
from app.database.repositories import district_repo, fok_repo, application_repo, sport_repo
from app.keyboards.inline import (
    get_catalog_districts_keyboard,
    get_foks_keyboard, 
    get_fok_card_keyboard,
    get_sports_filter_keyboard,
    get_main_menu_keyboard
)
from app.config import settings


router = Router()


@router.callback_query(F.data == "catalog_main")
async def catalog_main(callback: CallbackQuery):
    """Show districts catalog"""
    try:
        districts = await district_repo.get_all_active()
        
        if not districts:
            await callback.message.edit_text(
                "❌ К сожалению, районы не найдены. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            "🏢 <b>Каталог ФОКов</b>\n\n"
            "Выберите район для просмотра доступных физкультурно-оздоровительных комплексов:",
            reply_markup=get_catalog_districts_keyboard(districts, 0, settings.MAX_ITEMS_PER_PAGE)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in catalog_main: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("districts_page_"))
async def districts_page(callback: CallbackQuery):
    """Handle districts pagination"""
    try:
        page = int(callback.data.split("_")[-1])
        districts = await district_repo.get_all_active()
        
        await callback.message.edit_reply_markup(
            reply_markup=get_catalog_districts_keyboard(districts, page, settings.MAX_ITEMS_PER_PAGE)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in districts_page: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("district_"))
async def district_foks(callback: CallbackQuery):
    """Show FOKs in selected district"""
    try:
        district_id = callback.data.split("_", 1)[1]
        
        # Handle back navigation
        if district_id.startswith("back_"):
            district_name = district_id.split("_", 1)[1]
            district = await district_repo.find_by_name(district_name)
            if not district:
                await callback.answer("❌ Район не найден.", show_alert=True)
                return
            district_id = str(district.id)
        
        # Get district
        district = await district_repo.find_by_id(ObjectId(district_id))
        if not district:
            await callback.answer("❌ Район не найден.", show_alert=True)
            return
        
        # Get FOKs in district
        foks = await fok_repo.get_by_district(district.name, 0, settings.MAX_ITEMS_PER_PAGE)
        foks_count = await fok_repo.count_by_district(district.name)
        
        if not foks:
            await callback.message.edit_text(
                f"❌ В районе <b>{district.name}</b> пока нет доступных ФОКов.\n\n"
                f"Попробуйте выбрать другой район.",
                reply_markup=get_catalog_districts_keyboard(
                    await district_repo.get_all_active(), 0, settings.MAX_ITEMS_PER_PAGE
                )
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            f"🏢 <b>ФОКи района: {district.name}</b>\n\n"
            f"Найдено ФОКов: {foks_count}\n"
            f"Выберите интересующий комплекс:",
            reply_markup=get_foks_keyboard(foks, district.name, 0, settings.MAX_ITEMS_PER_PAGE)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in district_foks: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("foks_page_"))
async def foks_page(callback: CallbackQuery):
    """Handle FOKs pagination"""
    try:
        parts = callback.data.split("_")
        district_name = parts[2]
        page = int(parts[3])
        
        foks = await fok_repo.get_by_district(district_name, page * settings.MAX_ITEMS_PER_PAGE, settings.MAX_ITEMS_PER_PAGE)
        
        await callback.message.edit_reply_markup(
            reply_markup=get_foks_keyboard(foks, district_name, page, settings.MAX_ITEMS_PER_PAGE)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in foks_page: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("fok_"))
async def fok_card(callback: CallbackQuery, user: User):
    """Show FOK card"""
    try:
        fok_id = callback.data.split("_", 1)[1]
        
        # Get FOK
        fok = await fok_repo.find_by_id(ObjectId(fok_id))
        if not fok:
            await callback.answer("❌ ФОК не найден.", show_alert=True)
            return
        
        # Check if user has already applied
        user_has_applied = await application_repo.has_user_applied_to_fok(user.id, fok.id)
        
        await callback.message.edit_text(
            fok.get_card_text(),
            reply_markup=get_fok_card_keyboard(fok, user_has_applied, user.can_make_applications)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in fok_card: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "need_phone")
async def need_phone(callback: CallbackQuery):
    """Inform user about phone requirement"""
    await callback.answer(
        "📱 Для подачи заявки необходимо поделиться номером телефона. "
        "Обратитесь к администратору для добавления номера.",
        show_alert=True
    )


@router.callback_query(F.data == "application_submitted")
async def application_submitted(callback: CallbackQuery):
    """Inform that application is already submitted"""
    await callback.answer(
        "✅ Вы уже подали заявку в этот ФОК. "
        "Проверить статус можно в разделе 'Мои заявки'.",
        show_alert=True
    )


@router.callback_query(F.data == "search_sports")
async def search_sports(callback: CallbackQuery, state: FSMContext):
    """Show sports filter"""
    try:
        sports = await sport_repo.get_all_active()
        
        if not sports:
            await callback.message.edit_text(
                "❌ Виды спорта не найдены. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        # Get selected sports from state
        state_data = await state.get_data()
        selected_sports = state_data.get("selected_sports", [])
        
        await callback.message.edit_text(
            "🔍 <b>Поиск по видам спорта</b>\n\n"
            "Выберите интересующие виды спорта.\n"
            "Можно выбрать несколько вариантов:",
            reply_markup=get_sports_filter_keyboard(sports, selected_sports)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in search_sports: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("toggle_sport_"))
async def toggle_sport(callback: CallbackQuery, state: FSMContext):
    """Toggle sport selection"""
    try:
        sport_name = callback.data.split("toggle_sport_", 1)[1]
        
        # Get current selection
        state_data = await state.get_data()
        selected_sports = state_data.get("selected_sports", [])
        
        # Toggle sport
        if sport_name in selected_sports:
            selected_sports.remove(sport_name)
        else:
            selected_sports.append(sport_name)
        
        # Update state
        await state.update_data(selected_sports=selected_sports)
        
        # Update keyboard
        sports = await sport_repo.get_all_active()
        await callback.message.edit_reply_markup(
            reply_markup=get_sports_filter_keyboard(sports, selected_sports)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in toggle_sport: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "clear_sports")
async def clear_sports(callback: CallbackQuery, state: FSMContext):
    """Clear sports selection"""
    try:
        await state.update_data(selected_sports=[])
        
        sports = await sport_repo.get_all_active()
        await callback.message.edit_reply_markup(
            reply_markup=get_sports_filter_keyboard(sports, [])
        )
        await callback.answer("🗑 Выбор очищен")
        
    except Exception as e:
        logger.error(f"Error in clear_sports: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "search_by_sports")
async def search_by_sports(callback: CallbackQuery, state: FSMContext):
    """Search FOKs by selected sports"""
    try:
        state_data = await state.get_data()
        selected_sports = state_data.get("selected_sports", [])
        
        if not selected_sports:
            await callback.answer("❌ Выберите хотя бы один вид спорта.", show_alert=True)
            return
        
        # Search FOKs
        foks = await fok_repo.search_by_sports(selected_sports, 0, settings.MAX_ITEMS_PER_PAGE)
        
        if not foks:
            await callback.message.edit_text(
                f"❌ ФОКи с выбранными видами спорта не найдены.\n\n"
                f"Выбранные виды спорта: {', '.join(selected_sports)}\n\n"
                f"Попробуйте изменить критерии поиска.",
                reply_markup=get_sports_filter_keyboard(await sport_repo.get_all_active(), selected_sports)
            )
            await callback.answer()
            return
        
        # Create results text
        results_text = (
            f"🔍 <b>Результаты поиска</b>\n\n"
            f"Найдено ФОКов: {len(foks)}\n"
            f"Виды спорта: {', '.join(selected_sports)}\n\n"
            f"Выберите ФОК:"
        )
        
        # Create keyboard with found FOKs
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        for fok in foks:
            builder.row(
                callback.types.InlineKeyboardButton(
                    text=f"🏢 {fok.name} ({fok.district})",
                    callback_data=f"fok_{fok.id}"
                )
            )
        
        builder.row(
            callback.types.InlineKeyboardButton(text="🔙 К поиску", callback_data="search_sports"),
            callback.types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        )
        
        await callback.message.edit_text(
            results_text,
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in search_by_sports: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bson import ObjectId
from loguru import logger
from datetime import datetime, timedelta

from app.models import User, Application
from app.models.application import ApplicationStatus
from app.database.repositories import (
    application_repo, user_repo, fok_repo, 
    district_repo, sport_repo
)
from app.keyboards.inline import get_admin_menu_keyboard, get_back_keyboard
from app.middlewares.admin_middleware import AdminMiddleware
from app.tasks.notifications import send_application_status_update, send_admin_notification
from app.tasks.reports import generate_statistics_report, generate_custom_report
from app.config import settings


router = Router()
router.message.middleware(AdminMiddleware(admin_only=True))
router.callback_query.middleware(AdminMiddleware(admin_only=True))


class AdminStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_application_notes = State()
    waiting_for_fok_data = State()


@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, user: User):
    """Show admin menu"""
    if not user.is_admin and not user.is_super_admin and user.telegram_id not in settings.super_admin_ids_list:
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"👑 <b>Панель администратора</b>\n\n"
        f"Добро пожаловать, {user.display_name}!\n"
        f"Выберите раздел для управления:",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_applications")
async def admin_applications(callback: CallbackQuery):
    """Show applications management"""
    try:
        # Get pending applications
        pending_apps = await application_repo.get_by_status(ApplicationStatus.PENDING, 0, 10)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if pending_apps:
            builder.row(callback.types.InlineKeyboardButton(
                text=f"⏳ Ожидающие обработки ({len(pending_apps)})",
                callback_data="admin_apps_pending"
            ))
        
        builder.row(
            callback.types.InlineKeyboardButton(text="🔍 Поиск заявок", callback_data="admin_search_apps"),
            callback.types.InlineKeyboardButton(text="📊 Все заявки", callback_data="admin_all_apps")
        )
        
        builder.row(
            callback.types.InlineKeyboardButton(text="✅ Принятые", callback_data="admin_apps_accepted"),
            callback.types.InlineKeyboardButton(text="📤 Переданные", callback_data="admin_apps_transferred")
        )
        
        builder.row(
            callback.types.InlineKeyboardButton(text="🎉 Выполненные", callback_data="admin_apps_completed"),
            callback.types.InlineKeyboardButton(text="❌ Отмененные", callback_data="admin_apps_cancelled")
        )
        
        builder.row(callback.types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"))
        
        await callback.message.edit_text(
            "📋 <b>Управление заявками</b>\n\n"
            "Выберите категорию заявок для просмотра:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in admin_applications: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("admin_apps_"))
async def admin_apps_by_status(callback: CallbackQuery):
    """Show applications by status"""
    try:
        status_map = {
            "pending": ApplicationStatus.PENDING,
            "accepted": ApplicationStatus.ACCEPTED,
            "transferred": ApplicationStatus.TRANSFERRED,
            "completed": ApplicationStatus.COMPLETED,
            "cancelled": ApplicationStatus.CANCELLED
        }
        
        status_key = callback.data.split("_")[-1]
        status = status_map.get(status_key)
        
        if not status:
            await callback.answer("❌ Неверный статус.", show_alert=True)
            return
        
        applications = await application_repo.get_by_status(status, 0, settings.MAX_ITEMS_PER_PAGE)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if not applications:
            builder.row(callback.types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_applications"))
            
            await callback.message.edit_text(
                f"📋 <b>Заявки со статусом: {status.value}</b>\n\n"
                "Заявок не найдено.",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
            return
        
        for app in applications:
            builder.row(callback.types.InlineKeyboardButton(
                text=f"#{str(app.id)[-6:]} {app.fok_name} - {app.user_name}",
                callback_data=f"admin_app_{app.id}"
            ))
        
        builder.row(callback.types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_applications"))
        
        await callback.message.edit_text(
            f"📋 <b>Заявки со статусом: {status.value}</b>\n\n"
            f"Найдено заявок: {len(applications)}\n"
            "Выберите заявку для просмотра:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in admin_apps_by_status: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("admin_app_"))
async def admin_application_card(callback: CallbackQuery):
    """Show application card for admin"""
    try:
        app_id = callback.data.split("_", 2)[2]
        application = await application_repo.find_by_id(ObjectId(app_id))
        
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Status change buttons
        if application.status == ApplicationStatus.PENDING:
            builder.row(
                callback.types.InlineKeyboardButton(text="✅ Принять", callback_data=f"admin_accept_{app_id}"),
                callback.types.InlineKeyboardButton(text="🚫 Отклонить", callback_data=f"admin_reject_{app_id}")
            )
        elif application.status == ApplicationStatus.ACCEPTED:
            builder.row(
                callback.types.InlineKeyboardButton(text="📤 Передать", callback_data=f"admin_transfer_{app_id}"),
                callback.types.InlineKeyboardButton(text="🚫 Отклонить", callback_data=f"admin_reject_{app_id}")
            )
        elif application.status == ApplicationStatus.TRANSFERRED:
            builder.row(
                callback.types.InlineKeyboardButton(text="🎉 Выполнено", callback_data=f"admin_complete_{app_id}")
            )
        
        # Additional actions
        builder.row(
            callback.types.InlineKeyboardButton(text="📝 Добавить примечание", callback_data=f"admin_note_{app_id}"),
            callback.types.InlineKeyboardButton(text="👤 Профиль пользователя", callback_data=f"admin_user_{application.user_id}")
        )
        
        builder.row(callback.types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_applications"))
        
        await callback.message.edit_text(
            application.get_card_text(),
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in admin_application_card: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("admin_accept_"))
async def admin_accept_application(callback: CallbackQuery, user: User):
    """Accept application"""
    try:
        app_id = callback.data.split("_", 2)[2]
        application = await application_repo.find_by_id(ObjectId(app_id))
        
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        old_status = application.status
        application.update_status(ApplicationStatus.ACCEPTED, user.id)
        await application_repo.update(application)
        
        # Send notification to user
        await send_application_status_update.delay(
            str(application.id), old_status.value, ApplicationStatus.ACCEPTED.value
        )
        
        await callback.answer("✅ Заявка принята!", show_alert=True)
        
        # Update display
        await admin_application_card(callback)
        
    except Exception as e:
        logger.error(f"Error in admin_accept_application: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("admin_transfer_"))
async def admin_transfer_application(callback: CallbackQuery, user: User):
    """Transfer application"""
    try:
        app_id = callback.data.split("_", 2)[2]
        application = await application_repo.find_by_id(ObjectId(app_id))
        
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        old_status = application.status
        application.update_status(ApplicationStatus.TRANSFERRED, user.id)
        await application_repo.update(application)
        
        # Send notification to user
        await send_application_status_update.delay(
            str(application.id), old_status.value, ApplicationStatus.TRANSFERRED.value
        )
        
        await callback.answer("📤 Заявка передана в учреждение!", show_alert=True)
        
        # Update display
        await admin_application_card(callback)
        
    except Exception as e:
        logger.error(f"Error in admin_transfer_application: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("admin_complete_"))
async def admin_complete_application(callback: CallbackQuery, user: User):
    """Complete application"""
    try:
        app_id = callback.data.split("_", 2)[2]
        application = await application_repo.find_by_id(ObjectId(app_id))
        
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        old_status = application.status
        application.update_status(ApplicationStatus.COMPLETED, user.id)
        await application_repo.update(application)
        
        # Send notification to user
        await send_application_status_update.delay(
            str(application.id), old_status.value, ApplicationStatus.COMPLETED.value
        )
        
        await callback.answer("🎉 Заявка выполнена!", show_alert=True)
        
        # Update display
        await admin_application_card(callback)
        
    except Exception as e:
        logger.error(f"Error in admin_complete_application: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_application(callback: CallbackQuery, user: User):
    """Reject application"""
    try:
        app_id = callback.data.split("_", 2)[2]
        application = await application_repo.find_by_id(ObjectId(app_id))
        
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        old_status = application.status
        application.update_status(ApplicationStatus.REJECTED, user.id)
        await application_repo.update(application)
        
        # Send notification to user
        await send_application_status_update.delay(
            str(application.id), old_status.value, ApplicationStatus.REJECTED.value
        )
        
        await callback.answer("🚫 Заявка отклонена!", show_alert=True)
        
        # Update display
        await admin_application_card(callback)
        
    except Exception as e:
        logger.error(f"Error in admin_reject_application: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "admin_stats")
async def admin_statistics(callback: CallbackQuery):
    """Show statistics"""
    try:
        # Generate statistics for last 30 days
        stats = await generate_statistics_report.delay(30)
        stats_data = stats.get()
        
        # Format statistics message
        message = (
            f"📊 <b>Статистика за последние 30 дней</b>\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"• Всего: {stats_data['users']['total']}\n"
            f"• Активных: {stats_data['users']['active_in_period']}\n\n"
            f"📋 <b>Заявки:</b>\n"
            f"• Всего: {stats_data['applications']['total']}\n"
            f"• За период: {stats_data['applications']['period_total']}\n\n"
            f"📊 <b>По статусам:</b>\n"
        )
        
        for status, count in stats_data['applications']['by_status'].items():
            message += f"• {status}: {count}\n"
        
        message += f"\n🏢 <b>ФОКи:</b>\n"
        message += f"• Всего активных: {stats_data['foks']['total']}\n\n"
        
        if stats_data['foks']['popular']:
            message += f"🔥 <b>Популярные ФОКи:</b>\n"
            for fok in stats_data['foks']['popular'][:3]:
                message += f"• {fok['name']} ({fok['district']}) - {fok['applications']} заявок\n"
        
        await callback.message.edit_text(
            message,
            reply_markup=get_back_keyboard("admin_menu", "🔙 Назад")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in admin_statistics: {e}")
        await callback.answer("❌ Произошла ошибка при получении статистики.", show_alert=True)


@router.callback_query(F.data == "admin_foks")
async def admin_foks_management(callback: CallbackQuery):
    """FOKs management menu"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    builder.row(
        callback.types.InlineKeyboardButton(text="➕ Добавить ФОК", callback_data="admin_add_fok"),
        callback.types.InlineKeyboardButton(text="📝 Редактировать ФОК", callback_data="admin_edit_fok")
    )
    builder.row(
        callback.types.InlineKeyboardButton(text="🗑 Удалить ФОК", callback_data="admin_delete_fok"),
        callback.types.InlineKeyboardButton(text="📋 Список ФОКов", callback_data="admin_list_foks")
    )
    builder.row(callback.types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"))
    
    await callback.message.edit_text(
        "🏢 <b>Управление ФОКами</b>\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_management(callback: CallbackQuery):
    """Users management menu"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    builder.row(
        callback.types.InlineKeyboardButton(text="👑 Назначить админа", callback_data="admin_promote_user"),
        callback.types.InlineKeyboardButton(text="🚫 Заблокировать", callback_data="admin_block_user")
    )
    builder.row(
        callback.types.InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_search_user"),
        callback.types.InlineKeyboardButton(text="📊 Статистика", callback_data="admin_user_stats")
    )
    builder.row(callback.types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"))
    
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_reports")
async def admin_reports(callback: CallbackQuery):
    """Reports menu"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    builder.row(
        callback.types.InlineKeyboardButton(text="📊 Сгенерировать отчет", callback_data="admin_generate_report"),
        callback.types.InlineKeyboardButton(text="📅 Еженедельный отчет", callback_data="admin_weekly_report")
    )
    builder.row(
        callback.types.InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats"),
        callback.types.InlineKeyboardButton(text="📋 Экспорт данных", callback_data="admin_export_data")
    )
    builder.row(callback.types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"))
    
    await callback.message.edit_text(
        "📈 <b>Отчеты и статистика</b>\n\n"
        "Выберите тип отчета:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
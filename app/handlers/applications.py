from aiogram import Router, F
from aiogram.types import CallbackQuery
from bson import ObjectId
from loguru import logger

from app.models import User, Application
from app.models.application import ApplicationStatus
from app.database.repositories import application_repo, fok_repo, user_repo
from app.keyboards.inline import (
    get_applications_keyboard,
    get_application_card_keyboard,
    get_cancel_confirmation_keyboard,
    get_main_menu_keyboard
)
from app.config import settings
from app.tasks.notifications import send_admin_notification


router = Router()


@router.callback_query(F.data.startswith("apply_"))
async def apply_to_fok(callback: CallbackQuery, user: User):
    """Apply to FOK"""
    try:
        fok_id = callback.data.split("_", 1)[1]
        
        # Check if user can apply
        if not user.can_make_applications:
            await callback.answer(
                "❌ Для подачи заявки необходимо поделиться номером телефона.",
                show_alert=True
            )
            return
        
        # Get FOK
        fok = await fok_repo.find_by_id(ObjectId(fok_id))
        if not fok:
            await callback.answer("❌ ФОК не найден.", show_alert=True)
            return
        
        # Check if user already applied
        if await application_repo.has_user_applied_to_fok(user.id, fok.id):
            await callback.answer(
                "✅ Вы уже подали заявку в этот ФОК.",
                show_alert=True
            )
            return
        
        # Create application
        application = Application(
            user_id=user.id,
            fok_id=fok.id,
            user_name=user.display_name,
            user_phone=user.phone,
            user_telegram_id=user.telegram_id,
            fok_name=fok.name,
            fok_district=fok.district,
            fok_address=fok.address,
            status=ApplicationStatus.PENDING
        )
        
        application = await application_repo.create(application)
        
        # Update counters
        await fok_repo.increment_applications_count(fok.id)
        user.total_applications += 1
        await user_repo.update(user)
        
        # Record metrics
        from app.utils.metrics import record_application_created
        record_application_created()
        
        # Send notification to admins
        try:
            await send_admin_notification.delay(
                f"🆕 Новая заявка #{str(application.id)[-6:]}\n\n"
                f"👤 {user.display_name} ({user.phone})\n"
                f"🏢 {fok.name}\n"
                f"📍 {fok.district}"
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
        
        # Update keyboard to show application submitted
        from app.keyboards.inline import get_fok_card_keyboard
        await callback.message.edit_reply_markup(
            reply_markup=get_fok_card_keyboard(fok, True, user.can_make_applications)
        )
        
        await callback.answer(
            "✅ Заявка успешно подана! Вы получите уведомление о её обработке.",
            show_alert=True
        )
        
    except Exception as e:
        logger.error(f"Error in apply_to_fok: {e}")
        await callback.answer("❌ Произошла ошибка при подаче заявки. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "my_applications")
async def my_applications(callback: CallbackQuery, user: User):
    """Show user applications"""
    try:
        applications = await application_repo.get_user_applications(user.id, 0, settings.MAX_ITEMS_PER_PAGE)
        applications_count = await application_repo.count_user_applications(user.id)
        
        if not applications:
            text = (
                "📋 <b>Мои заявки</b>\n\n"
                "У вас пока нет поданных заявок.\n\n"
                "Чтобы подать заявку, выберите ФОК в каталоге и нажмите кнопку \"Оставить заявку\"."
            )
        else:
            text = (
                f"📋 <b>Мои заявки</b>\n\n"
                f"Всего заявок: {applications_count}\n"
                f"Выберите заявку для просмотра подробностей:"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_applications_keyboard(applications, 0, settings.MAX_ITEMS_PER_PAGE)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in my_applications: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("apps_page_"))
async def applications_page(callback: CallbackQuery, user: User):
    """Handle applications pagination"""
    try:
        page = int(callback.data.split("_")[-1])
        applications = await application_repo.get_user_applications(
            user.id, 
            page * settings.MAX_ITEMS_PER_PAGE, 
            settings.MAX_ITEMS_PER_PAGE
        )
        
        await callback.message.edit_reply_markup(
            reply_markup=get_applications_keyboard(applications, page, settings.MAX_ITEMS_PER_PAGE)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in applications_page: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("application_"))
async def application_card(callback: CallbackQuery, user: User):
    """Show application card"""
    try:
        application_id = callback.data.split("_", 1)[1]
        
        # Get application
        application = await application_repo.find_by_id(ObjectId(application_id))
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        # Check if application belongs to user
        if application.user_id != user.id and not user.is_admin:
            await callback.answer("❌ У вас нет доступа к этой заявке.", show_alert=True)
            return
        
        await callback.message.edit_text(
            application.get_card_text(),
            reply_markup=get_application_card_keyboard(application)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in application_card: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("cancel_app_"))
async def cancel_application_confirm(callback: CallbackQuery, user: User):
    """Confirm application cancellation"""
    try:
        application_id = callback.data.split("_", 2)[2]
        
        # Get application
        application = await application_repo.find_by_id(ObjectId(application_id))
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        # Check if application belongs to user
        if application.user_id != user.id:
            await callback.answer("❌ У вас нет доступа к этой заявке.", show_alert=True)
            return
        
        # Check if can be cancelled
        if not application.can_be_cancelled:
            await callback.answer(
                f"❌ Заявку со статусом '{application.status_display}' нельзя отменить.",
                show_alert=True
            )
            return
        
        await callback.message.edit_text(
            f"❓ <b>Подтверждение отмены</b>\n\n"
            f"Вы действительно хотите отменить заявку?\n\n"
            f"🏢 <b>ФОК:</b> {application.fok_name}\n"
            f"📍 <b>Район:</b> {application.fok_district}\n"
            f"📊 <b>Текущий статус:</b> {application.status_display}\n\n"
            f"⚠️ Это действие нельзя будет отменить.",
            reply_markup=get_cancel_confirmation_keyboard(application_id)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in cancel_application_confirm: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancel_application(callback: CallbackQuery, user: User):
    """Confirm and cancel application"""
    try:
        application_id = callback.data.split("_", 2)[2]
        
        # Get application
        application = await application_repo.find_by_id(ObjectId(application_id))
        if not application:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return
        
        # Check if application belongs to user
        if application.user_id != user.id:
            await callback.answer("❌ У вас нет доступа к этой заявке.", show_alert=True)
            return
        
        # Check if can be cancelled
        if not application.can_be_cancelled:
            await callback.answer(
                f"❌ Заявку со статусом '{application.status_display}' нельзя отменить.",
                show_alert=True
            )
            return
        
        # Cancel application
        application.update_status(ApplicationStatus.CANCELLED)
        await application_repo.update(application)
        
        # Send notification to admins
        try:
            await send_admin_notification.delay(
                f"❌ Заявка отменена пользователем #{str(application.id)[-6:]}\n\n"
                f"👤 {application.user_name}\n"
                f"🏢 {application.fok_name}\n"
                f"📍 {application.fok_district}"
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
        
        await callback.message.edit_text(
            application.get_card_text(),
            reply_markup=get_application_card_keyboard(application)
        )
        
        await callback.answer(
            "✅ Заявка успешно отменена.",
            show_alert=True
        )
        
    except Exception as e:
        logger.error(f"Error in confirm_cancel_application: {e}")
        await callback.answer("❌ Произошла ошибка при отмене заявки. Попробуйте позже.", show_alert=True)
import asyncio
from typing import List, Optional
from celery import current_task
from loguru import logger

from .celery_app import celery_app
from app.config import settings


@celery_app.task(bind=True, max_retries=3)
def send_admin_notification(self, message: str, parse_mode: str = "HTML"):
    """Send notification to admin chat"""
    try:
        asyncio.run(_send_admin_notification(message, parse_mode))
    except Exception as exc:
        logger.error(f"Admin notification failed: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


@celery_app.task(bind=True, max_retries=3)
def send_user_notification(self, user_id: int, message: str, parse_mode: str = "HTML"):
    """Send notification to specific user"""
    try:
        asyncio.run(_send_user_notification(user_id, message, parse_mode))
    except Exception as exc:
        logger.error(f"User notification failed for {user_id}: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


@celery_app.task(bind=True, max_retries=3)
def send_bulk_notifications(self, user_ids: List[int], message: str, parse_mode: str = "HTML"):
    """Send notifications to multiple users"""
    try:
        asyncio.run(_send_bulk_notifications(user_ids, message, parse_mode))
    except Exception as exc:
        logger.error(f"Bulk notifications failed: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


async def _send_admin_notification(message: str, parse_mode: str = "HTML"):
    """Internal function to send admin notification"""
    from aiogram import Bot
    from app.database.repositories import user_repo
    
    if not settings.BOT_TOKEN:
        logger.warning("Bot token not configured, skipping admin notification")
        return
    
    bot = Bot(token=settings.BOT_TOKEN)
    
    try:
        # Send to admin chat if configured
        if settings.ADMIN_CHAT_ID:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=message,
                parse_mode=parse_mode
            )
        
        # Send to all admins
        admins = await user_repo.get_admins()
        for admin in admins:
            try:
                await bot.send_message(
                    chat_id=admin.telegram_id,
                    text=message,
                    parse_mode=parse_mode
                )
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin.telegram_id}: {e}")
        
        # Send to super admins from config
        for admin_id in settings.super_admin_ids_list:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=parse_mode
                )
            except Exception as e:
                logger.error(f"Failed to send notification to super admin {admin_id}: {e}")
        
    finally:
        await bot.session.close()


async def _send_user_notification(user_id: int, message: str, parse_mode: str = "HTML"):
    """Internal function to send user notification"""
    from aiogram import Bot
    
    if not settings.BOT_TOKEN:
        logger.warning("Bot token not configured, skipping user notification")
        return
    
    bot = Bot(token=settings.BOT_TOKEN)
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode=parse_mode
        )
    finally:
        await bot.session.close()


async def _send_bulk_notifications(user_ids: List[int], message: str, parse_mode: str = "HTML"):
    """Internal function to send bulk notifications"""
    from aiogram import Bot
    import asyncio
    
    if not settings.BOT_TOKEN:
        logger.warning("Bot token not configured, skipping bulk notifications")
        return
    
    bot = Bot(token=settings.BOT_TOKEN)
    
    try:
        # Send notifications with rate limiting
        for i, user_id in enumerate(user_ids):
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=parse_mode
                )
                
                # Rate limiting: 30 messages per second max
                if (i + 1) % 30 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")
    finally:
        await bot.session.close()


@celery_app.task
def send_application_status_update(application_id: str, old_status: str, new_status: str):
    """Send notification about application status update"""
    try:
        asyncio.run(_send_application_status_update(application_id, old_status, new_status))
    except Exception as exc:
        logger.error(f"Application status notification failed: {exc}")
        raise


async def _send_application_status_update(application_id: str, old_status: str, new_status: str):
    """Internal function to send application status update"""
    from bson import ObjectId
    from app.database.repositories import application_repo
    from app.models.application import ApplicationStatus
    
    try:
        # Get application
        application = await application_repo.find_by_id(ObjectId(application_id))
        if not application:
            logger.error(f"Application {application_id} not found for status notification")
            return
        
        # Prepare notification message
        status_messages = {
            ApplicationStatus.ACCEPTED: "✅ Ваша заявка принята к рассмотрению!",
            ApplicationStatus.TRANSFERRED: "📤 Ваша заявка передана в учреждение для обработки.",
            ApplicationStatus.COMPLETED: "🎉 Ваша заявка выполнена! Вы можете посещать ФОК.",
            ApplicationStatus.REJECTED: "🚫 К сожалению, ваша заявка была отклонена.",
        }
        
        status_message = status_messages.get(application.status, f"📊 Статус заявки изменен на: {application.status_display}")
        
        message = (
            f"📋 <b>Обновление заявки #{str(application.id)[-6:]}</b>\n\n"
            f"{status_message}\n\n"
            f"🏢 <b>ФОК:</b> {application.fok_name}\n"
            f"📍 <b>Район:</b> {application.fok_district}\n"
            f"📅 <b>Дата подачи:</b> {application.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Вы можете просмотреть подробности в разделе \"Мои заявки\"."
        )
        
        # Send notification to user
        await _send_user_notification(application.user_telegram_id, message)
        
    except Exception as e:
        logger.error(f"Error in application status notification: {e}")
        raise
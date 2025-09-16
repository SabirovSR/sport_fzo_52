from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime
from loguru import logger

from app.database.connection import check_database_health, get_database_stats
from app.config import settings


router = Router()


@router.message(Command("health"))
async def health_check(message: Message):
    """Health check command for admins"""
    user_id = message.from_user.id
    
    # Only allow super admins
    if user_id not in settings.super_admin_ids_list:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    try:
        # Check database
        db_healthy = await check_database_health()
        
        # Get basic stats
        stats = await get_database_stats()
        
        # Format response
        status_text = (
            f"🏥 <b>Состояние системы</b>\n\n"
            f"📅 Время проверки: {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')} UTC\n\n"
            f"💾 <b>База данных:</b> {'✅ Работает' if db_healthy else '❌ Недоступна'}\n\n"
        )
        
        if stats:
            status_text += f"📊 <b>Статистика:</b>\n"
            for collection, count in stats.get('collections', {}).items():
                status_text += f"• {collection}: {count}\n"
            
            if stats.get('database_size'):
                size_mb = stats['database_size'] / (1024 * 1024)
                status_text += f"\n💽 Размер БД: {size_mb:.1f} MB"
        
        await message.answer(status_text)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        await message.answer(
            f"❌ Ошибка при проверке состояния системы:\n"
            f"<code>{str(e)}</code>"
        )
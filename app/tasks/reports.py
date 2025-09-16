import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
from io import BytesIO
from loguru import logger

from .celery_app import celery_app
from .notifications import send_admin_notification


@celery_app.task
def generate_weekly_report():
    """Generate and send weekly report"""
    try:
        asyncio.run(_generate_weekly_report())
    except Exception as exc:
        logger.error(f"Weekly report generation failed: {exc}")
        raise


@celery_app.task
def generate_statistics_report(days: int = 30):
    """Generate statistics report"""
    try:
        return asyncio.run(_generate_statistics_report(days))
    except Exception as exc:
        logger.error(f"Statistics report generation failed: {exc}")
        raise


async def _generate_weekly_report():
    """Internal function to generate weekly report"""
    from app.database.repositories import application_repo, user_repo, fok_repo
    from aiogram import Bot
    from app.config import settings
    
    try:
        # Calculate date range (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Get applications from last week
        applications = await application_repo.get_recent_applications(days=7, limit=1000)
        
        if not applications:
            await send_admin_notification.delay(
                "📊 <b>Еженедельный отчет</b>\n\n"
                "За прошедшую неделю новых заявок не было."
            )
            return
        
        # Create Excel report
        excel_data = []
        for app in applications:
            excel_data.append({
                'ID заявки': str(app.id)[-6:],
                'Дата подачи': app.created_at.strftime('%d.%m.%Y %H:%M'),
                'Имя заявителя': app.user_name,
                'Телефон': app.user_phone,
                'ФОК': app.fok_name,
                'Район': app.fok_district,
                'Адрес': app.fok_address,
                'Статус': app.status_display,
                'Дата обновления': app.status_updated_at.strftime('%d.%m.%Y %H:%M') if app.status_updated_at else '',
                'Примечания': app.admin_notes or ''
            })
        
        # Create DataFrame and Excel file
        df = pd.DataFrame(excel_data)
        excel_buffer = BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Заявки', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Заявки']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_buffer.seek(0)
        
        # Generate statistics
        stats = await application_repo.get_statistics(days=7)
        total_apps = len(applications)
        
        # Create summary message
        summary = (
            f"📊 <b>Еженедельный отчет</b>\n"
            f"📅 {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n\n"
            f"📋 <b>Всего заявок:</b> {total_apps}\n\n"
            f"📊 <b>По статусам:</b>\n"
        )
        
        for status, count in stats.items():
            summary += f"• {status}: {count}\n"
        
        # Send summary to admins
        await send_admin_notification.delay(summary)
        
        # Send Excel file to admin chat
        if settings.ADMIN_CHAT_ID and settings.BOT_TOKEN:
            bot = Bot(token=settings.BOT_TOKEN)
            try:
                filename = f"weekly_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
                
                await bot.send_document(
                    chat_id=settings.ADMIN_CHAT_ID,
                    document=BytesIO(excel_buffer.getvalue()),
                    filename=filename,
                    caption="📊 Еженедельный отчет по заявкам"
                )
            finally:
                await bot.session.close()
        
        logger.info(f"Weekly report generated successfully: {total_apps} applications")
        
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        await send_admin_notification.delay(
            f"❌ Ошибка при генерации еженедельного отчета: {str(e)}"
        )
        raise


async def _generate_statistics_report(days: int = 30) -> Dict[str, Any]:
    """Internal function to generate statistics report"""
    from app.database.repositories import application_repo, user_repo, fok_repo
    
    try:
        # Get statistics
        app_stats = await application_repo.get_statistics(days)
        total_users = await user_repo.count()
        active_users = await user_repo.get_active_users_count(days)
        total_foks = await fok_repo.count({"is_active": True})
        total_applications = await application_repo.count({"is_active": True})
        
        # Get popular FOKs
        popular_foks = await fok_repo.get_popular(limit=5)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "applications": {
                "total": total_applications,
                "by_status": app_stats,
                "period_total": sum(app_stats.values())
            },
            "users": {
                "total": total_users,
                "active_in_period": active_users
            },
            "foks": {
                "total": total_foks,
                "popular": [
                    {
                        "name": fok.name,
                        "district": fok.district,
                        "applications": fok.total_applications
                    }
                    for fok in popular_foks
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating statistics: {e}")
        raise


@celery_app.task
def generate_custom_report(filters: Dict[str, Any]):
    """Generate custom report with filters"""
    try:
        return asyncio.run(_generate_custom_report(filters))
    except Exception as exc:
        logger.error(f"Custom report generation failed: {exc}")
        raise


async def _generate_custom_report(filters: Dict[str, Any]) -> BytesIO:
    """Generate custom Excel report with filters"""
    from app.database.repositories import application_repo
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from app.database.connection import get_database
    
    try:
        db = await get_database()
        collection = db.applications
        
        # Build query from filters
        query = {"is_active": True}
        
        if filters.get("status"):
            query["status"] = filters["status"]
        
        if filters.get("district"):
            query["fok_district"] = filters["district"]
        
        if filters.get("start_date") and filters.get("end_date"):
            start_date = datetime.fromisoformat(filters["start_date"])
            end_date = datetime.fromisoformat(filters["end_date"])
            query["created_at"] = {"$gte": start_date, "$lte": end_date}
        
        # Get applications
        cursor = collection.find(query).sort("created_at", -1)
        applications = []
        
        async for doc in cursor:
            app = Application(**doc)
            applications.append({
                'ID заявки': str(app.id)[-6:],
                'Дата подачи': app.created_at.strftime('%d.%m.%Y %H:%M'),
                'Имя заявителя': app.user_name,
                'Телефон': app.user_phone,
                'ФОК': app.fok_name,
                'Район': app.fok_district,
                'Адрес': app.fok_address,
                'Статус': app.status_display,
                'Дата обновления': app.status_updated_at.strftime('%d.%m.%Y %H:%M') if app.status_updated_at else '',
                'Примечания': app.admin_notes or ''
            })
        
        # Create Excel file
        df = pd.DataFrame(applications)
        excel_buffer = BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Заявки', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Заявки']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_buffer.seek(0)
        return excel_buffer
        
    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        raise
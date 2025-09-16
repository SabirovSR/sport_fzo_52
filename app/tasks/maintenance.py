import asyncio
from datetime import datetime, timedelta
from loguru import logger

from .celery_app import celery_app


@celery_app.task
def cleanup_old_data():
    """Clean up old data periodically"""
    try:
        asyncio.run(_cleanup_old_data())
    except Exception as exc:
        logger.error(f"Data cleanup failed: {exc}")
        raise


async def _cleanup_old_data():
    """Internal function to cleanup old data"""
    from app.database.connection import get_database
    
    try:
        db = await get_database()
        
        # Clean up old logs (older than 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Clean up cancelled/rejected applications older than 30 days
        app_cutoff = datetime.utcnow() - timedelta(days=30)
        
        result = await db.applications.delete_many({
            "status": {"$in": ["cancelled", "rejected"]},
            "updated_at": {"$lt": app_cutoff}
        })
        
        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} old applications")
        
        # Update user activity statistics
        await db.users.update_many(
            {"last_activity": {"$lt": cutoff_date}},
            {"$set": {"is_active": False}}
        )
        
        logger.info("Data cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise


@celery_app.task
def backup_database():
    """Create database backup"""
    try:
        asyncio.run(_backup_database())
    except Exception as exc:
        logger.error(f"Database backup failed: {exc}")
        raise


async def _backup_database():
    """Internal function to backup database"""
    import subprocess
    import os
    from app.config import settings
    
    try:
        # Create backup directory
        backup_dir = "/app/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"fok_bot_backup_{timestamp}.gz"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create MongoDB dump
        cmd = [
            "mongodump",
            "--host", f"{settings.MONGO_HOST}:{settings.MONGO_PORT}",
            "--db", settings.MONGO_DB_NAME,
            "--archive", backup_path,
            "--gzip"
        ]
        
        if settings.MONGO_USERNAME:
            cmd.extend(["--username", settings.MONGO_USERNAME])
        if settings.MONGO_PASSWORD:
            cmd.extend(["--password", settings.MONGO_PASSWORD])
        
        # Execute backup
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Database backup created: {backup_filename}")
            
            # Clean up old backups (keep last 7)
            backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("fok_bot_backup_")])
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    os.remove(os.path.join(backup_dir, old_backup))
                    logger.info(f"Removed old backup: {old_backup}")
        else:
            logger.error(f"Database backup failed: {result.stderr}")
            raise Exception(f"Backup failed: {result.stderr}")
        
    except Exception as e:
        logger.error(f"Error during database backup: {e}")
        raise


@celery_app.task
def update_statistics():
    """Update cached statistics"""
    try:
        asyncio.run(_update_statistics())
    except Exception as exc:
        logger.error(f"Statistics update failed: {exc}")
        raise


async def _update_statistics():
    """Internal function to update statistics"""
    from app.database.repositories import application_repo, user_repo, fok_repo
    import redis.asyncio as redis
    from app.config import settings
    import json
    
    try:
        # Connect to Redis
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        
        # Calculate statistics
        stats = {
            "total_users": await user_repo.count(),
            "active_users_30d": await user_repo.get_active_users_count(30),
            "active_users_7d": await user_repo.get_active_users_count(7),
            "total_applications": await application_repo.count(),
            "total_foks": await fok_repo.count({"is_active": True}),
            "applications_stats_30d": await application_repo.get_statistics(30),
            "applications_stats_7d": await application_repo.get_statistics(7),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Cache statistics in Redis
        await redis_client.setex("bot_statistics", 3600, json.dumps(stats))  # Cache for 1 hour
        
        logger.info("Statistics updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating statistics: {e}")
        raise


@celery_app.task
def health_check():
    """Perform system health check"""
    try:
        return asyncio.run(_health_check())
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise


async def _health_check():
    """Internal function for health check"""
    from app.database.connection import check_database_health
    import redis.asyncio as redis
    from app.config import settings
    
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": False,
        "redis": False,
        "overall": False
    }
    
    try:
        # Check database
        health_status["database"] = await check_database_health()
        
        # Check Redis
        try:
            redis_client = redis.from_url(settings.redis_url)
            await redis_client.ping()
            health_status["redis"] = True
        except Exception:
            health_status["redis"] = False
        
        # Overall health
        health_status["overall"] = health_status["database"] and health_status["redis"]
        
        if not health_status["overall"]:
            logger.warning(f"Health check failed: {health_status}")
        else:
            logger.info("Health check passed")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        health_status["error"] = str(e)
        return health_status
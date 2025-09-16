import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from loguru import logger
from app.config import settings


class DatabaseConnection:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


db_connection = DatabaseConnection()


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if db_connection.database is None:
        await init_database()
    return db_connection.database


async def init_database():
    """Initialize database connection"""
    try:
        # Build connection options for replica set
        connection_options = {
            'maxPoolSize': 50,
            'minPoolSize': 10,
            'maxIdleTimeMS': 30000,
            'waitQueueTimeoutMS': 5000,
            'serverSelectionTimeoutMS': 5000,
            'retryWrites': True,
            'retryReads': True,
            'readPreference': 'secondaryPreferred'
        }
        
        # Add replica set name if using cluster mode
        if ',' in settings.MONGO_HOST:
            connection_options['replicaSet'] = 'fok-replica-set'
        
        # Create MongoDB client
        db_connection.client = AsyncIOMotorClient(
            settings.mongo_url,
            **connection_options
        )
        
        # Get database
        db_connection.database = db_connection.client[settings.MONGO_DB_NAME]
        
        # Test connection
        await db_connection.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB: {settings.MONGO_DB_NAME}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_database():
    """Close database connection"""
    if db_connection.client:
        db_connection.client.close()
        logger.info("Database connection closed")


async def create_indexes():
    """Create database indexes for performance"""
    try:
        db = db_connection.database
        
        # Users indexes
        await db.users.create_index("telegram_id", unique=True)
        await db.users.create_index("phone")
        await db.users.create_index("is_admin")
        await db.users.create_index("last_activity")
        
        # FOKs indexes
        await db.foks.create_index("name")
        await db.foks.create_index("district")
        await db.foks.create_index("sports")
        await db.foks.create_index([("is_active", 1), ("featured", -1), ("sort_order", 1)])
        
        # Applications indexes
        await db.applications.create_index("user_id")
        await db.applications.create_index("fok_id")
        await db.applications.create_index("status")
        await db.applications.create_index([("created_at", -1)])
        await db.applications.create_index([("user_id", 1), ("created_at", -1)])
        
        # Districts indexes
        await db.districts.create_index("name", unique=True)
        await db.districts.create_index([("is_active", 1), ("sort_order", 1)])
        
        # Sports indexes
        await db.sports.create_index("name", unique=True)
        await db.sports.create_index([("is_active", 1), ("sort_order", 1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")


# Utility functions for health checks
async def check_database_health() -> bool:
    """Check if database is healthy"""
    try:
        if not db_connection.client:
            return False
        await db_connection.client.admin.command('ping')
        return True
    except Exception:
        return False


async def get_database_stats() -> dict:
    """Get database statistics"""
    try:
        db = await get_database()
        stats = await db.command("dbStats")
        
        # Get collection counts
        collections_stats = {}
        for collection_name in ["users", "foks", "applications", "districts", "sports"]:
            count = await db[collection_name].count_documents({})
            collections_stats[collection_name] = count
        
        return {
            "database_size": stats.get("dataSize", 0),
            "collections": collections_stats,
            "indexes": stats.get("indexes", 0),
            "storage_size": stats.get("storageSize", 0)
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}
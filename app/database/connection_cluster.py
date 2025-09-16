import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from loguru import logger
from app.config import settings


class DatabaseClusterConnection:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


db_cluster_connection = DatabaseClusterConnection()


async def get_cluster_database() -> AsyncIOMotorDatabase:
    """Get database instance with cluster support"""
    if db_cluster_connection.database is None:
        await init_cluster_database()
    return db_cluster_connection.database


async def init_cluster_database():
    """Initialize database connection with MongoDB replica set"""
    try:
        # MongoDB replica set connection string
        replica_set_hosts = [
            f"{settings.MONGO_HOST}:27017",
            f"{settings.MONGO_HOST.replace('primary', 'secondary1')}:27017",
            f"{settings.MONGO_HOST.replace('primary', 'secondary2')}:27017"
        ]
        
        # Connection string for replica set
        if settings.MONGO_USERNAME and settings.MONGO_PASSWORD:
            connection_string = (
                f"mongodb://{settings.MONGO_USERNAME}:{settings.MONGO_PASSWORD}@"
                f"{','.join(replica_set_hosts)}/{settings.MONGO_DB_NAME}"
                f"?replicaSet=fok_replica&authSource=admin"
            )
        else:
            connection_string = (
                f"mongodb://{','.join(replica_set_hosts)}/{settings.MONGO_DB_NAME}"
                f"?replicaSet=fok_replica"
            )
        
        # Create MongoDB client with replica set support
        db_cluster_connection.client = AsyncIOMotorClient(
            connection_string,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            # Read preference - prefer secondary for read operations
            readPreference='secondaryPreferred',
            # Write concern - ensure writes are acknowledged by majority
            w='majority',
            wtimeout=5000
        )
        
        # Get database
        db_cluster_connection.database = db_cluster_connection.client[settings.MONGO_DB_NAME]
        
        # Test connection
        await db_cluster_connection.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB cluster: {settings.MONGO_DB_NAME}")
        
        # Get replica set status
        try:
            rs_status = await db_cluster_connection.client.admin.command('replSetGetStatus')
            logger.info(f"Replica set status: {rs_status['set']}, members: {len(rs_status['members'])}")
        except Exception as e:
            logger.warning(f"Could not get replica set status: {e}")
        
        # Create indexes
        await create_cluster_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB cluster: {e}")
        # Fallback to single instance
        logger.info("Falling back to single MongoDB instance")
        from .connection import init_database
        await init_database()


async def close_cluster_database():
    """Close database cluster connection"""
    if db_cluster_connection.client:
        db_cluster_connection.client.close()
        logger.info("Database cluster connection closed")


async def create_cluster_indexes():
    """Create database indexes optimized for cluster"""
    try:
        db = db_cluster_connection.database
        
        # Users indexes with read preference
        await db.users.create_index("telegram_id", unique=True)
        await db.users.create_index("phone")
        await db.users.create_index("is_admin")
        await db.users.create_index([("last_activity", -1)])
        
        # FOKs indexes
        await db.foks.create_index("name")
        await db.foks.create_index("district")
        await db.foks.create_index("sports")
        await db.foks.create_index([("is_active", 1), ("featured", -1), ("sort_order", 1)])
        
        # Applications indexes optimized for queries
        await db.applications.create_index("user_id")
        await db.applications.create_index("fok_id")
        await db.applications.create_index("status")
        await db.applications.create_index([("created_at", -1)])
        await db.applications.create_index([("user_id", 1), ("created_at", -1)])
        await db.applications.create_index([("status", 1), ("created_at", -1)])
        
        # Districts indexes
        await db.districts.create_index("name", unique=True)
        await db.districts.create_index([("is_active", 1), ("sort_order", 1)])
        
        # Sports indexes
        await db.sports.create_index("name", unique=True)
        await db.sports.create_index([("is_active", 1), ("sort_order", 1)])
        
        logger.info("Database cluster indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create cluster indexes: {e}")


async def check_cluster_health() -> dict:
    """Check cluster health"""
    try:
        if not db_cluster_connection.client:
            return {"status": "disconnected"}
        
        # Check primary connection
        await db_cluster_connection.client.admin.command('ping')
        
        # Get replica set status
        try:
            rs_status = await db_cluster_connection.client.admin.command('replSetGetStatus')
            
            members_status = []
            for member in rs_status['members']:
                members_status.append({
                    "name": member['name'],
                    "state": member['stateStr'],
                    "health": member['health'],
                    "uptime": member.get('uptime', 0)
                })
            
            return {
                "status": "healthy",
                "replica_set": rs_status['set'],
                "members": members_status,
                "primary": next((m['name'] for m in rs_status['members'] if m['stateStr'] == 'PRIMARY'), None)
            }
            
        except Exception as e:
            # Single instance fallback
            return {
                "status": "single_instance",
                "error": str(e)
            }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def get_cluster_stats() -> dict:
    """Get cluster statistics"""
    try:
        db = await get_cluster_database()
        
        # Basic stats
        stats = await db.command("dbStats")
        
        # Collection counts
        collections_stats = {}
        for collection_name in ["users", "foks", "applications", "districts", "sports"]:
            count = await db[collection_name].count_documents({})
            collections_stats[collection_name] = count
        
        # Replica set info
        cluster_info = await check_cluster_health()
        
        return {
            "database_size": stats.get("dataSize", 0),
            "collections": collections_stats,
            "indexes": stats.get("indexes", 0),
            "storage_size": stats.get("storageSize", 0),
            "cluster_info": cluster_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get cluster stats: {e}")
        return {}
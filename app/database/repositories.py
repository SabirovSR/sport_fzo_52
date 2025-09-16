from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger

from app.models import User, FOK, Application, District, Sport
from app.models.application import ApplicationStatus
from .connection import get_database


class BaseRepository:
    def __init__(self, collection_name: str, model_class):
        self.collection_name = collection_name
        self.model_class = model_class
    
    async def get_collection(self):
        db = await get_database()
        return db[self.collection_name]
    
    async def find_by_id(self, object_id: ObjectId) -> Optional[Any]:
        collection = await self.get_collection()
        data = await collection.find_one({"_id": object_id})
        return self.model_class(**data) if data else None
    
    async def create(self, obj: Any) -> Any:
        collection = await self.get_collection()
        data = obj.dict(exclude={"id"})
        result = await collection.insert_one(data)
        obj.id = result.inserted_id
        return obj
    
    async def update(self, obj: Any) -> Any:
        collection = await self.get_collection()
        obj.update_timestamp()
        data = obj.dict(exclude={"id"})
        await collection.update_one({"_id": obj.id}, {"$set": data})
        return obj
    
    async def delete(self, object_id: ObjectId) -> bool:
        collection = await self.get_collection()
        result = await collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
    
    async def count(self, filter_dict: Dict = None) -> int:
        collection = await self.get_collection()
        return await collection.count_documents(filter_dict or {})


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users", User)
    
    async def find_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        collection = await self.get_collection()
        data = await collection.find_one({"telegram_id": telegram_id})
        return User(**data) if data else None
    
    async def find_by_phone(self, phone: str) -> Optional[User]:
        collection = await self.get_collection()
        data = await collection.find_one({"phone": phone})
        return User(**data) if data else None
    
    async def get_admins(self) -> List[User]:
        collection = await self.get_collection()
        cursor = collection.find({"is_admin": True, "is_active": True})
        return [User(**data) async for data in cursor]
    
    async def get_super_admins(self) -> List[User]:
        collection = await self.get_collection()
        cursor = collection.find({"is_super_admin": True, "is_active": True})
        return [User(**data) async for data in cursor]
    
    async def update_activity(self, telegram_id: int):
        collection = await self.get_collection()
        await collection.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )
    
    async def get_active_users_count(self, days: int = 30) -> int:
        collection = await self.get_collection()
        since_date = datetime.utcnow() - timedelta(days=days)
        return await collection.count_documents({
            "last_activity": {"$gte": since_date},
            "is_active": True
        })


class DistrictRepository(BaseRepository):
    def __init__(self):
        super().__init__("districts", District)
    
    async def get_active_districts(self, skip: int = 0, limit: int = 10) -> List[District]:
        collection = await self.get_collection()
        cursor = collection.find(
            {"is_active": True}
        ).sort([("sort_order", 1), ("name", 1)]).skip(skip).limit(limit)
        return [District(**data) async for data in cursor]
    
    async def find_by_name(self, name: str) -> Optional[District]:
        collection = await self.get_collection()
        data = await collection.find_one({"name": name, "is_active": True})
        return District(**data) if data else None
    
    async def get_all_active(self) -> List[District]:
        collection = await self.get_collection()
        cursor = collection.find({"is_active": True}).sort([("sort_order", 1), ("name", 1)])
        return [District(**data) async for data in cursor]


class SportRepository(BaseRepository):
    def __init__(self):
        super().__init__("sports", Sport)
    
    async def get_active_sports(self, skip: int = 0, limit: int = 20) -> List[Sport]:
        collection = await self.get_collection()
        cursor = collection.find(
            {"is_active": True}
        ).sort([("sort_order", 1), ("name", 1)]).skip(skip).limit(limit)
        return [Sport(**data) async for data in cursor]
    
    async def find_by_name(self, name: str) -> Optional[Sport]:
        collection = await self.get_collection()
        data = await collection.find_one({"name": name, "is_active": True})
        return Sport(**data) if data else None
    
    async def get_all_active(self) -> List[Sport]:
        collection = await self.get_collection()
        cursor = collection.find({"is_active": True}).sort([("sort_order", 1), ("name", 1)])
        return [Sport(**data) async for data in cursor]


class FOKRepository(BaseRepository):
    def __init__(self):
        super().__init__("foks", FOK)
    
    async def get_by_district(self, district: str, skip: int = 0, limit: int = 10) -> List[FOK]:
        collection = await self.get_collection()
        cursor = collection.find({
            "district": district,
            "is_active": True
        }).sort([("featured", -1), ("sort_order", 1), ("name", 1)]).skip(skip).limit(limit)
        return [FOK(**data) async for data in cursor]
    
    async def count_by_district(self, district: str) -> int:
        collection = await self.get_collection()
        return await collection.count_documents({
            "district": district,
            "is_active": True
        })
    
    async def search_by_sports(self, sports: List[str], skip: int = 0, limit: int = 10) -> List[FOK]:
        collection = await self.get_collection()
        cursor = collection.find({
            "sports": {"$in": sports},
            "is_active": True
        }).sort([("featured", -1), ("sort_order", 1), ("name", 1)]).skip(skip).limit(limit)
        return [FOK(**data) async for data in cursor]
    
    async def get_featured(self, limit: int = 5) -> List[FOK]:
        collection = await self.get_collection()
        cursor = collection.find({
            "featured": True,
            "is_active": True
        }).sort([("sort_order", 1), ("name", 1)]).limit(limit)
        return [FOK(**data) async for data in cursor]
    
    async def increment_applications_count(self, fok_id: ObjectId):
        collection = await self.get_collection()
        await collection.update_one(
            {"_id": fok_id},
            {"$inc": {"total_applications": 1}}
        )
    
    async def get_popular(self, limit: int = 10) -> List[FOK]:
        collection = await self.get_collection()
        cursor = collection.find({
            "is_active": True
        }).sort([("total_applications", -1), ("name", 1)]).limit(limit)
        return [FOK(**data) async for data in cursor]


class ApplicationRepository(BaseRepository):
    def __init__(self):
        super().__init__("applications", Application)
    
    async def get_user_applications(self, user_id: ObjectId, skip: int = 0, limit: int = 10) -> List[Application]:
        collection = await self.get_collection()
        cursor = collection.find({
            "user_id": user_id,
            "is_active": True
        }).sort([("created_at", -1)]).skip(skip).limit(limit)
        return [Application(**data) async for data in cursor]
    
    async def count_user_applications(self, user_id: ObjectId) -> int:
        collection = await self.get_collection()
        return await collection.count_documents({
            "user_id": user_id,
            "is_active": True
        })
    
    async def has_user_applied_to_fok(self, user_id: ObjectId, fok_id: ObjectId) -> bool:
        collection = await self.get_collection()
        count = await collection.count_documents({
            "user_id": user_id,
            "fok_id": fok_id,
            "status": {"$nin": [ApplicationStatus.CANCELLED, ApplicationStatus.REJECTED]},
            "is_active": True
        })
        return count > 0
    
    async def get_by_status(self, status: ApplicationStatus, skip: int = 0, limit: int = 10) -> List[Application]:
        collection = await self.get_collection()
        cursor = collection.find({
            "status": status,
            "is_active": True
        }).sort([("created_at", -1)]).skip(skip).limit(limit)
        return [Application(**data) async for data in cursor]
    
    async def get_recent_applications(self, days: int = 7, limit: int = 100) -> List[Application]:
        collection = await self.get_collection()
        since_date = datetime.utcnow() - timedelta(days=days)
        cursor = collection.find({
            "created_at": {"$gte": since_date},
            "is_active": True
        }).sort([("created_at", -1)]).limit(limit)
        return [Application(**data) async for data in cursor]
    
    async def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        collection = await self.get_collection()
        since_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"created_at": {"$gte": since_date}, "is_active": True}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        result = {}
        async for doc in collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        
        return result
    
    async def search_applications(self, query: str, skip: int = 0, limit: int = 10) -> List[Application]:
        collection = await self.get_collection()
        cursor = collection.find({
            "$or": [
                {"user_name": {"$regex": query, "$options": "i"}},
                {"user_phone": {"$regex": query, "$options": "i"}},
                {"fok_name": {"$regex": query, "$options": "i"}},
                {"fok_district": {"$regex": query, "$options": "i"}}
            ],
            "is_active": True
        }).sort([("created_at", -1)]).skip(skip).limit(limit)
        return [Application(**data) async for data in cursor]


# Repository instances
user_repo = UserRepository()
district_repo = DistrictRepository()
sport_repo = SportRepository()
fok_repo = FOKRepository()
application_repo = ApplicationRepository()
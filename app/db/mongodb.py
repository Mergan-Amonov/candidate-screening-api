from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)

db = client[settings.mongo_db_name]

users_collection = db["users"]
jobs_collection = db["jobs"]
applications_collection = db["applications"]

from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.db.mongodb import jobs_collection


def serialize_job(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


async def create_job(data: dict) -> str:
    job = {
        "title": data["title"],
        "description": data["description"],
        "required_skills": data["required_skills"],
        "min_experience_years": data["min_experience_years"],
        "is_active": data.get("is_active", True),
        "created_at": datetime.utcnow(),
    }
    result = await jobs_collection.insert_one(job)
    return str(result.inserted_id)


async def get_job(job_id: str) -> Optional[dict]:
    return await jobs_collection.find_one({"_id": ObjectId(job_id)})


async def list_jobs(
    is_active: Optional[bool] = None,
    required_skill: Optional[str] = None,
    min_experience_lte: Optional[int] = None,
    limit: int = 20,
    skip: int = 0,
) -> list:
    query: dict = {}
    if is_active is not None:
        query["is_active"] = is_active
    if required_skill is not None:
        # case-insensitive "contains" match within the required_skills array
        query["required_skills"] = {"$regex": required_skill, "$options": "i"}
    if min_experience_lte is not None:
        query["min_experience_years"] = {"$lte": min_experience_lte}

    cursor = jobs_collection.find(query).skip(skip).limit(limit)
    return [serialize_job(doc) async for doc in cursor]


async def deactivate_job(job_id: str) -> bool:
    result = await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"is_active": False}},
    )
    return result.matched_count > 0

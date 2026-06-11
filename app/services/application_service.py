from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.db.mongodb import applications_collection


def serialize_application(doc: dict) -> dict:
    """Convert a MongoDB application document into a JSON-serializable dict."""
    return {
        "id": str(doc["_id"]),
        "job_id": str(doc.get("job_id")),
        "candidate_name": doc.get("candidate_name"),
        "email": doc.get("email"),
        "years_of_experience": doc.get("years_of_experience"),
        "skills": doc.get("skills", []),
        "resume_text": doc.get("resume_text"),
        "status": doc.get("status"),
        "score": doc.get("score"),
        "ai_department": doc.get("ai_department"),
        "ai_department_score": doc.get("ai_department_score"),
        "created_at": doc.get("created_at"),
        "scored_at": doc.get("scored_at"),
        "ai_processed_at": doc.get("ai_processed_at"),
    }


async def find_duplicate(job_id: str, email: str) -> Optional[dict]:
    """Return an existing application for the same job + email, if any."""
    return await applications_collection.find_one(
        {"job_id": job_id, "email": email}
    )


async def create_application(job_id: str, data: dict) -> str:
    application = {
        "job_id": job_id,
        "candidate_name": data["candidate_name"],
        "email": data["email"],
        "years_of_experience": data["years_of_experience"],
        "skills": data.get("skills", []),
        "resume_text": data["resume_text"],
        "status": "submitted",
        "score": None,
        "ai_department": None,
        "ai_department_score": None,
        "ai_processed_at": None,
        "created_at": datetime.utcnow(),
        "scored_at": None,
    }
    result = await applications_collection.insert_one(application)
    return str(result.inserted_id)


async def get_application(application_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(application_id)
    except Exception:
        return None
    return await applications_collection.find_one({"_id": oid})


async def list_applications(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    limit: int = 20,
    skip: int = 0,
) -> list:
    query: dict = {}
    if job_id is not None:
        query["job_id"] = job_id
    if status is not None:
        query["status"] = status
    if min_score is not None:
        query["score"] = {"$gte": min_score}

    cursor = (
        applications_collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [serialize_application(doc) async for doc in cursor]

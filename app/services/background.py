import asyncio
import logging
from datetime import datetime
from bson import ObjectId

from app.db.mongodb import applications_collection, jobs_collection
from app.services.ai_service import ai_department_eval
from app.services.scoring_service import compute_score

logger = logging.getLogger("screening")


async def process_application(application_id: str):
    """Background pipeline: submitted -> processing -> scored."""
    logger.info("Processing application %s", application_id)

    application = await applications_collection.find_one(
        {"_id": ObjectId(application_id)}
    )
    if not application:
        logger.warning("Application %s not found", application_id)
        return

    # Mark as processing
    await applications_collection.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": {"status": "processing"}},
    )

    # Rule-based score (needs the job for required skills / experience)
    job = None
    job_id = application.get("job_id")
    if job_id:
        try:
            job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
        except Exception:
            job = None

    score = compute_score(application, job or {})

    # AI department recommendation (CPU-bound -> run off the event loop)
    resume_text = application.get("resume_text", "")
    department, department_score = await asyncio.to_thread(
        ai_department_eval, resume_text
    )

    now = datetime.utcnow()
    await applications_collection.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": {
            "status": "scored",
            "score": score,
            "scored_at": now,
            "ai_department": department,
            "ai_department_score": department_score,
            "ai_processed_at": now,
        }},
    )
    logger.info(
        "Application %s scored: %s, department: %s",
        application_id, score, department,
    )

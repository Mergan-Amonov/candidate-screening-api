from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, status

from app.schemas.application_schema import (
    ApplicationCreate,
    ApplicationResponse,
    AIEvaluationResponse,
)
from app.services.application_service import (
    create_application,
    get_application,
    list_applications,
    find_duplicate,
    serialize_application,
)
from app.services.job_service import get_job
from app.services.background import process_application
from app.core.dependencies import get_current_user

router = APIRouter(tags=["Applications"])


# ==================================================
# APPLY TO JOB (PUBLIC — candidates apply without auth)
# ==================================================
@router.post("/jobs/{job_id}/apply", status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: str,
    application: ApplicationCreate,
    background_tasks: BackgroundTasks,
):
    # 1. Job must exist
    try:
        job = await get_job(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2. Job must be active
    if not job.get("is_active", False):
        raise HTTPException(status_code=400, detail="Job is not active")

    # 3. Cannot apply twice to the same job with the same email
    if await find_duplicate(job_id, application.email):
        raise HTTPException(
            status_code=409,
            detail="You have already applied to this job",
        )

    # 4. Create the application (status: submitted)
    application_id = await create_application(job_id, application.model_dump())

    # 5. Trigger background scoring + AI evaluation
    background_tasks.add_task(process_application, application_id)

    return {
        "message": "Application submitted",
        "application_id": application_id,
        "status": "submitted",
    }


# ==================================================
# LIST APPLICATIONS (PROTECTED — recruiters/admins)
# ==================================================
@router.get("/applications", response_model=list[ApplicationResponse])
async def get_applications(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user),
):
    return await list_applications(
        job_id=job_id,
        status=status,
        min_score=min_score,
        limit=limit,
        skip=skip,
    )


# ==================================================
# GET AI EVALUATION FOR AN APPLICATION
# ==================================================
@router.get(
    "/applications/{id}/ai-evaluation",
    response_model=AIEvaluationResponse,
)
async def get_ai_evaluation(id: str):
    doc = await get_application(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Application not found")

    data = serialize_application(doc)
    return {
        "department_recommendation": data["ai_department"],
        "department_score": data["ai_department_score"],
        "status": data["status"],
    }

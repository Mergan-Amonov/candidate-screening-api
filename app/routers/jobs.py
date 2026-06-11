from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.schemas.job_schema import JobCreate
from app.services.job_service import (
    create_job, get_job, list_jobs, deactivate_job, serialize_job
)
from app.core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", status_code=201)
async def create(job: JobCreate, current_user=Depends(get_current_user)):
    job_id = await create_job(job.model_dump())
    return {"id": job_id}


@router.get("/")
async def list_all(
    is_active: Optional[bool] = None,
    required_skill: Optional[str] = None,
    min_experience_lte: Optional[int] = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user),
):
    return await list_jobs(
        is_active=is_active,
        required_skill=required_skill,
        min_experience_lte=min_experience_lte,
        limit=limit,
        skip=skip,
    )


@router.get("/{id}")
async def get(id: str, current_user=Depends(get_current_user)):
    try:
        job = await get_job(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return serialize_job(job)


@router.patch("/{id}/deactivate")
async def deactivate(id: str, current_user=Depends(require_admin)):
    try:
        ok = await deactivate_job(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")

    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job deactivated"}

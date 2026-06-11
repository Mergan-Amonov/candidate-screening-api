from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class ApplicationCreate(BaseModel):
    candidate_name: str = Field(..., min_length=1)
    email: EmailStr
    years_of_experience: int = Field(..., ge=0)
    skills: List[str] = Field(default_factory=list)
    resume_text: str = Field(..., min_length=1)


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    candidate_name: str
    email: EmailStr
    years_of_experience: int
    skills: List[str]
    resume_text: str
    status: str
    score: Optional[int] = None
    ai_department: Optional[str] = None
    ai_department_score: Optional[float] = None
    created_at: Optional[datetime] = None
    scored_at: Optional[datetime] = None
    ai_processed_at: Optional[datetime] = None


class AIEvaluationResponse(BaseModel):
    department_recommendation: Optional[str] = None
    department_score: Optional[float] = None
    status: str

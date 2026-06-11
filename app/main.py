import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.mongodb import applications_collection, jobs_collection
from app.routers.auth import router as auth_router
from app.routers.jobs import router as jobs_router
from app.routers.applications import router as applications_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure indexes (bonus): prevents duplicate applications and speeds filters
    await applications_collection.create_index(
        [("job_id", 1), ("email", 1)], unique=True
    )
    await applications_collection.create_index([("status", 1)])
    await applications_collection.create_index([("score", -1)])
    await jobs_collection.create_index([("is_active", 1)])
    yield


app = FastAPI(
    title="Candidate Screening Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(applications_router)


@app.get("/", tags=["Health"])
async def health():
    return {"status": "ok"}

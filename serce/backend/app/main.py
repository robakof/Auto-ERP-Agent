from contextlib import asynccontextmanager

from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import v1_router
from app.config import settings
from app.core.rate_limit import limiter
from app.services.scheduler_service import expire_requests_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncScheduler() as scheduler:
        await scheduler.add_schedule(
            expire_requests_job,
            IntervalTrigger(minutes=settings.request_expiry_check_interval_minutes),
            id="expire_requests",
        )
        await scheduler.start_in_background()
        yield


app = FastAPI(
    title="Serce API",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)

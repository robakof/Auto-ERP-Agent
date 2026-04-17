from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.health import router as health_router
from app.api.v1.exchanges import router as exchanges_router
from app.api.v1.hearts import router as hearts_router
from app.api.v1.locations import router as locations_router
from app.api.v1.messages import router as messages_router
from app.api.v1.offers import router as offers_router
from app.api.v1.requests import router as requests_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.users import router as users_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(hearts_router)
v1_router.include_router(requests_router)
v1_router.include_router(offers_router)
v1_router.include_router(exchanges_router)
v1_router.include_router(messages_router)
v1_router.include_router(reviews_router)
v1_router.include_router(locations_router)
v1_router.include_router(categories_router)

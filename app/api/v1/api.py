from fastapi import APIRouter
from app.api.v1.endpoints import chat, health, security_status, storage

api_router = APIRouter()

# Include all API routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

api_router.include_router(
    security_status.router,
    prefix="/security",
    tags=["security"]
)

api_router.include_router(
    storage.router,
    prefix="/storage",
    tags=["storage"]
)

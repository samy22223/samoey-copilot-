from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Import all route modules here
from . import auth, users, conversations, messages, files, settings

# Include all routers
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(users.router, tags=["Users"], prefix="/users")
api_router.include_router(conversations.router, tags=["Conversations"], prefix="/conversations")
api_router.include_router(messages.router, tags=["Messages"], prefix="/messages")
api_router.include_router(files.router, tags=["Files"], prefix="/files")
api_router.include_router(settings.router, tags=["Settings"], prefix="/settings")

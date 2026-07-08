# from fastapi import APIRouter

# from app.modules.authentication.router import router as auth_router

# # Day 1: only auth router
# # Days 2-6 you will add more routers here:
# # from app.modules.datasets.router import router as datasets_router
# # from app.modules.chat.router import router as chat_router
# # etc.

# api_router = APIRouter(prefix="/api/v1")
# api_router.include_router(auth_router)

from fastapi import APIRouter

from app.modules.authentication.router import router as auth_router
from app.modules.datasets.router import router as datasets_router
from app.modules.chat.router import router as chat_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(datasets_router)
api_router.include_router(chat_router) 
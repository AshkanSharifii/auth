from fastapi import APIRouter

from src.presentation.rest.auth.router import router as auth_router
from src.presentation.rest.user.router import router as user_router
from src.presentation.rest.admin.router import router as admin_router

# ----------------------------------------------------------------------------
routes = APIRouter()

# ----------------------------------------------------------------------------
routes.include_router(user_router, prefix="", tags=["user"])
routes.include_router(auth_router, prefix="/auth", tags=["auth"])
routes.include_router(admin_router, prefix="/admin", tags=["admin"])
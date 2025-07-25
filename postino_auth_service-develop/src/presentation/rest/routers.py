from fastapi import APIRouter

from src.presentation.rest.auth.router import router as auth_router
from src.presentation.rest.user.router import router as user_router
from src.presentation.rest.brands.router import router as user_brands_router
from src.presentation.rest.industries.router import router as brand_industries_router
from src.presentation.rest.tones.router import router as brand_tones_router

# ----------------------------------------------------------------------------
routes = APIRouter()

# ----------------------------------------------------------------------------
routes.include_router(user_router, prefix="", tags=["user"])
routes.include_router(auth_router, prefix="/auth", tags=["auth"])
routes.include_router(user_brands_router, prefix="/brands", tags=['Brands'])
routes.include_router(brand_industries_router, prefix="/brands/industries", tags=['Brands'])
routes.include_router(brand_tones_router, prefix='/brands/tones', tags=['Brands'])

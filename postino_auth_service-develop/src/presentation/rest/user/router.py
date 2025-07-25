from dependency_injector.wiring import inject
from fastapi import APIRouter, Depends

from src.application.dtos.user_dto import UserMeDTO
from src.presentation.rest.user.dependencies import get_current_user

# ----------------------------------------------------------------------------
router = APIRouter()


# ----------------------------------------------------------------------------
@router.get("/me", response_model=UserMeDTO)
@inject
async def get_user_me(user_data: tuple = Depends(get_current_user)):
    user, role = user_data
    return UserMeDTO(
        name=user.name,
        family=user.family,
        phone_number=user.phone_number,
        email=user.email,
        position=user.position,
        personal_code=user.personal_code,
        id=user.id,
        latest_login=user.latest_login,
        role_id=user.role_id,
        role_name=role.role_name,
        is_verified=user.is_verified,
        email_verified=user.email_verified,
        phone_number_verified=user.phone_number_verified,
        is_active=user.is_active,
    )
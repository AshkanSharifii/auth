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
    user, role, brands = user_data
    return UserMeDTO(
        name=user.name,
        family=user.family,
        phone_number=user.phone_number,
        id=user.id,
        latest_login=user.latest_login,
        role_id=user.role_id,
        role_name=role.role_name,
        brands=[brand.to_dict() for brand in brands] if brands else None,
    )

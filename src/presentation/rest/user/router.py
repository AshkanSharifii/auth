from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dtos.user_dto import UserMeDTO
from src.application.dtos.admin_dtos import LoginHistoryListDTO, LoginHistoryDTO
from src.application.use_cases.login_history_use_case import GetMyLoginHistoryUseCase
from src.di.container import Container
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


# ----------------------------------------------------------------------------
@router.get("/me/login-history", response_model=LoginHistoryListDTO)
@inject
async def get_my_login_history(
        *,
        get_my_login_history_use_case: GetMyLoginHistoryUseCase = Depends(
            Provide[Container.get_my_login_history_use_case_provider]
        ),
        user_data: tuple = Depends(get_current_user),
        limit: int = 50,
        offset: int = 0
):
    """
    Get current user's login history.
    """
    try:
        user, role = user_data

        login_history = await get_my_login_history_use_case.execute(
            user=user,
            limit=limit,
            offset=offset
        )

        # Convert to DTOs
        history_dtos = []
        for history in login_history:
            history_dto = LoginHistoryDTO(
                user_id=history.user_id,
                login_time=history.login_time,
                ip_address=history.ip_address,
                user_agent=history.user_agent,
                login_method=history.login_method,
                success=history.success,
                failure_reason=history.failure_reason,
                id=history.id
            )
            history_dtos.append(history_dto)

        return LoginHistoryListDTO(
            login_history=history_dtos,
            total_count=len(history_dtos)
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
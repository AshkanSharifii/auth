from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer

from src.application.use_cases.get_current_user_use_case import GetCurrentUserUseCase
from src.di.container import Container
from src.domain.exceptions import UserNotFound

# ----------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/password")


# ----------------------------------------------------------------------------
@inject
async def get_current_admin_user(
        *,
        token: str = Security(oauth2_scheme),
        get_current_user_use_case: GetCurrentUserUseCase = Depends(
            Provide[Container.get_current_user_use_case]
        )
):
    """
    Dependency to get current user and verify they have admin privileges.
    NOTE: This is kept for potential future use, but currently most features require super_admin.

    Returns:
        tuple: (user, role) if user is admin/super_admin

    Raises:
        HTTPException: If user is not found or doesn't have admin privileges
    """
    try:
        user, role = await get_current_user_use_case.execute(token=token)

        # Check if user has admin privileges
        if role.role_name not in ["super_admin", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient privileges. Admin access required."
            )

        return user, role
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----------------------------------------------------------------------------
@inject
async def get_current_super_admin_user(
        *,
        token: str = Security(oauth2_scheme),
        get_current_user_use_case: GetCurrentUserUseCase = Depends(
            Provide[Container.get_current_user_use_case]
        )
):
    """
    Dependency to get current user and verify they have super admin privileges.

    Returns:
        tuple: (user, role) if user is super_admin

    Raises:
        HTTPException: If user is not found or doesn't have super admin privileges
    """
    try:
        user, role = await get_current_user_use_case.execute(token=token)

        # Check if user has super admin privileges
        if role.role_name != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Insufficient privileges. Super admin access required."
            )

        return user, role
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
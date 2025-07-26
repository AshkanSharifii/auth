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
async def get_current_user(
    *,
    token: str = Security(oauth2_scheme),
    get_current_user_use_case: GetCurrentUserUseCase = Depends(
        Provide[Container.get_current_user_use_case]
    )
):
    try:
        user, role = await get_current_user_use_case.execute(token=token)
        return user, role
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
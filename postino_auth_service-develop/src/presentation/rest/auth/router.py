from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from src.application.dtos.access_token_dto import AccessTokenDTO
from src.application.dtos.refresh_token_dto import RefreshTokenDTO, RefreshTokenOutDTO
from src.application.dtos.user_dto import RegisterUserDTO, SubmitCodeDTO, UserBaseDTO
from src.application.use_cases.login_with_password_use_case import LoginWithPasswordUseCase
from src.application.use_cases.otp_login_use_case import OTPLoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.resend_code_use_case import ResendCodeUseCase
from src.application.use_cases.submit_verification_code_use_case import (
    SubmitVerificationCodeUseCase,
)
from src.di.container import Container
from src.domain.exceptions import (
    CredentialError,
    ExpRefreshToken,
    IncorrectVerificationCode,
    InvalidRefreshToken,
    NotifyUserError,
    NotVerifiedUser,
    UserExist,
    UserIsLocked,
    UserNotFound,
    VerificationCodeExist,
    VerificationCodeExpired,
)

# ----------------------------------------------------------------------------
router = APIRouter()


# ----------------------------------------------------------------------------
@router.post("/login/password", status_code=status.HTTP_200_OK, response_model=AccessTokenDTO)
@inject
async def user_login_password(
    *,
    login_password_use_case: LoginWithPasswordUseCase = Depends(
        Provide[Container.login_with_password_use_case_provider]
    ),
    login_password_dto: OAuth2PasswordRequestForm = Depends()
):
    try:
        response = await login_password_use_case.execute(
            identifier=login_password_dto.username, password=login_password_dto.password
        )
        return response
    except UserNotFound as not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(not_found))
    except NotVerifiedUser as not_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(not_verified))
    except UserIsLocked as is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(is_locked))
    except CredentialError as credential_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(credential_error))


# ----------------------------------------------------------------------------
@router.post("/login/otp", status_code=status.HTTP_200_OK)
@inject
async def user_login_otp(
    *,
    otp_login_use_case: OTPLoginUseCase = Depends(Provide[Container.otp_login_use_case_provider]),
    otp_login_dto: UserBaseDTO
):
    try:
        response = await otp_login_use_case.execute(phone_number=otp_login_dto.phone_number)
        return response
    except UserNotFound as not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(not_found))
    except VerificationCodeExist as verification_code_exist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(verification_code_exist)
        )
    except UserIsLocked as is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(is_locked))
    except NotifyUserError as notification_service_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(notification_service_error)
        )


# ----------------------------------------------------------------------------
@router.post("/register", response_model=UserBaseDTO, status_code=status.HTTP_201_CREATED)
@inject
async def register_user(
    *,
    register_user_use_case: RegisterUserUseCase = Depends(
        Provide[Container.register_user_use_case_provider]
    ),
    register_user_dto: RegisterUserDTO
):
    try:
        response = await register_user_use_case.execute(
            phone_number=register_user_dto.phone_number,
            email=register_user_dto.email,
            name=register_user_dto.name,
            family=register_user_dto.family,
            position=register_user_dto.position,
            personal_code=register_user_dto.personal_code,
            password=register_user_dto.password,
        )
        return response
    except UserExist as user_exist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(user_exist))
    except NotifyUserError as not_verified:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(not_verified)
        )


# ----------------------------------------------------------------------------
@router.post("/code/submit", response_model=AccessTokenDTO, status_code=status.HTTP_200_OK)
@inject
async def submit_code(
    *,
    submit_code_use_case: SubmitVerificationCodeUseCase = Depends(
        Provide[Container.submit_verification_code_use_case_provider]
    ),
    submit_code_dto: SubmitCodeDTO
):
    try:
        response = await submit_code_use_case.execute(
            phone_number=submit_code_dto.phone_number, code=submit_code_dto.code
        )
        return response
    except UserIsLocked as is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(is_locked))
    except VerificationCodeExpired as verification_code_expired:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(verification_code_expired)
        )
    except IncorrectVerificationCode as incorrect_verification_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(incorrect_verification_code)
        )
    except UserNotFound as user_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(user_not_found))


# ----------------------------------------------------------------------------
@router.post("/code/resend", status_code=status.HTTP_200_OK)
@inject
async def resend_code(
    *,
    resend_code_use_case: ResendCodeUseCase = Depends(
        Provide[Container.resend_code_use_case_provider]
    ),
    resend_code_dto: UserBaseDTO
):
    try:
        response = await resend_code_use_case.execute(phone_number=resend_code_dto.phone_number)
        return response
    except VerificationCodeExist as verification_code_exist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(verification_code_exist)
        )
    except NotifyUserError as notify_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(notify_error)
        )
    except UserNotFound as not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(not_found))


# ----------------------------------------------------------------------------
@router.post("/refresh", response_model=RefreshTokenOutDTO, status_code=status.HTTP_200_OK)
@inject
async def refresh_token(
    refresh_token_dto: RefreshTokenDTO,
    refresh: RefreshTokenUseCase = Depends(Provide[Container.refresh_token_use_case_provider]),
):

    try:
        access_token = await refresh.execute(refresh_token=refresh_token_dto.refresh_token)
        return access_token
    except ExpRefreshToken as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except UserNotFound as user_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(user_not_found))
    except InvalidRefreshToken as invalid_refresh:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(invalid_refresh))
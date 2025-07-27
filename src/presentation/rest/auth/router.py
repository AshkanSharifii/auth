from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from src.application.dtos.access_token_dto import AccessTokenDTO
from src.application.dtos.refresh_token_dto import RefreshTokenDTO, RefreshTokenOutDTO
from src.application.dtos.user_dto import (
    RegisterUserDTO,
    SubmitCodeDTO,
    UserBaseDTO,
    EmailOTPRequestDTO,
    EmailOTPVerifyDTO,
    LoginDTO
)
from src.application.dtos.admin_dtos import (
    EmailVerificationDTO,
    AdminActionResponseDTO,
    EmailVerificationSubmitDTO
)
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


# ============================================================================
# PASSWORD AUTHENTICATION
# ============================================================================

@router.post("/login/password", status_code=status.HTTP_200_OK, response_model=AccessTokenDTO)
@inject
async def login_with_password(
        *,
        login_password_use_case: LoginWithPasswordUseCase = Depends(
            Provide[Container.login_with_password_use_case_provider]
        ),
        login_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Login with email and password.

    Username field should contain the email address.
    """
    try:
        response = await login_password_use_case.execute(
            email=login_data.username,
            password=login_data.password
        )
        return response
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotVerifiedUser as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UserIsLocked as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CredentialError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/login", status_code=status.HTTP_200_OK, response_model=AccessTokenDTO)
@inject
async def login_with_email_password(
        *,
        login_password_use_case: LoginWithPasswordUseCase = Depends(
            Provide[Container.login_with_password_use_case_provider]
        ),
        login_data: LoginDTO
):
    """
    Alternative login endpoint with email and password.
    """
    try:
        response = await login_password_use_case.execute(
            email=login_data.email,
            password=login_data.password
        )
        return response
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotVerifiedUser as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UserIsLocked as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CredentialError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ============================================================================
# EMAIL OTP AUTHENTICATION
# ============================================================================

@router.post("/otp/send", status_code=status.HTTP_200_OK)
@inject
async def send_email_otp(
        *,
        otp_login_use_case: OTPLoginUseCase = Depends(Provide[Container.otp_login_use_case_provider]),
        request: EmailOTPRequestDTO
):
    """
    Send OTP to email address for authentication.
    """
    try:
        response = await otp_login_use_case.execute(email=request.email)
        return response
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except UserIsLocked as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/otp/verify", response_model=AccessTokenDTO, status_code=status.HTTP_200_OK)
@inject
async def verify_email_otp(
        *,
        submit_code_use_case: SubmitVerificationCodeUseCase = Depends(
            Provide[Container.submit_verification_code_use_case_provider]
        ),
        otp_data: EmailOTPVerifyDTO
):
    """
    Verify email OTP and get authentication tokens.
    """
    try:
        response = await submit_code_use_case.execute(
            email=otp_data.email,
            code=otp_data.code
        )
        return response
    except UserIsLocked as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VerificationCodeExpired as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IncorrectVerificationCode as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/otp/resend", status_code=status.HTTP_200_OK)
@inject
async def resend_email_otp(
        *,
        resend_code_use_case: ResendCodeUseCase = Depends(
            Provide[Container.resend_code_use_case_provider]
        ),
        request: EmailOTPRequestDTO
):
    """
    Resend OTP to email address.
    """
    try:
        response = await resend_code_use_case.execute_email_otp(email=request.email)
        return response
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# USER REGISTRATION
# ============================================================================

@router.post("/register", response_model=UserBaseDTO, status_code=status.HTTP_201_CREATED)
@inject
async def register_user(
        *,
        register_user_use_case: RegisterUserUseCase = Depends(
            Provide[Container.register_user_use_case_provider]
        ),
        register_data: RegisterUserDTO
):
    """
    Register a new user account.

    Phone number is optional (for contact purposes only).
    Email verification code will be sent automatically.
    """
    try:
        response = await register_user_use_case.execute(
            email=register_data.email,
            name=register_data.name,
            family=register_data.family,
            position=register_data.position,
            personal_code=register_data.personal_code,
            password=register_data.password,
            phone_number=register_data.phone_number,
        )
        return response
    except UserExist as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ============================================================================
# EMAIL VERIFICATION (REGISTRATION)
# ============================================================================

@router.post("/email/verify", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def verify_email_for_registration(
        *,
        submit_code_use_case: SubmitVerificationCodeUseCase = Depends(
            Provide[Container.submit_verification_code_use_case_provider]
        ),
        verification_data: EmailVerificationSubmitDTO
):
    """
    Verify email address with verification code (for registration).
    """
    try:
        response = await submit_code_use_case.execute_registration_verification(
            email=verification_data.email,
            code=verification_data.code
        )
        return AdminActionResponseDTO(
            success=True,
            message="Email address verified successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExpired as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IncorrectVerificationCode as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/email/resend", status_code=status.HTTP_200_OK)
@inject
async def resend_email_verification(
        *,
        resend_code_use_case: ResendCodeUseCase = Depends(
            Provide[Container.resend_code_use_case_provider]
        ),
        request: EmailOTPRequestDTO
):
    """
    Resend email verification code (for registration).
    """
    try:
        response = await resend_code_use_case.execute_email_verification(email=request.email)
        return response
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# TOKEN REFRESH
# ============================================================================

@router.post("/refresh", response_model=RefreshTokenOutDTO, status_code=status.HTTP_200_OK)
@inject
async def refresh_token(
        refresh_token_dto: RefreshTokenDTO,
        refresh: RefreshTokenUseCase = Depends(Provide[Container.refresh_token_use_case_provider]),
):
    """
    Refresh access token using refresh token.
    """
    try:
        access_token = await refresh.execute(refresh_token=refresh_token_dto.refresh_token)
        return access_token
    except ExpRefreshToken as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidRefreshToken as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ============================================================================
# LEGACY/DEPRECATED ENDPOINTS (for backward compatibility)
# ============================================================================

@router.post("/code/submit", response_model=AccessTokenDTO, status_code=status.HTTP_200_OK)
@inject
async def submit_code_legacy(
        *,
        submit_code_use_case: SubmitVerificationCodeUseCase = Depends(
            Provide[Container.submit_verification_code_use_case_provider]
        ),
        submit_code_dto: SubmitCodeDTO
):
    """
    LEGACY: Submit verification code for email verification and login.
    Use /otp/verify instead.
    """
    try:
        response = await submit_code_use_case.execute(
            email=submit_code_dto.email,
            code=submit_code_dto.code
        )
        return response
    except UserIsLocked as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VerificationCodeExpired as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IncorrectVerificationCode as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
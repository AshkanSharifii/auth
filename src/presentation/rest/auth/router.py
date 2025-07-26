from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional

from src.application.dtos.access_token_dto import AccessTokenDTO
from src.application.dtos.refresh_token_dto import RefreshTokenDTO, RefreshTokenOutDTO
from src.application.dtos.user_dto import RegisterUserDTO, SubmitCodeDTO, UserBaseDTO
from src.application.dtos.admin_dtos import (
    EmailVerificationDTO,
    AdminActionResponseDTO,
    PhoneVerificationDTO,
    SubmitPhoneVerificationDTO
)
from src.application.use_cases.login_with_password_use_case import LoginWithPasswordUseCase
from src.application.use_cases.otp_login_use_case import OTPLoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.resend_code_use_case import ResendCodeUseCase
from src.application.use_cases.submit_verification_code_use_case import (
    SubmitVerificationCodeUseCase,
)
from src.application.use_cases.confirm_email_use_case import ConfirmEmailUseCase
from src.application.use_cases.confirm_phone_use_case import (
    ConfirmPhoneUseCase,
    SubmitPhoneVerificationUseCase
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


# NEW DTOs for flexible login and OTP
class FlexibleLoginRequestDTO(BaseModel):
    identifier: str  # email, phone, or personal_code
    password: Optional[str] = None
    send_otp: bool = False


class OTPRequestDTO(BaseModel):
    identifier: str  # email or phone number


class OTPVerificationDTO(BaseModel):
    identifier: str  # email or phone number
    code: str


class OTPVerifyRequestDTO(BaseModel):
    identifier: str  # email, phone, or personal_code
    otp: str


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
    """
    User login with password (username can be email, phone, or personal code).
    """
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
@router.post("/login/flexible", status_code=status.HTTP_200_OK)
@inject
async def flexible_login(
        *,
        login_password_use_case: LoginWithPasswordUseCase = Depends(
            Provide[Container.login_with_password_use_case_provider]
        ),
        login_dto: FlexibleLoginRequestDTO
):
    """
    Flexible login endpoint:
    1. identifier + password = Direct login with tokens
    2. identifier + send_otp=true = Send OTP
    3. identifier only (no password) = Send OTP
    """
    try:
        response = await login_password_use_case.execute(
            identifier=login_dto.identifier,
            password=login_dto.password,
            send_otp=login_dto.send_otp
        )
        return response

    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotVerifiedUser as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UserIsLocked as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CredentialError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ----------------------------------------------------------------------------
@router.post("/login/verify-otp", status_code=status.HTTP_200_OK, response_model=AccessTokenDTO)
@inject
async def verify_login_otp(
        *,
        login_password_use_case: LoginWithPasswordUseCase = Depends(
            Provide[Container.login_with_password_use_case_provider]
        ),
        otp_dto: OTPVerifyRequestDTO
):
    """
    Verify OTP for flexible login and get access tokens
    """
    try:
        response = await login_password_use_case.verify_login_otp(
            identifier=otp_dto.identifier,
            otp=otp_dto.otp
        )
        return response

    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CredentialError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ----------------------------------------------------------------------------
@router.post("/login/otp", status_code=status.HTTP_200_OK)
@inject
async def user_login_otp(
        *,
        otp_login_use_case: OTPLoginUseCase = Depends(Provide[Container.otp_login_use_case_provider]),
        otp_login_dto: UserBaseDTO
):
    """
    Initiate OTP login by sending verification code to phone number.
    """
    try:
        response = await otp_login_use_case.execute_phone_otp(phone_number=otp_login_dto.phone_number)
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
@router.post("/otp/send", status_code=status.HTTP_200_OK)
@inject
async def send_otp(
        *,
        otp_login_use_case: OTPLoginUseCase = Depends(Provide[Container.otp_login_use_case_provider]),
        otp_request: OTPRequestDTO
):
    """
    Send OTP to email or phone number.
    Auto-detects if identifier is email or phone.
    """
    try:
        response = await otp_login_use_case.execute(identifier=otp_request.identifier)
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
@router.post("/otp/send/email", status_code=status.HTTP_200_OK)
@inject
async def send_email_otp(
        *,
        otp_login_use_case: OTPLoginUseCase = Depends(Provide[Container.otp_login_use_case_provider]),
        email: EmailStr
):
    """
    Send OTP specifically to email address.
    """
    try:
        response = await otp_login_use_case.execute_email_otp(email=email)
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
@router.post("/otp/send/phone", status_code=status.HTTP_200_OK)
@inject
async def send_phone_otp(
        *,
        otp_login_use_case: OTPLoginUseCase = Depends(Provide[Container.otp_login_use_case_provider]),
        phone_number: str
):
    """
    Send OTP specifically to phone number.
    """
    try:
        response = await otp_login_use_case.execute_phone_otp(phone_number=phone_number)
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
@router.post("/otp/verify", response_model=AccessTokenDTO, status_code=status.HTTP_200_OK)
@inject
async def verify_otp(
        *,
        submit_code_use_case: SubmitVerificationCodeUseCase = Depends(
            Provide[Container.submit_verification_code_use_case_provider]
        ),
        otp_verification: OTPVerificationDTO
):
    """
    Verify OTP for email or phone and get access tokens.
    Auto-detects if identifier is email or phone.
    """
    try:
        response = await submit_code_use_case.execute(
            identifier=otp_verification.identifier,
            code=otp_verification.code
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
@router.post("/register", response_model=UserBaseDTO, status_code=status.HTTP_201_CREATED)
@inject
async def register_user(
        *,
        register_user_use_case: RegisterUserUseCase = Depends(
            Provide[Container.register_user_use_case_provider]
        ),
        register_user_dto: RegisterUserDTO
):
    """
    Register a new user account.
    """
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
    """
    Submit verification code for phone number verification and login.
    """
    try:
        response = await submit_code_use_case.execute_phone_verification(
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
    """
    Resend verification code to phone number.
    """
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
    """
    Refresh access token using refresh token.
    """
    try:
        access_token = await refresh.execute(refresh_token=refresh_token_dto.refresh_token)
        return access_token
    except ExpRefreshToken as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except UserNotFound as user_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(user_not_found))
    except InvalidRefreshToken as invalid_refresh:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(invalid_refresh))


# ----------------------------------------------------------------------------
@router.post("/email/verify", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def verify_user_email(
        *,
        confirm_email_use_case: ConfirmEmailUseCase = Depends(
            Provide[Container.confirm_email_use_case_provider]
        ),
        email_dto: EmailVerificationDTO
):
    """
    Send email verification code to user for email confirmation.
    """
    try:
        response = await confirm_email_use_case.execute(email=email_dto.email)
        return AdminActionResponseDTO(
            success=True,
            message="Email verification code sent successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ----------------------------------------------------------------------------
@router.post("/phone/verify", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def verify_user_phone(
        *,
        confirm_phone_use_case: ConfirmPhoneUseCase = Depends(
            Provide[Container.confirm_phone_use_case_provider]
        ),
        phone_dto: PhoneVerificationDTO
):
    """
    Send phone verification code to user for phone confirmation.
    """
    try:
        response = await confirm_phone_use_case.execute(phone_number=phone_dto.phone_number)
        return AdminActionResponseDTO(
            success=True,
            message="Phone verification code sent successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ----------------------------------------------------------------------------
@router.post("/phone/confirm", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def confirm_phone_verification(
        *,
        submit_phone_verification_use_case: SubmitPhoneVerificationUseCase = Depends(
            Provide[Container.submit_phone_verification_use_case_provider]
        ),
        phone_dto: SubmitPhoneVerificationDTO
):
    """
    Confirm phone number with verification code.
    """
    try:
        response = await submit_phone_verification_use_case.execute(
            phone_number=phone_dto.phone_number,
            code=phone_dto.code
        )
        return AdminActionResponseDTO(
            success=True,
            message="Phone number verified successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExpired as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IncorrectVerificationCode as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
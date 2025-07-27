# src/presentation/rest/auth/router.py
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from src.application.dtos.access_token_dto import AccessTokenDTO
from src.application.dtos.refresh_token_dto import RefreshTokenDTO, RefreshTokenOutDTO
from src.application.dtos.user_dto import (
    RegisterUserDTO,
    UserBaseDTO,
    EmailOTPRequestDTO,
    EmailOTPVerifyDTO,
    LoginDTO
)
from src.application.dtos.admin_dtos import (
    AdminActionResponseDTO,
    EmailVerificationSubmitDTO
)
from src.application.dtos.forgot_password_dto import (
    ForgotPasswordRequestDTO,
    ForgotPasswordVerifyDTO,
    ResetPasswordDTO,
    ForgotPasswordResponseDTO
)
from src.application.use_cases.login_with_password_use_case import LoginWithPasswordUseCase
from src.application.use_cases.otp_login_use_case import OTPLoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.resend_code_use_case import ResendCodeUseCase
from src.application.use_cases.submit_verification_code_use_case import (
    SubmitVerificationCodeUseCase,
)
from src.application.use_cases.forgot_password_use_cases import (
    ForgotPasswordSendCodeUseCase,
    ForgotPasswordVerifyCodeUseCase,
    ResetPasswordUseCase,
    ResendPasswordResetCodeUseCase
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
# METHOD 1: EMAIL + PASSWORD LOGIN (Traditional Authentication)
# ============================================================================

@router.post("/login/password", status_code=status.HTTP_200_OK, response_model=AccessTokenDTO)
@inject
async def login_with_email_and_password(
        *,
        login_password_use_case: LoginWithPasswordUseCase = Depends(
            Provide[Container.login_with_password_use_case_provider]
        ),
        login_data: LoginDTO
):
    """
    METHOD 1: Traditional login with email and password.

    🔑 TRADITIONAL LOGIN: User provides email + password for immediate authentication.
    Returns tokens directly if credentials are valid.

    Request body:
    {
        "email": "user@example.com",
        "password": "mypassword"
    }

    Response:
    {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "token_type": "bearer",
        "role": "user"
    }
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


@router.post("/login", status_code=status.HTTP_200_OK, response_model=AccessTokenDTO)
@inject
async def oauth2_login(
        *,
        login_password_use_case: LoginWithPasswordUseCase = Depends(
            Provide[Container.login_with_password_use_case_provider]
        ),
        form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible login endpoint (username field = email).
    Same as /login/password but uses OAuth2PasswordRequestForm for Swagger UI compatibility.

    Form data:
    - username: user@example.com (email address)
    - password: mypassword

    Response:
    {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "token_type": "bearer",
        "role": "user"
    }
    """
    try:
        # Add validation for required fields
        if not form_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username (email) is required"
            )
        if not form_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )

        # Validate email format
        try:
            from pydantic import EmailStr, ValidationError
            from pydantic import BaseModel

            class EmailValidator(BaseModel):
                email: EmailStr

            # Validate email format
            EmailValidator(email=form_data.username)
        except ValidationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        # Debug log (remove in production)
        print(f"🔍 OAuth2 Login attempt - Username: {form_data.username}")

        response = await login_password_use_case.execute(
            email=form_data.username,  # username field contains email
            password=form_data.password
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
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ OAuth2 Login error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )


# ============================================================================
# METHOD 2: EMAIL + OTP LOGIN (Passwordless Authentication)
# ============================================================================

@router.post("/login/otp/send", status_code=status.HTTP_200_OK)
@inject
async def send_login_otp(
        *,
        otp_login_use_case: OTPLoginUseCase = Depends(Provide[Container.otp_login_use_case_provider]),
        request: EmailOTPRequestDTO
):
    """
    METHOD 2 - Step 1: Send OTP to email for passwordless login.

    🔐 PASSWORDLESS LOGIN: User only provides email, NO PASSWORD needed!
    System sends OTP code to the email address for verification.

    Request body:
    {
        "email": "user@example.com"
    }

    Response:
    {
        "success": true,
        "message": "OTP sent to email user@example.com",
        "method": "email",
        "email": "user@example.com"
    }
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


@router.post("/login/otp/verify", response_model=AccessTokenDTO, status_code=status.HTTP_200_OK)
@inject
async def verify_login_otp(
        *,
        submit_code_use_case: SubmitVerificationCodeUseCase = Depends(
            Provide[Container.submit_verification_code_use_case_provider]
        ),
        otp_data: EmailOTPVerifyDTO
):
    """
    METHOD 2 - Step 2: Verify OTP and get authentication tokens.

    🔐 PASSWORDLESS LOGIN: User only provides email + OTP code.
    NO PASSWORD needed! The OTP code serves as the authentication credential.
    Returns authentication tokens if OTP is valid.

    Request body:
    {
        "email": "user@example.com",
        "code": "1234"
    }

    Response:
    {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "token_type": "bearer",
        "role": "user"
    }
    """
    try:
        response = await submit_code_use_case.execute_login_otp_verification(
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


@router.post("/login/otp/resend", status_code=status.HTTP_200_OK)
@inject
async def resend_login_otp(
        *,
        resend_code_use_case: ResendCodeUseCase = Depends(
            Provide[Container.resend_code_use_case_provider]
        ),
        request: EmailOTPRequestDTO
):
    """
    METHOD 2 - Helper: Resend OTP for passwordless login.

    🔐 PASSWORDLESS LOGIN: Only email needed, NO PASSWORD required!
    Resends OTP if user didn't receive the first one.

    Request body:
    {
        "email": "user@example.com"
    }

    Response:
    {
        "success": true,
        "message": "OTP resent to email user@example.com",
        "method": "email",
        "email": "user@example.com"
    }
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
# FORGOT PASSWORD / PASSWORD RESET
# ============================================================================

@router.post("/forgot-password/send", status_code=status.HTTP_200_OK, response_model=ForgotPasswordResponseDTO)
@inject
async def send_password_reset_code(
        *,
        forgot_password_send_code_use_case: ForgotPasswordSendCodeUseCase = Depends(
            Provide[Container.forgot_password_send_code_use_case_provider]
        ),
        request: ForgotPasswordRequestDTO
):
    """
    Send password reset code to user's email.

    🔐 FORGOT PASSWORD - Step 1: Send reset code to email.
    User only needs to provide their email address.

    Request body:
    {
        "email": "user@example.com"
    }

    Response:
    {
        "success": true,
        "message": "Password reset code sent to user@example.com",
        "email": "user@example.com"
    }
    """
    try:
        response = await forgot_password_send_code_use_case.execute(email=request.email)
        return ForgotPasswordResponseDTO(**response)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UserIsLocked as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/forgot-password/verify", status_code=status.HTTP_200_OK, response_model=ForgotPasswordResponseDTO)
@inject
async def verify_password_reset_code(
        *,
        forgot_password_verify_code_use_case: ForgotPasswordVerifyCodeUseCase = Depends(
            Provide[Container.forgot_password_verify_code_use_case_provider]
        ),
        request: ForgotPasswordVerifyDTO
):
    """
    Verify password reset code (optional step).

    🔐 FORGOT PASSWORD - Step 2 (Optional): Verify reset code before password reset.
    This step is optional - you can go directly to reset-password endpoint.

    Request body:
    {
        "email": "user@example.com",
        "code": "1234"
    }

    Response:
    {
        "success": true,
        "message": "Password reset code verified successfully",
        "email": "user@example.com"
    }
    """
    try:
        response = await forgot_password_verify_code_use_case.execute(
            email=request.email,
            code=request.code
        )
        return ForgotPasswordResponseDTO(**response)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExpired as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IncorrectVerificationCode as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/forgot-password/reset", status_code=status.HTTP_200_OK, response_model=ForgotPasswordResponseDTO)
@inject
async def reset_password(
        *,
        reset_password_use_case: ResetPasswordUseCase = Depends(
            Provide[Container.reset_password_use_case_provider]
        ),
        request: ResetPasswordDTO
):
    """
    Reset password with verification code.

    🔐 FORGOT PASSWORD - Step 3: Reset password using the code.
    User provides the reset code and new password.

    Request body:
    {
        "email": "user@example.com",
        "code": "1234",
        "new_password": "mynewpassword",
        "confirm_password": "mynewpassword"
    }

    Response:
    {
        "success": true,
        "message": "Password reset successfully. You can now login with your new password.",
        "email": "user@example.com"
    }
    """
    try:
        # Validate password match
        if not request.passwords_match():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        response = await reset_password_use_case.execute(
            email=request.email,
            code=request.code,
            new_password=request.new_password,
            confirm_password=request.confirm_password
        )
        return ForgotPasswordResponseDTO(**response)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExpired as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IncorrectVerificationCode as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/forgot-password/resend", status_code=status.HTTP_200_OK, response_model=ForgotPasswordResponseDTO)
@inject
async def resend_password_reset_code(
        *,
        resend_password_reset_code_use_case: ResendPasswordResetCodeUseCase = Depends(
            Provide[Container.resend_password_reset_code_use_case_provider]
        ),
        request: ForgotPasswordRequestDTO
):
    """
    Resend password reset code to user's email.

    🔐 FORGOT PASSWORD - Helper: Resend reset code if user didn't receive it.

    Request body:
    {
        "email": "user@example.com"
    }

    Response:
    {
        "success": true,
        "message": "Password reset code resent to user@example.com",
        "email": "user@example.com"
    }
    """
    try:
        response = await resend_password_reset_code_use_case.execute(email=request.email)
        return ForgotPasswordResponseDTO(**response)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


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
    Email verification code will be sent automatically after registration.
    User must verify email before they can login.

    Request body:
    {
        "email": "user@example.com",
        "name": "John",
        "family": "Doe",
        "position": "Developer",
        "personal_code": "EMP001",
        "password": "securepassword",
        "confirm_password": "securepassword",
        "phone_number": "+1234567890"  // Optional
    }

    Response:
    {
        "email": "user@example.com"
    }
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
# EMAIL VERIFICATION (FOR REGISTRATION)
# ============================================================================

@router.post("/register/verify-email", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def verify_email_for_registration(
        *,
        submit_code_use_case: SubmitVerificationCodeUseCase = Depends(
            Provide[Container.submit_verification_code_use_case_provider]
        ),
        verification_data: EmailVerificationSubmitDTO
):
    """
    Verify email address with verification code (for registration completion).

    This activates the user account after registration.
    Different from login OTP - this is a one-time account activation.

    Request body:
    {
        "email": "user@example.com",
        "code": "1234"
    }

    Response:
    {
        "success": true,
        "message": "Email address verified successfully. Account activated."
    }
    """
    try:
        response = await submit_code_use_case.execute_registration_verification(
            email=verification_data.email,
            code=verification_data.code
        )
        return AdminActionResponseDTO(
            success=True,
            message="Email address verified successfully. Account activated."
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExpired as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IncorrectVerificationCode as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/register/resend-verification", status_code=status.HTTP_200_OK)
@inject
async def resend_email_verification(
        *,
        resend_code_use_case: ResendCodeUseCase = Depends(
            Provide[Container.resend_code_use_case_provider]
        ),
        request: EmailOTPRequestDTO
):
    """
    Resend email verification code (for registration completion).

    If user didn't receive the verification email after registration,
    they can request a new verification code.

    Request body:
    {
        "email": "user@example.com"
    }

    Response:
    {
        "success": true,
        "message": "Verification code resent to email user@example.com",
        "method": "email",
        "email": "user@example.com"
    }
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

    When access token expires, use this endpoint to get a new one
    without requiring the user to login again.

    Request body:
    {
        "refresh_token": "eyJ..."
    }

    Response:
    {
        "access_token": "eyJ...",
        "token_type": "bearer",
        "role": "user"
    }
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
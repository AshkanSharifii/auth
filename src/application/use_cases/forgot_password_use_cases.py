from src.application.utils.security import generate_verification_code, hash_password
from src.domain.exceptions import (
    NotifyUserError,
    UserNotFound,
    VerificationCodeExist,
    VerificationCodeExpired,
    IncorrectVerificationCode,
    UserIsLocked
)
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class ForgotPasswordSendCodeUseCase:
    """
    Use case for sending password reset code to user's email.
    """

    def __init__(
            self,
            user_repo: IUserRepository,
            cache_client: ICacheClient,
            notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._cache_client = cache_client
        self._notify_user = notify_user

    async def execute(self, email: str) -> dict:
        """
        Send password reset code to user's email.

        Args:
            email (str): The user's email address.

        Returns:
            dict: Success response with details.

        Raises:
            UserNotFound: If no user found with the email.
            UserIsLocked: If user account is locked.
            VerificationCodeExist: If a reset code already exists.
            NotifyUserError: If email sending fails.
        """
        try:
            # Check if user exists
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

            # Check if user is locked
            if user.is_locked:
                raise UserIsLocked("User account is temporarily locked")

            # Check if reset code already exists
            cache_key = f"password_reset_{email}"
            code_exists = await self._cache_client.retrieve_code(key=cache_key)
            if code_exists:
                raise VerificationCodeExist("Password reset code already sent. Please check your email or wait before requesting a new one.")

            # Generate reset code
            code = generate_verification_code()

            # Send reset code via email
            response = await self._notify_user.send_password_reset_email(
                email=email,
                otp=code,
                user_name=f"{user.name} {user.family}"
            )

            if response.status_code == 200:
                # Store reset code in cache (valid for 15 minutes)
                await self._cache_client.store_code(key=cache_key, value=code)
                return {
                    "success": True,
                    "message": f"Password reset code sent to {email}",
                    "email": email
                }
            else:
                raise NotifyUserError("Failed to send password reset email")

        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class ForgotPasswordVerifyCodeUseCase:
    """
    Use case for verifying password reset code (without actually resetting password).
    """

    def __init__(
            self,
            user_repo: IUserRepository,
            cache_client: ICacheClient
    ):
        self._user_repo = user_repo
        self._cache_client = cache_client

    async def execute(self, email: str, code: str) -> dict:
        """
        Verify password reset code.

        Args:
            email (str): The user's email address.
            code (str): The reset code.

        Returns:
            dict: Success response if code is valid.

        Raises:
            UserNotFound: If user not found.
            VerificationCodeExpired: If code expired.
            IncorrectVerificationCode: If code is wrong.
        """
        try:
            # Check if user exists
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound("User not found")

            # Get reset code from cache
            cache_key = f"password_reset_{email}"
            reset_code = await self._cache_client.retrieve_code(key=cache_key)
            if not reset_code:
                raise VerificationCodeExpired("Password reset code has expired")

            if code != reset_code:
                raise IncorrectVerificationCode("Invalid password reset code")

            return {
                "success": True,
                "message": "Password reset code verified successfully",
                "email": email
            }

        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class ResetPasswordUseCase:
    """
    Use case for resetting user password with verification code.
    """

    def __init__(
            self,
            user_repo: IUserRepository,
            cache_client: ICacheClient
    ):
        self._user_repo = user_repo
        self._cache_client = cache_client

    async def execute(
            self,
            email: str,
            code: str,
            new_password: str,
            confirm_password: str
    ) -> dict:
        """
        Reset user password with verification code.

        Args:
            email (str): The user's email address.
            code (str): The reset code.
            new_password (str): The new password.
            confirm_password (str): Password confirmation.

        Returns:
            dict: Success response if password reset successful.

        Raises:
            UserNotFound: If user not found.
            VerificationCodeExpired: If code expired.
            IncorrectVerificationCode: If code is wrong.
            ValueError: If passwords don't match.
        """
        try:
            # Validate password confirmation
            if new_password != confirm_password:
                raise ValueError("Passwords do not match")

            # Check if user exists
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound("User not found")

            # Get and verify reset code from cache
            cache_key = f"password_reset_{email}"
            reset_code = await self._cache_client.retrieve_code(key=cache_key)
            if not reset_code:
                raise VerificationCodeExpired("Password reset code has expired")

            if code != reset_code:
                raise IncorrectVerificationCode("Invalid password reset code")

            # Hash new password
            hashed_password = hash_password(new_password)

            # Update user password and clear any locks
            await self._user_repo.update(
                user_id=user.id,
                user_new_data={
                    "hashed_password": hashed_password,
                    "is_locked": False,
                    "lock_expire_time": None,
                    "login_retries": False,
                }
            )

            # Remove reset code from cache
            await self._cache_client.delete_code(key=cache_key)

            return {
                "success": True,
                "message": "Password reset successfully. You can now login with your new password.",
                "email": email
            }

        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class ResendPasswordResetCodeUseCase:
    """
    Use case for resending password reset code.
    """

    def __init__(
            self,
            user_repo: IUserRepository,
            cache_client: ICacheClient,
            notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._cache_client = cache_client
        self._notify_user = notify_user

    async def execute(self, email: str) -> dict:
        """
        Resend password reset code to user's email.

        Args:
            email (str): The user's email address.

        Returns:
            dict: Success response with details.

        Raises:
            UserNotFound: If no user found with the email.
            VerificationCodeExist: If a reset code already exists.
            NotifyUserError: If email sending fails.
        """
        try:
            # Check if user exists
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

            # Check if reset code already exists
            cache_key = f"password_reset_{email}"
            code_exists = await self._cache_client.retrieve_code(key=cache_key)
            if code_exists:
                raise VerificationCodeExist(
                    "Password reset code already exists. Please wait before requesting a new one.")

            # Generate new reset code
            code = generate_verification_code()

            # Send reset code via email
            response = await self._notify_user.send_password_reset_email(
                email=email,
                otp=code,
                user_name=f"{user.name} {user.family}"
            )

            if response.status_code == 200:
                # Store reset code in cache
                await self._cache_client.store_code(key=cache_key, value=code)
                return {
                    "success": True,
                    "message": f"Password reset code resent to {email}",
                    "email": email
                }
            else:
                raise NotifyUserError("Failed to resend password reset email")

        except Exception as e:
            raise e
from datetime import datetime
from typing import Optional

from src.application.utils.security import validate_user
from src.domain.exceptions import (
    IncorrectVerificationCode,
    UserIsLocked,
    UserNotFound,
    VerificationCodeExpired,
)
from src.domain.interfaces.access_token import IAccessToken
from src.domain.interfaces.cache_client import ICacheClient
from src.ports.repositories.role_repo import IRoleRepository
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class SubmitVerificationCodeUseCase:
    """
    Use case for submitting email OTP verification codes.

    Supports multiple verification scenarios:
    1. Email OTP login verification
    2. Email registration verification
    3. Legacy compatibility methods
    """

    def __init__(
            self,
            user_repo: IUserRepository,
            access_token: IAccessToken,
            role_repo: IRoleRepository,
            cache_client: ICacheClient,
    ):
        self._user_repo = user_repo
        self._access_token = access_token
        self._role_repo = role_repo
        self._cache_client = cache_client

    async def execute(self, email: str, code: str) -> Optional[dict]:
        """
        Primary method: Verify email OTP and return authentication tokens.

        Args:
            email (str): The email address where OTP was sent.
            code (str): The verification code received.

        Returns:
            Optional[dict]: Authentication tokens and user info if successful.
        """
        return await self.execute_email_verification(email=email, code=code)

    async def execute_email_verification(self, email: str, code: str) -> Optional[dict]:
        """
        Verify email OTP and return authentication tokens.

        Args:
            email (str): The email address where OTP was sent.
            code (str): The verification code received.

        Returns:
            Optional[dict]: Authentication tokens and user info if successful.

        Raises:
            UserNotFound: If user not found.
            UserIsLocked: If user account is locked.
            VerificationCodeExpired: If OTP has expired.
            IncorrectVerificationCode: If OTP is incorrect.
        """
        try:
            user = await self._user_repo.get_by_email(email)
            if not user:
                raise UserNotFound("User not found")

            # Check if user is locked
            if user.is_locked:
                if user.lock_expire_time and user.lock_expire_time > datetime.now():
                    raise UserIsLocked("User account is temporarily locked")
                else:
                    # Unlock expired lock
                    await self._user_repo.update(
                        user_id=user.id,
                        user_new_data={
                            "is_locked": False,
                            "lock_expire_time": None,
                            "login_retries": False,
                        },
                    )

            # Find verification code
            cache_key = f"email_otp_{email}"
            verification_code = await self._cache_client.retrieve_code(key=cache_key)
            if not verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise VerificationCodeExpired("Verification code has expired")

            if code != verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise IncorrectVerificationCode("Incorrect verification code")

            # Generate authentication tokens
            payload = {"sub": str(user.id)}
            access_token = self._access_token.create_access_token(data=payload)
            refresh_token = self._access_token.create_access_token(data=payload, refresh_type=True)
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)

            # Update user status
            await self._user_repo.update(
                user_id=user.id,
                user_new_data={
                    "is_locked": False,
                    "lock_expire_time": None,
                    "login_retries": False,
                    "latest_login": datetime.now(),
                    "is_verified": True,
                    "email_verified": True,
                },
            )

            # Clear OTP from cache
            await self._cache_client.delete_code(key=cache_key)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "role": role.role_name,
                "token_type": "bearer",
                "login_method": "email_otp"
            }
        except Exception as e:
            raise e

    async def execute_registration_verification(self, email: str, code: str) -> bool:
        """
        Verify email for registration (without returning tokens).

        Args:
            email (str): The email address to verify.
            code (str): The verification code.

        Returns:
            bool: True if verification successful.
        """
        try:
            user = await self._user_repo.get_by_email(email)
            if not user:
                raise UserNotFound("User not found")

            # Find registration verification code
            cache_key = f"email_verification_{email}"
            verification_code = await self._cache_client.retrieve_code(key=cache_key)
            if not verification_code:
                raise VerificationCodeExpired("Verification code has expired")

            if code != verification_code:
                raise IncorrectVerificationCode("Incorrect verification code")

            # Update user email verification status
            await self._user_repo.update(
                user_id=user.id,
                user_new_data={
                    "email_verified": True,
                    "is_verified": True,
                    "is_active": True
                }
            )

            # Clear verification code from cache
            await self._cache_client.delete_code(key=cache_key)
            return True
        except Exception as e:
            raise e

    async def execute_login_otp_verification(self, email: str, code: str) -> Optional[dict]:
        """
        Verify OTP specifically for login flow.

        Args:
            email (str): The email address.
            code (str): The verification code.

        Returns:
            Optional[dict]: Authentication tokens if successful.
        """
        try:
            user = await self._user_repo.get_by_email(email)
            if not user:
                raise UserNotFound("User not found")

            # Check if user is locked
            if user.is_locked:
                if user.lock_expire_time and user.lock_expire_time > datetime.now():
                    raise UserIsLocked("User account is temporarily locked")
                else:
                    await self._user_repo.update(
                        user_id=user.id,
                        user_new_data={
                            "is_locked": False,
                            "lock_expire_time": None,
                            "login_retries": False,
                        },
                    )

            # Find login OTP code
            cache_key = f"login_otp_{email}"
            verification_code = await self._cache_client.retrieve_code(key=cache_key)
            if not verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise VerificationCodeExpired("OTP has expired")

            if code != verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise IncorrectVerificationCode("Incorrect OTP")

            # Generate authentication tokens
            payload = {"sub": str(user.id)}
            access_token = self._access_token.create_access_token(data=payload)
            refresh_token = self._access_token.create_access_token(data=payload, refresh_type=True)
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)

            # Update user status
            await self._user_repo.update(
                user_id=user.id,
                user_new_data={
                    "is_locked": False,
                    "lock_expire_time": None,
                    "login_retries": False,
                    "latest_login": datetime.now(),
                },
            )

            # Clear OTP from cache
            await self._cache_client.delete_code(key=cache_key)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "role": role.role_name,
                "token_type": "bearer",
                "login_method": "email_otp"
            }
        except Exception as e:
            raise e

    # Legacy compatibility methods
    async def execute_legacy(self, email: str, code: str) -> Optional[dict]:
        """
        LEGACY: For backward compatibility.
        Use execute() instead.
        """
        return await self.execute(email=email, code=code)
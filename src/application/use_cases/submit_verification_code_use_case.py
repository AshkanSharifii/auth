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
    UPDATED: Use case for submitting verification code for both phone and email OTP login.
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

    async def execute_phone_verification(self, phone_number: str, code: str) -> Optional[dict]:
        """
        Verify OTP for phone number login.
        """
        try:
            user = await self._user_repo.get_by_phone_number(phone_number)
            if not user:
                raise UserNotFound("User not found")

            # Check if user is locked
            if user.is_locked:
                if user.lock_expire_time > datetime.now():
                    raise UserIsLocked("User is locked")
                else:
                    await self._user_repo.update(
                        user_id=user.id,
                        user_new_data={
                            "is_locked": False,
                            "lock_expire_time": None,
                            "login_retries": False,
                        },
                    )

            # Find verification code with phone-specific key
            cache_key = f"otp_phone_{phone_number}"
            verification_code = await self._cache_client.retrieve_code(key=cache_key)
            if not verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise VerificationCodeExpired("Verification code expired")

            if code != verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise IncorrectVerificationCode("Incorrect verification code")

            # Generate tokens
            payload = {"sub": str(user.id)}
            access_token = self._access_token.create_access_token(data=payload)
            refresh_token = self._access_token.create_access_token(data=payload, refresh_type=True)
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)

            await self._user_repo.update(
                user_id=user.id,
                user_new_data={
                    "is_locked": False,
                    "lock_expire_time": None,
                    "login_retries": False,
                    "latest_login": datetime.now(),
                    "is_verified": True,
                    "phone_number_verified": True,
                },
            )

            # Clear OTP from cache
            await self._cache_client.delete_code(key=cache_key)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "role": role.role_name,
                "token_type": "bearer",
                "login_method": "phone_otp"
            }
        except Exception as e:
            raise e

    async def execute_email_verification(self, email: str, code: str) -> Optional[dict]:
        """
        Verify OTP for email login.
        """
        try:
            user = await self._user_repo.get_by_email(email)
            if not user:
                raise UserNotFound("User not found")

            # Check if user is locked
            if user.is_locked:
                if user.lock_expire_time > datetime.now():
                    raise UserIsLocked("User is locked")
                else:
                    await self._user_repo.update(
                        user_id=user.id,
                        user_new_data={
                            "is_locked": False,
                            "lock_expire_time": None,
                            "login_retries": False,
                        },
                    )

            # Find verification code with email-specific key
            cache_key = f"otp_email_{email}"
            verification_code = await self._cache_client.retrieve_code(key=cache_key)
            if not verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise VerificationCodeExpired("Verification code expired")

            if code != verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise IncorrectVerificationCode("Incorrect verification code")

            # Generate tokens
            payload = {"sub": str(user.id)}
            access_token = self._access_token.create_access_token(data=payload)
            refresh_token = self._access_token.create_access_token(data=payload, refresh_type=True)
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)

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

    async def execute(self, identifier: str, code: str) -> Optional[dict]:
        """
        UPDATED: Auto-detect identifier type and verify appropriate OTP.
        """
        try:
            # Auto-detect if identifier is email or phone
            if "@" in identifier:
                return await self.execute_email_verification(email=identifier, code=code)
            elif identifier.startswith("+") or identifier.replace("-", "").replace(" ", "").isdigit():
                return await self.execute_phone_verification(phone_number=identifier, code=code)
            else:
                raise UserNotFound(f"Invalid identifier format: {identifier}")
        except Exception as e:
            raise e

    # Keep legacy method for backward compatibility
    async def execute_legacy(self, phone_number: str, code: str) -> Optional[dict]:
        """
        Legacy method for backward compatibility with existing phone verification.
        """
        return await self.execute_phone_verification(phone_number, code)
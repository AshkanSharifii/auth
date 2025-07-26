from datetime import datetime
from typing import Dict, Optional

from src.application.utils.security import validate_user, verify_password, generate_verification_code
from src.domain.exceptions import (
    CredentialError,
    NotVerifiedUser,
    UserIsLocked,
    UserNotFound,
    VerificationCodeExist,
    NotifyUserError
)
from src.domain.interfaces.access_token import IAccessToken
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.role_repo import IRoleRepository
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class LoginWithPasswordUseCase:
    """
    UPDATED: Use case for logging in a user with flexible options:
    1. Identifier + Password = Direct login
    2. Identifier only = Send OTP
    """

    def __init__(
            self,
            user_repo: IUserRepository,
            access_token: IAccessToken,
            role_repo: IRoleRepository,
            cache_client: ICacheClient,
            notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._access_token = access_token
        self._role_repo = role_repo
        self._cache_client = cache_client
        self._notify_user = notify_user

    async def execute(
            self,
            identifier: str,
            password: Optional[str] = None,
            send_otp: bool = False
    ) -> dict[str, str]:
        """
        UPDATED: Flexible authentication that handles:
        1. Password login (when password provided)
        2. OTP login (when send_otp=True or no password)

        Args:
            identifier (str): The user's phone number, email, or personal code.
            password (Optional[str]): The user's password (optional).
            send_otp (bool): Whether to send OTP instead of password login.

        Returns:
            dict[str, str]: Login result with tokens or OTP sent confirmation.
        """
        try:
            user = None

            # Try to find user by different identifiers
            if "@" in identifier:
                user = await self._user_repo.get_by_email(email=identifier)
            elif identifier.startswith("+") or identifier.replace("-", "").isdigit():
                user = await self._user_repo.get_by_phone_number(phone_number=identifier)
            else:
                user = await self._user_repo.get_by_personal_code(personal_code=identifier)

            if not user:
                raise UserNotFound(f"User with identifier {identifier} not found")

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

            if not user.is_verified or not user.is_active:
                raise NotVerifiedUser("User is not verified or active")

            # OPTION 1: Password Login (when password provided and send_otp=False)
            if password and not send_otp:
                if not verify_password(plain_password=password, hashed_password=user.hashed_password):
                    await validate_user(user=user, user_repo=self._user_repo)
                    raise CredentialError("Identifier or password is incorrect")

                # Generate tokens for successful password login
                access_token = self._access_token.create_access_token(data={"sub": str(user.id)})
                refresh_token = self._access_token.create_access_token(
                    data={"sub": str(user.id)}, refresh_type=True
                )
                role = await self._role_repo.get_role_by_id(role_id=user.role_id)

                await self._user_repo.update(
                    user_id=user.id,
                    user_new_data={
                        "is_locked": False,
                        "lock_expire_time": None,
                        "login_retries": False,
                        "latest_login": datetime.now(),
                    },
                )

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "role": role.role_name,
                    "token_type": "bearer",
                    "login_method": "password",
                    "message": "Login successful"
                }

            # OPTION 2: OTP Login (when no password or send_otp=True)
            else:
                # Check if verification code already exists
                cache_key = f"login_otp_{identifier}"
                code_exists = await self._cache_client.retrieve_code(key=cache_key)
                if code_exists:
                    raise VerificationCodeExist("OTP already sent. Please wait before requesting a new one.")

                # Generate verification code
                code = generate_verification_code()

                # Determine where to send OTP
                if "@" in identifier:
                    # Email - use phone for now since we use SMS service
                    response = await self._notify_user.send_request(
                        phone_number=user.phone_number,
                        otp=code
                    )
                    message = f"OTP sent to email {identifier}"
                else:
                    # Phone number
                    response = await self._notify_user.send_request(
                        phone_number=identifier,
                        otp=code
                    )
                    message = f"OTP sent to phone {identifier}"

                if response.status_code == 200:
                    # Store OTP in cache
                    await self._cache_client.store_code(key=cache_key, value=code)
                    return {
                        "login_method": "otp_sent",
                        "message": message,
                        "identifier": identifier
                    }
                else:
                    raise NotifyUserError("Failed to send OTP")

        except Exception as e:
            raise e

    async def verify_login_otp(
            self,
            identifier: str,
            otp: str
    ) -> dict[str, str]:
        """
        NEW METHOD: Verify OTP for login and return tokens
        """
        try:
            # Find user
            user = None
            if "@" in identifier:
                user = await self._user_repo.get_by_email(email=identifier)
            elif identifier.startswith("+") or identifier.replace("-", "").isdigit():
                user = await self._user_repo.get_by_phone_number(phone_number=identifier)
            else:
                user = await self._user_repo.get_by_personal_code(personal_code=identifier)

            if not user:
                raise UserNotFound("User not found")

            # Check cached OTP
            cache_key = f"login_otp_{identifier}"
            cached_otp = await self._cache_client.retrieve_code(key=cache_key)

            if not cached_otp:
                raise CredentialError("OTP expired or not found")

            if cached_otp != otp:
                raise CredentialError("Invalid OTP")

            # Generate tokens
            access_token = self._access_token.create_access_token(data={"sub": str(user.id)})
            refresh_token = self._access_token.create_access_token(
                data={"sub": str(user.id)}, refresh_type=True
            )
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)

            # Update user login info
            await self._user_repo.update(
                user_id=user.id,
                user_new_data={
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
                "login_method": "otp",
                "message": "Login successful"
            }

        except Exception as e:
            raise e
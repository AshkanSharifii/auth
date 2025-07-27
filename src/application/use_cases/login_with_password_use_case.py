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
    Use case for user authentication with multiple options:
    1. Email + Password login (direct authentication)
    2. Email + OTP login (send OTP, then verify)

    Supports flexible authentication while maintaining email-only OTP delivery.
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

    async def execute(self, email: str, password: str) -> dict[str, str]:
        """
        Authenticate user with email and password.

        Args:
            email (str): The user's email address.
            password (str): The user's password.

        Returns:
            dict[str, str]: Authentication tokens and user info.

        Raises:
            UserNotFound: If user doesn't exist.
            NotVerifiedUser: If user account is not verified or active.
            UserIsLocked: If user account is locked.
            CredentialError: If email/password combination is invalid.
        """
        try:
            # Find user by email
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

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

            # Check if user is verified and active
            if not user.is_verified or not user.is_active:
                raise NotVerifiedUser("User account is not verified or active")

            # Verify password
            if not verify_password(plain_password=password, hashed_password=user.hashed_password):
                await validate_user(user=user, user_repo=self._user_repo)
                raise CredentialError("Invalid email or password")

            # Generate authentication tokens
            access_token = self._access_token.create_access_token(data={"sub": str(user.id)})
            refresh_token = self._access_token.create_access_token(
                data={"sub": str(user.id)}, refresh_type=True
            )
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)

            # Update user login info
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

        except Exception as e:
            raise e

    async def execute_flexible(
            self,
            email: str,
            password: Optional[str] = None,
            send_otp: bool = False
    ) -> dict[str, str]:
        """
        Flexible authentication that handles:
        1. Password login (when password provided and send_otp=False)
        2. Email OTP login (when send_otp=True or no password)

        Args:
            email (str): The user's email address.
            password (Optional[str]): The user's password (optional).
            send_otp (bool): Whether to send OTP instead of password login.

        Returns:
            dict[str, str]: Login result with tokens or OTP sent confirmation.
        """
        try:
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

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

            if not user.is_verified or not user.is_active:
                raise NotVerifiedUser("User account is not verified or active")

            # OPTION 1: Password Login
            if password and not send_otp:
                if not verify_password(plain_password=password, hashed_password=user.hashed_password):
                    await validate_user(user=user, user_repo=self._user_repo)
                    raise CredentialError("Invalid email or password")

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

            # OPTION 2: Email OTP Login
            else:
                # Check if verification code already exists
                cache_key = f"login_otp_{email}"
                code_exists = await self._cache_client.retrieve_code(key=cache_key)
                if code_exists:
                    raise VerificationCodeExist("OTP already sent. Please wait before requesting a new one.")

                # Generate verification code
                code = generate_verification_code()

                # Send OTP to user's email
                response = await self._notify_user.send_email_otp(
                    email=email,
                    otp=code
                )

                if response.status_code == 200:
                    # Store OTP in cache
                    await self._cache_client.store_code(key=cache_key, value=code)
                    return {
                        "login_method": "otp_sent",
                        "message": f"OTP sent to email {email}",
                        "email": email
                    }
                else:
                    raise NotifyUserError("Failed to send OTP to email")

        except Exception as e:
            raise e

    async def verify_login_otp(
            self,
            email: str,
            otp: str
    ) -> dict[str, str]:
        """
        Verify OTP for login and return tokens.

        Args:
            email (str): The user's email address.
            otp (str): The OTP code received via email.

        Returns:
            dict[str, str]: Login tokens and user info.
        """
        try:
            # Find user by email
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound("User not found")

            # Check cached OTP
            cache_key = f"login_otp_{email}"
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
                    "is_locked": False,
                    "lock_expire_time": None,
                    "login_retries": False,
                },
            )

            # Clear OTP from cache
            await self._cache_client.delete_code(key=cache_key)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "role": role.role_name,
                "token_type": "bearer",
                "login_method": "email_otp",
                "message": "Login successful"
            }

        except Exception as e:
            raise e
from datetime import datetime
from typing import Optional

from src.domain.exceptions import (UserNotFound,
                                   UserIsLocked,
                                   VerificationCodeExpired,
                                   IncorrectVerificationCode)
from src.application.utils.security import validate_user
from src.domain.interfaces.access_token import IAccessToken
from src.domain.interfaces.cache_client import ICacheClient
from src.ports.repositories.role_repo import IRoleRepository
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class SubmitVerificationCodeUseCase:
    """
    Use case for submitting a verification code during the auth process.

    This class verifies the user's phone number, checks if the account is locked,
    validates the OTP code, and returns an access token upon successful verification.

    Attributes:
        _user_repo (IUserRepository): Interface to interact with the user repository.
        _access_token (IAccessToken): Interface to create access tokens.
        _role_repo (IRoleRepository): Interface to retrieve user roles.
        _cache_client (ICacheClient): Interface to interact with a cache (e.g., Redis) storing OTP codes.
    """

    def __init__(self,
                 user_repo: IUserRepository,
                 access_token: IAccessToken,
                 role_repo: IRoleRepository,
                 cache_client: ICacheClient):
        self._user_repo = user_repo
        self._access_token = access_token
        self._role_repo = role_repo
        self._cache_client = cache_client

    async def execute(self, phone_number: str, code: str) -> Optional[dict]:
        """
        Executes the verification process by validating the code for the given phone number.

        Args:
            phone_number (str): The user's phone number.
            code (str): The verification code submitted by the user.

        Returns:
            Optional[dict]: A dictionary containing the access token, user role, and token type if successful.

        Raises:
            UserNotFound: If the user with the given phone number does not exist.
            UserIsLocked: If the user account is locked.
            VerificationCodeExpired: If the verification code has expired or is missing.
            IncorrectVerificationCode: If the submitted code does not match the stored code.
        """

        try:
            # Check if phone number exists
            user = await self._user_repo.get_by_phone_number(phone_number)
            if not user:
                raise UserNotFound("User not found")

            # Check if user is locked or not
            if user.is_locked:
                if user.lock_expire_time > datetime.now():
                    raise UserIsLocked("User is locked")
                else:
                    await self._user_repo.update_user_login_status(user_id=user.id, login=False)

            # Find verification code of user
            verification_code = await self._cache_client.retrieve_code(key=user.phone_number)
            if not verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise VerificationCodeExpired("Verification code expired")

            if code != verification_code:
                await validate_user(user=user, user_repo=self._user_repo)
                raise IncorrectVerificationCode("Incorrect verification code")

            payload = {"sub": str(user.id)}
            access_token = self._access_token.create_access_token(data=payload)
            refresh_token = self._access_token.create_access_token(data=payload, refresh_type=True)
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)
            await self._user_repo.update_user_login_status(user_id=user.id, login=True)
            return {'access_token': access_token,
                    'refresh_token': refresh_token,
                    'role': role.role_name,
                    'token_type': 'bearer'}
        except Exception as e:
            raise e


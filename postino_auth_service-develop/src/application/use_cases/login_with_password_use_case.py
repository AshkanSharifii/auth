from datetime import datetime

from src.application.utils.security import validate_user, verify_password
from src.domain.exceptions import CredentialError, NotVerifiedUser, UserIsLocked, UserNotFound
from src.domain.interfaces.access_token import IAccessToken
from src.ports.repositories.role_repo import IRoleRepository
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class LoginWithPasswordUseCase:
    """
    Use case for logging in a user using identifier (phone/email/personal_code) and password.

    This class handles the auth process, including:
    - Retrieving the user by phone number, email, or personal code.
    - Verifying the user is not locked or unverified.
    - Validating the user's password.
    - Generating an access token upon successful authentication.
    - Fetching the user's role information.

    Dependencies:
        user_repo (IUserRepository): Interface to access user data.
        access_token (IAccessToken): Interface to generate JWT access tokens.
        role_repo (IRoleRepository): Interface to retrieve user role information.

    Methods:
        execute(identifier: str, password: str) -> dict[str, str]:
            Orchestrates the auth process and returns an access token and role information.
    """

    def __init__(
            self, user_repo: IUserRepository, access_token: IAccessToken, role_repo: IRoleRepository
    ):
        self._user_repo = user_repo
        self._access_token = access_token
        self._role_repo = role_repo

    async def execute(self, identifier: str, password: str) -> dict[str, str]:
        """
        Authenticate the user with the provided identifier and password.

        Args:
            identifier (str): The user's phone number, email, or personal code.
            password (str): The user's plain-text password.

        Returns:
            dict[str, str]: A dictionary containing:
                - 'access_token': The generated JWT access token.
                - 'refresh_token': The generated JWT refresh token.
                - 'role': The user's role name.
                - 'token_type': Token type (always 'bearer').

        Raises:
            UserNotFound: If the user with the provided identifier does not exist.
            UserIsLocked: If the user is currently locked and the lock has not expired.
            NotVerifiedUser: If the user is not verified or active.
            CredentialError: If the provided password is incorrect.
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

            if not verify_password(plain_password=password, hashed_password=user.hashed_password):
                await validate_user(user=user, user_repo=self._user_repo)
                raise CredentialError("Identifier or password is incorrect")

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
            }
        except Exception as e:
            raise e
import uuid
from datetime import datetime

from jwt.exceptions import ExpiredSignatureError

from src.domain.exceptions import ExpRefreshToken, InvalidRefreshToken, UserNotFound
from src.domain.interfaces.access_token import IAccessToken
from src.ports.repositories.role_repo import IRoleRepository
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class RefreshTokenUseCase:
    """
    Use case for refreshing an access token using a refresh token.

    This class handles the token refresh process, including:
    - Decoding and validating the provided refresh token.
    - Verifying the existence of the associated user.
    - Generating a new access token for the user.
    - Retrieving the user's role and updating their login status.

    Dependencies:
        user_repo (IUserRepository): Interface to access and manage user data.
        access_token (IAccessToken): Interface to handle token decoding and creation.
        role_repo (IRoleRepository): Interface to retrieve role data.

    Methods:
        execute(refresh_token: str) -> dict:
            Processes the refresh token and returns a new access token with user role information.
    """

    def __init__(
        self, user_repo: IUserRepository, access_token: IAccessToken, role_repo: IRoleRepository
    ):
        self._user_repo = user_repo
        self._access_token = access_token
        self._role_repo = role_repo

    async def execute(self, refresh_token: str):
        try:
            payload = self._access_token.decode_access_token(refresh_token, check_type=False)
            user_id = payload.get("sub")
            user_id = uuid.UUID(user_id)
            user = await self._user_repo.get_by_id(user_id)

            if not user:
                raise UserNotFound("User not found")

            try:
                token_type = payload.get("type")

            except Exception:
                raise InvalidRefreshToken("Invalid refresh token")

            if token_type != "refresh_token":
                raise InvalidRefreshToken("Invalid refresh token")

            payload = {"sub": str(user.id)}
            access_token = self._access_token.create_access_token(data=payload)
            role = await self._role_repo.get_role_by_id(role_id=user.role_id)
            await self._user_repo.update(
                user_id=user.id,
                user_new_data={
                    "is_locked": False,
                    "lock_expire_time": None,
                    "login_retries": 0,
                    "latest_login": datetime.now(),
                },
            )
            return {"access_token": access_token, "role": role.role_name, "token_type": "bearer"}

        except ExpiredSignatureError:
            raise ExpRefreshToken("Invalid refresh token")

        except Exception as e:
            raise e

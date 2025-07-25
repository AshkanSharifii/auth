from typing import Optional
import uuid

from src.domain.exceptions import UserNotFound
from src.domain.interfaces.access_token import IAccessToken
from src.ports.repositories.brand_repo import IBrandRepository
from src.ports.repositories.role_repo import IRoleRepository
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class GetCurrentUserUseCase:
    """
    Use case for retrieving the currently authenticated user.

    This class handles the process of:
    - Decoding the access token to extract the user ID.
    - Fetching the user from the database using the extracted ID.

    Dependencies:
        user_repo (IUserRepository): Interface to access user data.
        access_token (IAccessToken): Interface to decode JWT access tokens.

    Methods:
        execute(token: str) -> Optional[User]:
            Decodes the access token and returns the corresponding user entity.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        role_repo: IRoleRepository,
        brand_repo: IBrandRepository,
        access_token: IAccessToken,
    ):
        self._user_repo = user_repo
        self._role_repo = role_repo
        self._brand_repo = brand_repo
        self._access_token = access_token

    async def execute(self, token: str) -> Optional[tuple]:
        """
        Retrieves the user associated with the given JWT access token.

        This method:
        - Decodes the token to extract the user ID.
        - Fetches the user from the repository using the ID.

        Args:
            token (str): The JWT access token.

        Returns:
            Optional[tuple]: The user entity, user role and user

        Raises:
            UserNotFound: If the user ID is missing in the token or the user is not found in the database.
        """
        try:
            payload = self._access_token.decode_access_token(token)
            user_id = payload["sub"]
            user_id = uuid.UUID(user_id)
            if not user_id:
                raise UserNotFound("User id does not exist")
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")
            user_role = await self._role_repo.get_role_by_id(role_id=user.role_id)
            user_brands = await self._brand_repo.get_by_user_id(user_id=user.id)
            return user, user_role, user_brands
        except Exception as e:
            raise e

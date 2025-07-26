from typing import List, Optional
from uuid import UUID

from src.domain.exceptions import UserNotFound, RoleNotFound
from src.ports.repositories.user_repo import IUserRepository
from src.ports.repositories.role_repo import IRoleRepository
from src.domain.entities.user import User
from src.domain.entities.role import Role


# ----------------------------------------------------------------------------
class ConfirmUserBySuperAdminUseCase:
    """
    Use case for super admin to confirm/verify a user account.
    """

    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def execute(self, user_id: UUID, admin_user: User) -> bool:
        """
        Confirms a user account by super admin.

        Args:
            user_id (UUID): The ID of the user to confirm.
            admin_user (User): The admin user performing the action.

        Returns:
            bool: True if user was successfully confirmed.

        Raises:
            UserNotFound: If the user to be confirmed does not exist.
        """
        try:
            # Verify user exists
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")

            # Update user verification status
            await self._user_repo.update(
                user_id=user_id,
                user_new_data={
                    "is_verified": True,
                    "email_verified": True,
                    "phone_number_verified": True,
                    "is_active": True
                }
            )
            return True
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class ActivateUserBySuperAdminUseCase:
    """
    Use case for super admin to activate/deactivate a user account.
    """

    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def execute(self, user_id: UUID, is_active: bool, admin_user: User) -> bool:
        """
        Activates or deactivates a user account.

        Args:
            user_id (UUID): The ID of the user to activate/deactivate.
            is_active (bool): Whether to activate (True) or deactivate (False) the user.
            admin_user (User): The admin user performing the action.

        Returns:
            bool: True if operation was successful.

        Raises:
            UserNotFound: If the user does not exist.
        """
        try:
            # Verify user exists
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")

            # Update user active status
            await self._user_repo.update(
                user_id=user_id,
                user_new_data={"is_active": is_active}
            )
            return True
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class GetAllUsersUseCase:
    """
    Use case for retrieving all users in the system.
    """

    def __init__(self, user_repo: IUserRepository, role_repo: IRoleRepository):
        self._user_repo = user_repo
        self._role_repo = role_repo

    async def execute(self, admin_user: User) -> List[tuple]:
        """
        Retrieves all users in the system with their roles.

        Args:
            admin_user (User): The admin user performing the action.

        Returns:
            List[tuple]: List of (user, role) tuples.
        """
        try:
            users = await self._user_repo.get_all()

            user_role_pairs = []
            for user in users:
                role = await self._role_repo.get_role_by_id(user.role_id)
                user_role_pairs.append((user, role))

            return user_role_pairs
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class GetSpecificUserUseCase:
    """
    Use case for retrieving a specific user by ID.
    """

    def __init__(self, user_repo: IUserRepository, role_repo: IRoleRepository):
        self._user_repo = user_repo
        self._role_repo = role_repo

    async def execute(self, user_id: UUID, admin_user: User) -> Optional[tuple]:
        """
        Retrieves a specific user by ID with their role.

        Args:
            user_id (UUID): The ID of the user to retrieve.
            admin_user (User): The admin user performing the action.

        Returns:
            Optional[tuple]: (user, role) tuple if found, None otherwise.

        Raises:
            UserNotFound: If the user does not exist.
        """
        try:
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")

            role = await self._role_repo.get_role_by_id(user.role_id)
            return user, role
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class AssignRoleToUserUseCase:
    """
    Use case for super admin to assign a role to a user.
    """

    def __init__(self, user_repo: IUserRepository, role_repo: IRoleRepository):
        self._user_repo = user_repo
        self._role_repo = role_repo

    async def execute(self, user_id: UUID, role_id: UUID, admin_user: User) -> bool:
        """
        Assigns a role to a user.

        Args:
            user_id (UUID): The ID of the user to assign the role to.
            role_id (UUID): The ID of the role to assign.
            admin_user (User): The admin user performing the action.

        Returns:
            bool: True if role was successfully assigned.

        Raises:
            UserNotFound: If the user does not exist.
            RoleNotFound: If the role does not exist.
        """
        try:
            # Verify user exists
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")

            # Verify role exists
            role = await self._role_repo.get_role_by_id(role_id)
            if not role:
                raise RoleNotFound("Role not found")

            # Update user's role
            await self._user_repo.update(
                user_id=user_id,
                user_new_data={"role_id": role_id}
            )
            return True
        except Exception as e:
            raise e
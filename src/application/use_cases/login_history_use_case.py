from typing import List, Optional
from uuid import UUID
from datetime import datetime

from src.domain.entities.login_history import LoginHistory
from src.domain.entities.user import User
from src.domain.exceptions import UserNotFound
from src.ports.repositories.user_repo import IUserRepository
from src.ports.repositories.login_history_repo import ILoginHistoryRepository


# ----------------------------------------------------------------------------
class RecordLoginHistoryUseCase:
    """
    Use case for recording login history.
    """

    def __init__(self, login_history_repo: ILoginHistoryRepository):
        self._login_history_repo = login_history_repo

    async def execute(
        self,
        user_id: UUID,
        ip_address: str,
        user_agent: str,
        login_method: str,
        success: bool,
        failure_reason: str | None = None
    ) -> LoginHistory:
        """
        Records a login attempt in the history.

        Args:
            user_id (UUID): The user attempting login.
            ip_address (str): IP address of the request.
            user_agent (str): Browser/device information.
            login_method (str): Method used (password, otp, etc.).
            success (bool): Whether login was successful.
            failure_reason (str | None): Reason for failure if applicable.

        Returns:
            LoginHistory: The created login history record.
        """
        try:
            login_record = LoginHistory(
                user_id=user_id,
                login_time=datetime.now(),
                ip_address=ip_address,
                user_agent=user_agent,
                login_method=login_method,
                success=success,
                failure_reason=failure_reason
            )

            return await self._login_history_repo.insert(login_record)
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class GetLoginHistoryUseCase:
    """
    Use case for retrieving user login history.
    """

    def __init__(
        self,
        login_history_repo: ILoginHistoryRepository,
        user_repo: IUserRepository
    ):
        self._login_history_repo = login_history_repo
        self._user_repo = user_repo

    async def execute(
        self,
        user_id: UUID,
        admin_user: User,
        limit: int = 50,
        offset: int = 0
    ) -> List[LoginHistory]:
        """
        Retrieves login history for a specific user.

        Args:
            user_id (UUID): The user whose history to retrieve.
            admin_user (User): The admin requesting the history.
            limit (int): Maximum number of records to return.
            offset (int): Number of records to skip.

        Returns:
            List[LoginHistory]: List of login history records.

        Raises:
            UserNotFound: If the target user doesn't exist.
        """
        try:
            # Verify target user exists
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")

            return await self._login_history_repo.get_by_user_id(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class GetMyLoginHistoryUseCase:
    """
    Use case for users to get their own login history.
    """

    def __init__(self, login_history_repo: ILoginHistoryRepository):
        self._login_history_repo = login_history_repo

    async def execute(
        self,
        user: User,
        limit: int = 50,
        offset: int = 0
    ) -> List[LoginHistory]:
        """
        Retrieves login history for the current user.

        Args:
            user (User): The user requesting their own history.
            limit (int): Maximum number of records to return.
            offset (int): Number of records to skip.

        Returns:
            List[LoginHistory]: List of login history records.
        """
        try:
            return await self._login_history_repo.get_by_user_id(
                user_id=user.id,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            raise e
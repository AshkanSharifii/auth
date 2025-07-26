from typing import override, List
from uuid import UUID

from sqlalchemy import select, desc

from src.domain.entities.login_history import LoginHistory
from src.domain.interfaces.sql_connection import ISQLConnection
from src.infrastructure.models.login_history_model import LoginHistoryModel
from src.ports.repositories.login_history_repo import ILoginHistoryRepository


# ----------------------------------------------------------------------------
class LoginHistoryRepository(ILoginHistoryRepository):
    """
    Repository implementation for managing LoginHistory entities in the database.
    """

    def __init__(self, sql_connection: ISQLConnection):
        self._sql_connection = sql_connection

    def _model_to_entity(self, history_model: LoginHistoryModel) -> LoginHistory:
        """Convert LoginHistoryModel to LoginHistory entity"""
        return LoginHistory(
            user_id=history_model.user_id,
            login_time=history_model.login_time,
            ip_address=history_model.ip_address,
            user_agent=history_model.user_agent,
            login_method=history_model.login_method,
            success=history_model.success,
            failure_reason=history_model.failure_reason,
            id=history_model.id,
        )

    @override
    async def insert(self, login_history: LoginHistory) -> LoginHistory:
        """
        Inserts a new login history record into the database.

        Args:
            login_history (LoginHistory): The login history domain object to insert.

        Returns:
            LoginHistory: The inserted login history object.

        Raises:
            Exception: If a database error occurs.
        """
        history_model = LoginHistoryModel(**login_history.to_dict())
        try:
            async with self._sql_connection.session() as session:
                session.add(history_model)
                await session.commit()
                await session.refresh(history_model)
                return login_history
        except Exception as e:
            raise e

    @override
    async def get_by_user_id(
            self,
            user_id: UUID,
            limit: int = 50,
            offset: int = 0
    ) -> List[LoginHistory]:
        """
        Retrieves login history for a specific user, ordered by most recent first.

        Args:
            user_id (UUID): The user's ID.
            limit (int): Maximum number of records to return.
            offset (int): Number of records to skip.

        Returns:
            List[LoginHistory]: List of login history entities.
        """
        async with self._sql_connection.session() as session:
            query = (
                select(LoginHistoryModel)
                .where(LoginHistoryModel.user_id == user_id)
                .order_by(desc(LoginHistoryModel.login_time))
                .offset(offset)
                .limit(limit)
            )

            result = await session.execute(query)
            history_models = result.scalars().all()

            return [self._model_to_entity(model) for model in history_models]

    @override
    async def get_by_id(self, history_id: UUID) -> LoginHistory | None:
        """
        Retrieves a specific login history record by ID.

        Args:
            history_id (UUID): The login history record ID.

        Returns:
            LoginHistory | None: The login history entity if found, else None.
        """
        async with self._sql_connection.session() as session:
            query = select(LoginHistoryModel).where(LoginHistoryModel.id == history_id)
            result = await session.execute(query)
            if history_model := result.scalars().one_or_none():
                return self._model_to_entity(history_model)
            return None
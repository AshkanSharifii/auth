from uuid import UUID
from typing import (override,
                    Optional)
from sqlalchemy import select, func

from src.domain.entities.role import Role
from src.infrastructure.models.role_model import RoleModel
from src.ports.repositories.role_repo import IRoleRepository
from src.domain.interfaces.sql_connection import ISQLConnection


# ----------------------------------------------------------------------------
class RoleRepository(IRoleRepository):
    """
    Repository implementation for managing roles in the database.

    Provides methods to retrieve and insert role entities using an asynchronous
    SQLAlchemy connection. Implements the IRoleRepository interface.

    Attributes:
        _sql_connection (ISQLConnection): The database connection/session provider.
    """

    def __init__(self, sql_connection: ISQLConnection):
        self._sql_connection = sql_connection

    @override
    async def get_role_by_id(self, role_id: UUID) -> Optional[Role]:
        """
        Retrieves a role entity by its unique identifier.

        Args:
            role_id (UUID): The ID of the role to retrieve.

        Returns:
            Optional[Role]: The role entity if found, otherwise None.
        """
        async with self._sql_connection.session() as session:
            query = select(RoleModel).where(RoleModel.id == role_id)
            result = await session.execute(query)
            if role := result.scalars().one_or_none():
                return Role(role_name=role.role_name,
                            id=role.id)

    @override
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        Retrieves a role entity by its name, case-insensitive.

        Args:
            name (str): The name of the role to search for.

        Returns:
            Optional[Role]: The role entity if found, otherwise None.
        """
        async with self._sql_connection.session() as session:
            query = select(RoleModel).where(func.lower(RoleModel.role_name) == name.lower())
            result = await session.execute(query)
            if role := result.scalars().one_or_none():
                return Role(role_name=role.role_name,
                            id=role.id)

    @override
    async def insert(self, role: Role) -> Role:
        """
        Inserts a new role entity into the database.

        Args:
            role (Role): The role domain object to persist.

        Returns:
            Role: The same role object after it has been saved.

        Raises:
            Exception: If any database error occurs during the operation.
        """
        role_model = RoleModel(**role.to_dict())
        try:
            async with self._sql_connection.session() as session:
                session.add(role_model)
                await session.commit()
                await session.refresh(role_model)
                return role
        except Exception as e:
            raise e

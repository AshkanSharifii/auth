from typing import override
from uuid import UUID

from sqlalchemy import select

from src.domain.entities.user import User
from src.domain.interfaces.sql_connection import ISQLConnection
from src.infrastructure.models.user_model import UserModel
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class UserRepository(IUserRepository):
    """
    Repository implementation for managing User entities in the database.

    Provides CRUD operations and authentication-related logic for User data
    using an asynchronous SQLAlchemy session. Implements the IUserRepository interface.

    Attributes:
        _sql_connection (ISQLConnection): Asynchronous SQL connection provider.
    """

    def __init__(self, sql_connection: ISQLConnection):
        self._sql_connection = sql_connection

    async def _get_user_by_id(self, session, user_id: UUID):
        """
        Internal helper method to fetch a UserModel instance by ID.

        Args:
            session (AsyncSession): The current SQLAlchemy async session.
            user_id (UUID): The ID of the user to retrieve.

        Returns:
            Optional[UserModel]: The user model instance if found, else None.
        """
        query = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    def _model_to_entity(self, user_model: UserModel) -> User:
        """Convert UserModel to User entity"""
        return User(
            phone_number=user_model.phone_number,
            email=user_model.email,
            name=user_model.name,
            family=user_model.family,
            hashed_password=user_model.hashed_password,
            role_id=user_model.role_id,
            position=user_model.position,
            personal_code=user_model.personal_code,
            is_verified=user_model.is_verified,
            email_verified=user_model.email_verified,
            phone_number_verified=user_model.phone_number_verified,
            latest_login=user_model.latest_login,
            login_retries=user_model.login_retries,
            lock_expire_time=user_model.lock_expire_time,
            is_locked=user_model.is_locked,
            is_active=user_model.is_active,
            id=user_model.id,
        )

    @override
    async def get_by_id(self, user_id: UUID):
        """
        Retrieves a user domain object by its unique identifier.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            Optional[User]: The user entity if found, else None.
        """
        async with self._sql_connection.session() as session:
            if user := await self._get_user_by_id(session, user_id):
                return self._model_to_entity(user)
            return None

    @override
    async def get_by_phone_number(self, phone_number: str):
        """
        Retrieves a user domain object by their phone number.

        Args:
            phone_number (str): The user's phone number.

        Returns:
            Optional[User]: The user entity if found, else None.
        """
        async with self._sql_connection.session() as session:
            query = select(UserModel).where(UserModel.phone_number == phone_number)
            result = await session.execute(query)
            if user := result.scalars().one_or_none():
                return self._model_to_entity(user)
            return None

    @override
    async def get_by_email(self, email: str):
        """
        Retrieves a user domain object by their email.

        Args:
            email (str): The user's email.

        Returns:
            Optional[User]: The user entity if found, else None.
        """
        async with self._sql_connection.session() as session:
            query = select(UserModel).where(UserModel.email == email)
            result = await session.execute(query)
            if user := result.scalars().one_or_none():
                return self._model_to_entity(user)
            return None

    @override
    async def get_by_personal_code(self, personal_code: str):
        """
        Retrieves a user domain object by their personal code.

        Args:
            personal_code (str): The user's personal code.

        Returns:
            Optional[User]: The user entity if found, else None.
        """
        async with self._sql_connection.session() as session:
            query = select(UserModel).where(UserModel.personal_code == personal_code)
            result = await session.execute(query)
            if user := result.scalars().one_or_none():
                return self._model_to_entity(user)
            return None

    @override
    async def insert(self, user: User):
        """
        Inserts a new user into the database.

        Args:
            user (User): The user domain object to insert.

        Returns:
            User: The inserted user object.

        Raises:
            Exception: If a database error occurs.
        """
        user_model = UserModel(**user.to_dict())
        try:
            async with self._sql_connection.session() as session:
                session.add(user_model)
                await session.commit()
                await session.refresh(user_model)
                return user
        except Exception as e:
            raise e

    @override
    async def update(self, user_id: UUID, user_new_data):
        try:
            async with self._sql_connection.session() as session:
                if user := await self._get_user_by_id(session=session, user_id=user_id):
                    for field in user_new_data:
                        setattr(user, field, user_new_data[field])
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                return None
        except Exception as e:
            raise e
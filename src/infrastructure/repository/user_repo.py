from typing import override, List, Optional
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
    Simplified for email-only authentication system.

    Provides CRUD operations for User data using an asynchronous
    SQLAlchemy session. Email is the primary authentication method.
    """

    def __init__(self, sql_connection: ISQLConnection):
        self._sql_connection = sql_connection

    async def _get_user_by_id(self, session, user_id: UUID):
        """Helper method to fetch a UserModel instance by ID."""
        query = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    def _model_to_entity(self, user_model: UserModel) -> User:
        """Convert UserModel to User entity"""
        return User(
            email=user_model.email,
            phone_number=user_model.phone_number,
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
        """Retrieve user by ID"""
        async with self._sql_connection.session() as session:
            if user := await self._get_user_by_id(session, user_id):
                return self._model_to_entity(user)
            return None

    @override
    async def get_by_email(self, email: str):
        """Retrieve user by email (primary authentication method)"""
        async with self._sql_connection.session() as session:
            query = select(UserModel).where(UserModel.email == email)
            result = await session.execute(query)
            if user := result.scalars().one_or_none():
                return self._model_to_entity(user)
            return None

    @override
    async def get_by_personal_code(self, personal_code: str):
        """Retrieve user by personal code"""
        async with self._sql_connection.session() as session:
            query = select(UserModel).where(UserModel.personal_code == personal_code)
            result = await session.execute(query)
            if user := result.scalars().one_or_none():
                return self._model_to_entity(user)
            return None

    @override
    async def get_by_phone_number(self, phone_number: str):
        """
        Retrieve user by phone number (for contact purposes only, not authentication)
        Returns None if phone_number is empty or None
        """
        if not phone_number or phone_number.strip() == "":
            return None

        async with self._sql_connection.session() as session:
            query = select(UserModel).where(
                UserModel.phone_number == phone_number,
                UserModel.phone_number.isnot(None)
            )
            result = await session.execute(query)
            if user := result.scalars().one_or_none():
                return self._model_to_entity(user)
            return None

    @override
    async def insert(self, user: User):
        """Insert new user into database"""
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
        """Update user data"""
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

    @override
    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[User]:
        """Retrieve all users with optional pagination"""
        async with self._sql_connection.session() as session:
            query = select(UserModel)

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            result = await session.execute(query)
            user_models = result.scalars().all()

            return [self._model_to_entity(user_model) for user_model in user_models]
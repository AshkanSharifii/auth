from uuid import UUID
from typing import Optional
from abc import ABC, abstractmethod

from src.domain.entities.user import User


# ----------------------------------------------------------------------------
class IUserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        ...

    @abstractmethod
    async def get_by_phone_number(self, phone_number) -> Optional[User]:
        ...

    @abstractmethod
    async def insert(self, user: User) -> User:
        ...

    @abstractmethod
    async def lock_user(self, user_id: UUID) -> User:
        ...

    @abstractmethod
    async def update_user_login_status(self, user_id: UUID, login: bool):
        ...

    @abstractmethod
    async def increase_login_attempts(self, user_id: UUID):
        ...
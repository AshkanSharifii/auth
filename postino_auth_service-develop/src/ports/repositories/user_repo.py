from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.user import User


# ----------------------------------------------------------------------------
class IUserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...

    @abstractmethod
    async def get_by_phone_number(self, phone_number) -> Optional[User]: ...

    @abstractmethod
    async def insert(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user_id: UUID, user_new_data: dict) -> Optional[User]: ...

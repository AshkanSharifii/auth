from uuid import UUID
from typing import Optional
from abc import ABC, abstractmethod

from src.domain.entities.role import Role


# ----------------------------------------------------------------------------
class IRoleRepository(ABC):
    @abstractmethod
    async def get_role_by_id(self, role_id: UUID) -> Optional[Role]:
        ...

    @abstractmethod
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        ...

    @abstractmethod
    async def insert(self, role: Role) -> Role:
        ...
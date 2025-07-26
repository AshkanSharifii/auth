from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.domain.entities.login_history import LoginHistory


# ----------------------------------------------------------------------------
class ILoginHistoryRepository(ABC):

    @abstractmethod
    async def insert(self, login_history: LoginHistory) -> LoginHistory: ...

    @abstractmethod
    async def get_by_user_id(
            self,
            user_id: UUID,
            limit: int = 50,
            offset: int = 0
    ) -> List[LoginHistory]: ...

    @abstractmethod
    async def get_by_id(self, history_id: UUID) -> LoginHistory | None: ...
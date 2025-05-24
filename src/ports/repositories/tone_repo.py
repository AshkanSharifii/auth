from abc import ABC, abstractmethod
from uuid import UUID


from src.domain.entities.tone import BrandTone


class IBrandToneRepository(ABC):

    @abstractmethod
    async def get_by_id(self, tone_id: UUID) -> BrandTone: ...

    @abstractmethod
    async def get_all(self) -> list[BrandTone]: ...

    @abstractmethod
    async def insert(tone: BrandTone) -> BrandTone: ...

    @abstractmethod
    async def update(self, tone_id: UUID, tone_name: str, tone_desc: str) -> BrandTone: ...

    @abstractmethod
    async def delete(self, tone_id: UUID) -> bool: ...
 
from abc import ABC, abstractmethod
from uuid import UUID


from src.domain.entities.industry import BrandIndustry


class IBrandIndustryRepository(ABC):

    @abstractmethod
    async def get_by_id(self, industry_id: UUID) -> BrandIndustry: ...

    @abstractmethod
    async def get_all(self) -> list[BrandIndustry]: ...

    @abstractmethod
    async def insert(industry: BrandIndustry): ...

    @abstractmethod
    async def update(self, industry_id: UUID, industry_name: str, industry_desc: str) -> BrandIndustry: ...

    @abstractmethod
    async def delete(self, industry_id: UUID) -> bool: ...
    
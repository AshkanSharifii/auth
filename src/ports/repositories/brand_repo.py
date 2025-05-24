from fastapi import UploadFile
from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.brand import Brand


# ----------------------------------------------------------------------------
class IBrandRepository(ABC):

    @abstractmethod
    async def get_by_id(self, brand_id: UUID): ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID): ...

    @abstractmethod
    async def insert(brand: Brand): ...

    @abstractmethod
    async def update(
            self, brand_id: UUID, user_id: UUID, brand_name: str,
            brand_logo_url: str, brand_desc: str, brand_tone: UUID, 
            brand_industry: UUID, brand_slogan: str, 
            brand_audience: str, brand_color: str): ...

    @abstractmethod
    async def delete(self, brand_id: UUID): ...

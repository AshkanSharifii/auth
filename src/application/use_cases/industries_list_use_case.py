from typing import List

from src.domain.entities.industry import BrandIndustry
from src.ports.repositories.industry_repo import IBrandIndustryRepository


class GetBrandIndustriesUseCase:
    """
    Use case for retrieving all brand industries from the system.

    This class handles the process of fetching all brand industry entities from the database,
    providing a simple interface to access the complete list of industries.

    Dependencies:
        industry_repo (IBrandIndustryRepository): Interface to access brand industry data.

    Methods:
        execute() -> List[BrandIndustry]:
            Retrieves all brand industries and returns them as a list.
    """
    
    def __init__(self, industry_repo: IBrandIndustryRepository):
        self._industry_repo = industry_repo

    async def execute(self) -> List[BrandIndustry]:
        return await self._industry_repo.get_all()
    
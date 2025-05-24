from uuid import UUID
from datetime import datetime

from src.ports.repositories.industry_repo import IBrandIndustryRepository
from src.ports.repositories.role_repo import IRoleRepository
from src.domain.entities.industry import BrandIndustry


class CreateBrandIndustryUseCase:
    """
    Use case for creating a brand industry in the system.

    This class handles the brand industry creation process, including:
    - Verifying the user's role to ensure only admins can create industries.
    - Creating and persisting the brand industry entity with the provided name and description.

    Dependencies:
        industry_repo (IBrandIndustryRepository): Interface to access and persist brand industry data.
        role_repo (IRoleRepository): Interface to retrieve role data for permission checks.

    Methods:
        execute(industry_name: str, industry_desc: str, user_role_id: UUID) -> BrandIndustry:
            Orchestrates the brand industry creation process and returns the created industry entity.
    """

    def __init__(self, industry_repo=IBrandIndustryRepository, role_repo=IRoleRepository):
        self._industry_repo = industry_repo
        self._role_repo = role_repo

    async def execute(self, industry_name: str, industry_desc: str, user_role_id: UUID) -> BrandIndustry:
        
        try:
            role = await self._role_repo.get_role_by_id(role_id=user_role_id)

            if role.role_name != 'admin':
                raise PermissionError('Permission denied')
            
            industry = BrandIndustry(
                industry_name=industry_name,
                industry_description=industry_desc,
                industry_created_at=datetime.now()
            )

            industry = await self._industry_repo.insert(
                industry
            )
            return industry
            
        except Exception as e:
            raise e

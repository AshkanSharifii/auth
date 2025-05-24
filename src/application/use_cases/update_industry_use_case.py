from uuid import UUID

from src.ports.repositories.industry_repo import IBrandIndustryRepository
from src.ports.repositories.role_repo import IRoleRepository


class UpdateBrandIndustryUseCase:
    """
    Use case for updating an existing brand industry in the system.

    This class handles the brand industry update process, including:
    - Verifying the user's role to ensure only admins can update industries.
    - Updating the brand industry entity with the provided name and description.

    Dependencies:
        industry_repo (IBrandIndustryRepository): Interface to access and manage brand industry data.
        role_repo (IRoleRepository): Interface to retrieve role data for permission checks.

    Methods:
        execute(industry_id: UUID, industry_name: str, industry_desc: str, user_role_id: UUID) -> BrandIndustry:
            Orchestrates the brand industry update process and returns the updated industry entity.
    """

    def __init__(self, industry_repo=IBrandIndustryRepository, role_repo=IRoleRepository):
        self._industry_repo = industry_repo
        self._role_repo = role_repo

    async def execute(self, industry_id: UUID, industry_name: str, industry_desc: str, user_role_id: UUID):
        
        try:
            role = await self._role_repo.get_role_by_id(role_id=user_role_id)

            if role.role_name != 'admin':
                raise PermissionError('Permission denied')

            industry = await self._industry_repo.update(
                industry_id=industry_id,
                industry_name=industry_name,
                industry_desc=industry_desc
            )
            return industry
            
        except Exception as e:
            raise e

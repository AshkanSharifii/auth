from uuid import UUID

from src.ports.repositories.industry_repo import IBrandIndustryRepository
from src.ports.repositories.role_repo import IRoleRepository


class DeleteBrandIndustryUseCase:
    """
    Use case for deleting a brand industry from the system.

    This class handles the brand industry deletion process, including:
    - Verifying the user's role to ensure only admins can delete industries.
    - Deleting the brand industry entity identified by the provided industry ID.

    Dependencies:
        industry_repo (IBrandIndustryRepository): Interface to access and manage brand industry data.
        role_repo (IRoleRepository): Interface to retrieve role data for permission checks.

    Methods:
        execute(industry_id: UUID, user_role_id: UUID) -> None:
            Orchestrates the brand industry deletion process.
    """
    
    def __init__(self, industry_repo=IBrandIndustryRepository, role_repo=IRoleRepository):
        self._industry_repo = industry_repo
        self._role_repo = role_repo

    async def execute(self, industry_id: UUID, user_role_id: UUID):
        
        try:
            role = await self._role_repo.get_role_by_id(role_id=user_role_id)

            if role.role_name != 'admin':
                raise PermissionError('Permission denied')

            await self._industry_repo.delete(industry_id=industry_id)
            
        except Exception as e:
            raise e

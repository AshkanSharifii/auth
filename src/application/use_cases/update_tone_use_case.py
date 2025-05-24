from uuid import UUID

from src.ports.repositories.tone_repo import IBrandToneRepository
from src.ports.repositories.role_repo import IRoleRepository


class UpdateBrandToneUseCase:
    """
    Use case for updating an existing brand tone in the system.

    This class handles the brand tone update process, including:
    - Verifying the user's role to ensure only admins can update industries.
    - Updating the brand tone entity with the provided name and description.

    Dependencies:
        tone_repo (IBrandToneRepository): Interface to access and manage brand tone data.
        role_repo (IRoleRepository): Interface to retrieve role data for permission checks.

    Methods:
        execute(tone_id: UUID, tone_name: str, tone_desc: str, user_role_id: UUID) -> BrandTone:
            Orchestrates the brand tone update process and returns the updated tone entity.
    """

    def __init__(self, tone_repo=IBrandToneRepository, role_repo=IRoleRepository):
        self._tone_repo = tone_repo
        self._role_repo = role_repo

    async def execute(self, tone_id: UUID, tone_name: str, tone_desc: str, user_role_id: UUID):
        
        try:
            role = await self._role_repo.get_role_by_id(role_id=user_role_id)

            if role.role_name != 'admin':
                raise PermissionError('Permission denied')

            tone = await self._tone_repo.update(
                tone_id=tone_id,
                tone_name=tone_name,
                tone_desc=tone_desc
            )
            return tone
            
        except Exception as e:
            raise e

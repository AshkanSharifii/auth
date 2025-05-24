from uuid import UUID

from src.ports.repositories.tone_repo import IBrandToneRepository
from src.ports.repositories.role_repo import IRoleRepository


class DeleteBrandToneUseCase:
    """
    Use case for deleting a brand tone from the system.

    This class handles the brand tone deletion process, including:
    - Verifying the user's role to ensure only admins can delete industries.
    - Deleting the brand tone entity identified by the provided tone ID.

    Dependencies:
        tone_repo (IBrandToneRepository): Interface to access and manage brand tone data.
        role_repo (IRoleRepository): Interface to retrieve role data for permission checks.

    Methods:
        execute(tone_id: UUID, user_role_id: UUID) -> None:
            Orchestrates the brand tone deletion process.
    """
    
    def __init__(self, tone_repo=IBrandToneRepository, role_repo=IRoleRepository):
        self._tone_repo = tone_repo
        self._role_repo = role_repo

    async def execute(self, tone_id: UUID, user_role_id: UUID):
        
        try:
            role = await self._role_repo.get_role_by_id(role_id=user_role_id)

            if role.role_name != 'admin':
                raise PermissionError('Permission denied')

            await self._tone_repo.delete(tone_id=tone_id)
            
        except Exception as e:
            raise e

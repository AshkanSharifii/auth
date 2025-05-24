from uuid import UUID
from datetime import datetime

from src.ports.repositories.tone_repo import IBrandToneRepository
from src.ports.repositories.role_repo import IRoleRepository
from src.domain.entities.tone import BrandTone


class CreateBrandToneUseCase:
    """
    Use case for creating a brand tone in the system.

    This class handles the brand tone creation process, including:
    - Verifying the user's role to ensure only admins can create tones.
    - Creating and persisting the brand tone entity with the provided name and description.

    Dependencies:
        tone_repo (IBrandToneRepository): Interface to access and persist brand tone data.
        role_repo (IRoleRepository): Interface to retrieve role data for permission checks.

    Methods:
        execute(tone_name: str, tone_desc: str, user_role_id: UUID) -> BrandTone:
            Orchestrates the brand tone creation process and returns the created tone entity.
    """

    def __init__(self, tone_repo=IBrandToneRepository, role_repo=IRoleRepository):
        self._tone_repo = tone_repo
        self._role_repo = role_repo

    async def execute(self, tone_name: str, tone_desc: str, user_role_id: UUID) -> BrandTone:
        
        try:
            role = await self._role_repo.get_role_by_id(role_id=user_role_id)

            if role.role_name != 'admin':
                raise PermissionError('Permission denied')
            
            tone = BrandTone(
                tone_name=tone_name,
                tone_description=tone_desc,
                tone_created_at=datetime.now()
            )

            tone = await self._tone_repo.insert(
                tone
            )
            return tone
            
        except Exception as e:
            raise e

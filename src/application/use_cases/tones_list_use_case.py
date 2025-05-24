from typing import List

from src.domain.entities.tone import BrandTone
from src.ports.repositories.tone_repo import IBrandToneRepository


class GetBrandTonesUseCase:
    """
    Use case for retrieving all brand tones from the system.

    This class handles the process of fetching all brand tone entities from the database,
    providing a simple interface to access the complete list of tones.

    Dependencies:
        tone_repo (IBrandToneRepository): Interface to access brand tone data.

    Methods:
        execute() -> List[BrandTone]:
            Retrieves all brand tones and returns them as a list.
    """

    def __init__(self, tone_repo: IBrandToneRepository):
        self._tone_repo = tone_repo

    async def execute(self) -> List[BrandTone]:
        return await self._tone_repo.get_all()
    
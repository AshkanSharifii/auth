from uuid import UUID

from src.ports.repositories.brand_repo import IBrandRepository
from src.domain.interfaces.object_storage import IObjectStorage


class DeleteUserBrandUseCase:
    """
    Use case for deleting a user brand from the system.

    This class handles the brand deletion process, including:
    - Deleting the brand entity identified by the provided brand ID and associated user ID.
    - Removing the brand's logo file from object storage.
    - Ensuring the operation is performed only by the brand's owner.

    Dependencies:
        brand_repo (IBrandRepository): Interface to access and manage brand data.
        object_storage (IObjectStorage): Interface to handle file deletion in object storage.

    Methods:
        execute(brand_id: UUID, user_id: UUID) -> bool:
            Orchestrates the brand deletion process and returns the result of the deletion.
    """

    def __init__(self, brand_repo: IBrandRepository, object_storage: IObjectStorage):
        self._brand_repo = brand_repo
        self._object_storage = object_storage

    async def execute(self, brand_id: UUID, user_id: UUID):

        try:
            logo_object_name, result = await self._brand_repo.delete(brand_id=brand_id, user_id=user_id)
            await self._object_storage.delete_file(bucket_name='brands', object_name=logo_object_name)
            return result
    
        except Exception as e: 
            raise e

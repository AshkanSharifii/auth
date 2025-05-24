from fastapi import UploadFile
from abc import ABC, abstractmethod


class IObjectStorage(ABC):

    @abstractmethod
    async def upload_file(self, file: UploadFile , bucket_name: str, object_name: str) -> str:
        ...

    @abstractmethod
    async def generate_presigned_url(self, bucket_name: str, object_name: str) -> str:
        ...

    @abstractmethod
    async def delete_file(self, bucket_name: str, object_name: str) -> str:
        ...

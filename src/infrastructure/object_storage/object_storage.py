from fastapi import UploadFile
from botocore.exceptions import ClientError
from typing import override
from io import BytesIO

from src.domain.interfaces.object_storage import IObjectStorage
from src.domain.exceptions import ObjStorageClientError
from src.config import settings

import aioboto3


class S3ObjectStorage(IObjectStorage):
    """
    Implementation of object storage operations using AWS S3.

    This class provides asynchronous methods for interacting with an S3-compatible storage service,
    including uploading files, generating presigned URLs, and deleting files. Implements the
    `IObjectStorage` interface to ensure adherence to the defined contract.

    Attributes:
        aws_access_key (str): AWS access key for S3 authentication.
        aws_secret_key (str): AWS secret key for S3 authentication.
        aws_endpoint_url (str): Endpoint URL for the S3-compatible storage service.

    Methods:
        upload_file(file: UploadFile, bucket_name: str, object_name: str) -> str:
            Uploads a file to the specified S3 bucket and returns the object name.
        generate_presigned_url(bucket_name: str, object_name: str) -> str:
            Generates a presigned URL for accessing an object in the specified S3 bucket.
        delete_file(bucket_name: str, object_name: str) -> str:
            Deletes an object from the specified S3 bucket and returns the response.
    """
    
    def __init__(self):
        self.aws_access_key = settings.OBJECT_STORAGE_ACCESS_KEY
        self.aws_secret_key = settings.OBJECT_STORAGE_SECRET_KEY
        self.aws_endpoint_url = settings.OBJECT_STORAGE_ENDPOINT_URL

    @override
    async def upload_file(self, file: UploadFile, bucket_name: str, object_name: str) -> str:
        object_name = object_name or file

        async with aioboto3.Session().client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            endpoint_url=self.aws_endpoint_url
        ) as s3_client:
            try:
                file_content = await file.read()
                file_obj = BytesIO(file_content)
                await s3_client.upload_fileobj(file_obj, bucket_name, object_name)
                return object_name
            except ClientError:
                raise ObjStorageClientError("Failed to upload file")

    @override
    async def generate_presigned_url(self, bucket_name: str, object_name: str) -> str:
        async with aioboto3.Session().client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
        ) as s3_client:
            try:
                url = await s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": object_name},
                )
                return url
            except ClientError:
                raise ObjStorageClientError("Failed to generate presigned URL")
    
    @override
    async def delete_file(self, bucket_name: str, object_name: str) -> str:
        async with aioboto3.Session().client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            endpoint_url=self.aws_endpoint_url
        ) as s3_client:
            try:
                response = await s3_client.delete_object(
                    Bucket=bucket_name,
                    Key=object_name
                )
                return response
            except ClientError:
                raise ObjStorageClientError("Failed to delete file")

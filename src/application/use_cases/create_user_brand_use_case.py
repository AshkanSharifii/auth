from fastapi import UploadFile
from uuid import UUID

from src.domain.entities.brand import Brand
from src.domain.exceptions import IndustryNotFound, ToneNotFound, InvalidHexColorCode
from src.ports.repositories.brand_repo import IBrandRepository
from src.domain.interfaces.object_storage import IObjectStorage
from src.ports.repositories.industry_repo import IBrandIndustryRepository
from src.ports.repositories.tone_repo import IBrandToneRepository

import datetime
import re


class CreateUserBrandUseCase:
    """
    Use case for creating a user brand in the system.

    This class handles the brand creation process, including:
    - Validating the brand color hex code format.
    - Verifying the existence of the specified brand tone and industry.
    - Uploading the brand logo to object storage and generating a presigned URL.
    - Creating and persisting the brand entity with associated details.
    - Handling cleanup of uploaded files in case of errors.

    Dependencies:
        brand_repo (IBrandRepository): Interface to access and persist brand data.
        industry_repo (IBrandIndustryRepository): Interface to retrieve brand industry data.
        object_storage (IObjectStorage): Interface to handle file uploads and URL generation.
        tone_repo (IBrandToneRepository): Interface to retrieve brand tone data.

    Methods:
        execute(user_id: UUID, brand_name: str, brand_logo: UploadFile, brand_desc: str, brand_tone: str, brand_industry: str, brand_slogan: str, brand_audience: str, brand_color: str) -> Brand:
            Orchestrates the brand creation process and returns the created brand entity.
    """

    def __init__(self, brand_repo: IBrandRepository, industry_repo: IBrandIndustryRepository, object_storage: IObjectStorage, tone_repo: IBrandToneRepository):
        self._brand_repo = brand_repo
        self._industry_repo = industry_repo
        self._tone_repo = tone_repo
        self._object_storage = object_storage

    async def execute(
            self, user_id: UUID, brand_name: str, brand_logo: UploadFile,
            brand_desc: str, brand_tone: str, brand_industry: str,
            brand_slogan: str, brand_audience: str, brand_color: str
        ) -> Brand:

        ct = datetime.datetime.now()
        object_name = f'brand_logo_{str(user_id)}_{int(ct.timestamp())}'

        try:
            if brand_color and not re.match(r'^#[0-9A-Fa-f]{6}$', brand_color):
                raise InvalidHexColorCode("Invalid hex color code. Must be like #FFFFFF")

            tone = await self._tone_repo.get_by_id(tone_id=brand_tone)

            if tone is None:
                raise ToneNotFound('Tone not found')
            
            industry = await self._industry_repo.get_by_id(industry_id=brand_industry)

            if industry is None:
                raise IndustryNotFound('Industry not found')
            
            object_name = await self._object_storage.upload_file(file=brand_logo, bucket_name='brands', object_name=object_name)
            logo_url = await self._object_storage.generate_presigned_url(bucket_name='brands', object_name=object_name)

            brand = Brand(
                user_id=user_id,
                brand_name=brand_name,
                brand_logo_url=logo_url,
                logo_obj_name=object_name,
                brand_desc=brand_desc,
                brand_slogan=brand_slogan,
                brand_audience=brand_audience,
                brand_color=brand_color,
                industry_id=industry.id,
                tone_id=tone.id
            )
            
            created_brand = await self._brand_repo.insert(brand)
            
            return created_brand
        
        except Exception as e:
            await self._object_storage.delete_file(bucket_name='brands', object_name=object_name)
            raise e
        
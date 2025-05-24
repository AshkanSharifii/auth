from uuid import UUID
from fastapi import UploadFile

from src.ports.repositories.brand_repo import IBrandRepository
from src.domain.interfaces.object_storage import IObjectStorage
from src.domain.exceptions import IndustryNotFound, ToneNotFound, InvalidHexColorCode
from src.ports.repositories.industry_repo import IBrandIndustryRepository
from src.ports.repositories.tone_repo import IBrandToneRepository
from src.domain.entities.brand import Brand

import datetime
import re


class UpdateUserBrandUseCase:
    """
    Use case for updating an existing user brand in the system.

    This class handles the brand update process, including:
    - Validating the brand color hex code format.
    - Verifying the existence of the specified brand tone and industry.
    - Uploading the updated brand logo to object storage and generating a presigned URL.
    - Updating the brand entity with new details.
    - Handling cleanup of uploaded files in case of errors.

    Dependencies:
        brand_repo (IBrandRepository): Interface to access and manage brand data.
        industry_repo (IBrandIndustryRepository): Interface to retrieve brand industry data.
        object_storage (IObjectStorage): Interface to handle file uploads and URL generation.
        tone_repo (IBrandToneRepository): Interface to retrieve brand tone data.

    Methods:
        execute(brand_id: UUID, user_id: UUID, brand_name: str, brand_logo: UploadFile, brand_desc: str, brand_tone: UUID, brand_industry: UUID, brand_slogan: str, brand_audience: str, brand_color: str) -> Brand:
            Orchestrates the brand update process and returns the updated brand entity.
    """
    
    def __init__(self, brand_repo: IBrandRepository, industry_repo: IBrandIndustryRepository, object_storage: IObjectStorage, tone_repo: IBrandToneRepository):
        self._brand_repo = brand_repo
        self._industry_repo = industry_repo
        self._tone_repo = tone_repo
        self._object_storage = object_storage

    async def execute(
            self, brand_id: UUID, user_id: UUID, brand_name: str,
            brand_logo: UploadFile, brand_desc: str, brand_tone: UUID, 
            brand_industry: UUID, brand_slogan: str, 
            brand_audience: str, brand_color: str
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
            
            await self._object_storage.upload_file(file=brand_logo, bucket_name='brands', object_name=object_name)
            logo_url = await self._object_storage.generate_presigned_url(bucket_name='brands', object_name=object_name)

            await self._brand_repo.update(
                brand_id=brand_id,
                user_id=user_id,
                brand_name=brand_name,
                brand_logo_url=logo_url,
                logo_obj_name=object_name,
                brand_desc=brand_desc,
                brand_slogan=brand_slogan,
                brand_audience=brand_audience,
                brand_color=brand_color,
                brand_industry=industry.id,
                brand_tone=tone.id
            )

            updated_brand = await self._brand_repo.get_by_id(brand_id=brand_id, user_id=user_id)
            
            return updated_brand
        
        except Exception as e: 
            await self._object_storage.delete_file(bucket_name='brands', object_name=object_name)
            raise e
    
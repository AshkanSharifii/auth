from typing import Optional, override
from uuid import UUID

from sqlalchemy import and_, func, select

from src.domain.entities.brand import Brand
from src.domain.exceptions import BrandExists, BrandNotFound
from src.domain.interfaces.sql_connection import ISQLConnection
from src.infrastructure.models.brand_model import BrandModel
from src.ports.repositories.brand_repo import IBrandRepository


# ----------------------------------------------------------------------------
class BrandRepository(IBrandRepository):
    """
    Repository implementation for managing brand entities in the database.

    Provides asynchronous methods for CRUD (Create, Read, Update, Delete) operations on
    brand entities using a SQLAlchemy database connection. Implements the
    `IBrandRepository` interface to ensure adherence to the defined contract.

    Attributes:
        _sql_connection (ISQLConnection): The database connection/session provider used for
            executing database operations.

    Methods:
        get_by_id: Retrieves a brand by its UUID and associated user ID.
        get_by_user_id: Retrieves all brands associated with a given user ID.
        insert: Inserts a new brand into the database, checking for name uniqueness.
        update: Updates an existing brand's attributes.
        delete: Deletes a brand by its UUID and user ID, returning the logo object name.

    Raises:
        BrandNotFound: If a brand is not found during retrieval, update, or delete operations.
        BrandExists: If a brand with the same name already exists for the user during insertion.
        Exception: For database access or query execution errors.
    """

    def __init__(self, sql_connection: ISQLConnection):
        self._sql_connection = sql_connection

    async def __get_brand_by_id(self, session, brand_id: UUID):
        query = select(BrandModel).where(BrandModel.id == brand_id)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    async def __get_brand_by_name(self, session, brand_name: str, user_id: UUID):
        query = select(BrandModel).where(
            and_(
                func.lower(BrandModel.brand_name) == brand_name.lower(),
                BrandModel.user_id == user_id,
            )
        )
        result = await session.execute(query)
        return result.scalars().one_or_none()

    @override
    async def get_by_id(self, brand_id: UUID, user_id: UUID) -> Optional[Brand]:
        try:
            async with self._sql_connection.session() as session:
                if brand := await self.__get_brand_by_id(session=session, brand_id=brand_id):
                    return Brand(
                        user_id=user_id,
                        brand_name=brand.brand_name,
                        brand_logo_url=brand.brand_logo_url,
                        logo_obj_name=brand.logo_obj_name,
                        brand_desc=brand.brand_desc,
                        brand_slogan=brand.brand_slogan,
                        brand_audience=brand.brand_audience,
                        brand_color=brand.brand_color,
                        industry_name=brand.industry.industry_name,
                        industry_id=brand.industry_id,
                        tone_name=brand.tone.tone_name,
                        tone_id=brand.tone_id,
                        id=brand.id,
                    )
                else:
                    raise BrandNotFound("Brand not found")
        except Exception as e:
            raise e

    @override
    async def get_by_user_id(self, user_id: UUID):
        try:
            async with self._sql_connection.session() as session:
                query = select(BrandModel).where(BrandModel.user_id == user_id)
                result = await session.execute(query)
                if brands := result.scalars().all():
                    return [
                        Brand(
                            user_id=user_id,
                            brand_name=brand.brand_name,
                            brand_logo_url=brand.brand_logo_url,
                            logo_obj_name=brand.logo_obj_name,
                            brand_desc=brand.brand_desc,
                            brand_slogan=brand.brand_slogan,
                            brand_audience=brand.brand_audience,
                            brand_color=brand.brand_color,
                            industry_name=brand.industry.industry_name,
                            industry_id=brand.industry_id,
                            tone_name=brand.tone.tone_name,
                            tone_id=brand.tone_id,
                            id=brand.id,
                        )
                        for brand in brands
                    ]
        except Exception as e:
            raise e

    @override
    async def insert(self, brand: Brand):
        try:
            async with self._sql_connection.session() as session:
                brand_exists = await self.__get_brand_by_name(
                    session=session, brand_name=brand.brand_name, user_id=brand.user_id
                )
                if brand_exists:
                    raise BrandExists("Brand already exists")
                brand_in_db = BrandModel(**brand.to_dict())
                session.add(brand_in_db)
                await session.commit()
                await session.refresh(brand_in_db)
                return brand
        except Exception as e:
            raise e

    @override
    async def update(
        self,
        brand_id: UUID,
        user_id: UUID,
        brand_name: str,
        brand_logo_url: str,
        brand_desc: str,
        brand_tone: UUID,
        brand_industry: UUID,
        brand_slogan: str,
        logo_obj_name: str,
        brand_audience: str,
        brand_color: str,
    ):

        try:
            async with self._sql_connection.session() as session:
                if brand := await self.__get_brand_by_id(session=session, brand_id=brand_id):
                    if brand.user_id != user_id:
                        raise BrandNotFound("Brand not found")
                    brand.brand_name = brand_name
                    brand.brand_logo_url = brand_logo_url
                    brand.logo_obj_name = logo_obj_name
                    brand.brand_desc = brand_desc
                    brand.brand_slogan = brand_slogan
                    brand.brand_audience = brand_audience
                    brand.brand_color = brand_color
                    brand.tone_id = brand_tone
                    brand.industry_id = brand_industry
                    await session.commit()
                    await session.refresh(brand)
                else:
                    raise BrandNotFound("Brand not found")
        except Exception as e:
            raise e

    @override
    async def delete(self, brand_id: UUID, user_id: UUID):
        try:
            async with self._sql_connection.session() as session:
                if brand := await self.__get_brand_by_id(session=session, brand_id=brand_id):
                    brand_obj_name = brand.logo_obj_name
                    if brand.user_id != user_id:
                        raise BrandNotFound("Brand not found")
                    await session.delete(brand)
                    await session.commit()
                    return brand_obj_name, True
                else:
                    raise BrandNotFound("Brand not found")
        except Exception as e:
            raise e

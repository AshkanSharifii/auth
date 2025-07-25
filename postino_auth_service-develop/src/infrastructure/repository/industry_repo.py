from typing import override
from uuid import UUID
from sqlalchemy import select

from src.ports.repositories.industry_repo import IBrandIndustryRepository
from src.infrastructure.database.postgresql_connection import ISQLConnection
from src.infrastructure.models.industry_model import IndustryModel
from src.domain.entities.industry import BrandIndustry
from src.domain.exceptions import IndustryNotFound


class IndustryRepository(IBrandIndustryRepository):
    """
    Repository implementation for managing brand industry entities in the database.

    Provides asynchronous methods for CRUD (Create, Read, Update, Delete) operations on
    brand industry entities using a SQLAlchemy database connection. Implements the
    `IBrandIndustryRepository` interface to ensure adherence to the defined contract.

    Attributes:
        _sql_connection (ISQLConnection): The database connection/session provider used for
            executing database operations.

    Methods:
        get_all: Retrieves all brand industries as a list of `BrandIndustry` objects.
        get_by_id: Retrieves a single brand industry by its UUID.
        insert: Inserts a new brand industry into the database.
        update: Updates an existing brand industry's name and description.
        delete: Deletes a brand industry by its UUID.

    Raises:
        IndustryNotFound: If an industry is not found during update or delete operations.
        Exception: For database access or query execution errors.
    """
        
    def __init__(self, sql_connection: ISQLConnection):
        self._sql_connection = sql_connection

    @override
    async def get_all(self) -> list[BrandIndustry]:
        async with self._sql_connection.session() as session:
            result = await session.execute(select(IndustryModel))
            industries = result.scalars().all()
            return [
                BrandIndustry(
                    id=industry.id,
                    industry_name=industry.industry_name,
                    industry_description=industry.industry_description,
                    industry_created_at=industry.industry_created_at
                )
                for industry in industries
            ]
    
    @override
    async def get_by_id(self, industry_id: UUID) -> BrandIndustry:
        async with self._sql_connection.session() as session:
            query = select(IndustryModel).where(IndustryModel.id == industry_id)
            result = await session.execute(query)
            if industry := result.scalars().one_or_none():
                return BrandIndustry(
                    id=industry.id,
                    industry_name=industry.industry_name,
                    industry_description=industry.industry_description,
                    industry_created_at=industry.industry_created_at
                )
            
    @override
    async def insert(self, industry: BrandIndustry) -> BrandIndustry:
        try:
            async with self._sql_connection.session() as session:
                industry_in_db = IndustryModel(**industry.to_dict())
                session.add(industry_in_db)
                await session.commit()
                industry = await session.refresh(industry_in_db)
                return BrandIndustry(
                    industry_name=industry_in_db.industry_name,
                    industry_description=industry_in_db.industry_description,
                    industry_created_at=industry_in_db.industry_created_at,
                    id=industry_in_db.id
                )
        except Exception as e:
            raise e

    @override
    async def update(self, industry_id: UUID, industry_name: str, industry_desc: str) -> BrandIndustry:
        async with self._sql_connection.session() as session:
            query = select(IndustryModel).where(IndustryModel.id == industry_id)
            result = await session.execute(query)
            if industry := result.scalars().one_or_none():
                industry.industry_name = industry_name
                industry.industry_description = industry_desc
                await session.commit()
                await session.refresh(industry)
                return BrandIndustry(
                    industry_name=industry.industry_name,
                    industry_description=industry.industry_description,
                    industry_created_at=industry.industry_created_at,
                    id=industry.id
                )
            else:
                raise IndustryNotFound('Industry not found')

    @override
    async def delete(self, industry_id: UUID) -> bool:
        async with self._sql_connection.session() as session:
            query = select(IndustryModel).where(IndustryModel.id == industry_id)
            result = await session.execute(query)
            if industry := result.scalars().one_or_none():
                    await session.delete(industry)
                    await session.commit()
                    return True
            else:
                raise IndustryNotFound('Industry not found')
            
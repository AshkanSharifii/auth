from typing import override
from uuid import UUID
from sqlalchemy import select

from src.ports.repositories.tone_repo import IBrandToneRepository
from src.infrastructure.database.postgresql_connection import ISQLConnection
from src.infrastructure.models.tone_model import ToneModel
from src.domain.entities.tone import BrandTone
from src.domain.exceptions import ToneNotFound


class BrandToneRepository(IBrandToneRepository):
    """
    Repository implementation for managing brand tone entities in the database.

    Provides asynchronous methods for CRUD (Create, Read, Update, Delete) operations on
    brand tone entities using a SQLAlchemy database connection. Implements the
    `IBrandToneRepository` interface to ensure adherence to the defined contract.

    Attributes:
        _sql_connection (ISQLConnection): The database connection/session provider used for
            executing database operations.

    Methods:
        get_all: Retrieves all brand tones as a list of `BrandTone` objects.
        get_by_id: Retrieves a single brand tone by its UUID.
        insert: Inserts a new brand tone into the database.
        update: Updates an existing brand tone's name and description.
        delete: Deletes a brand tone by its UUID.

    Raises:
        ToneNotFound: If a brand tone is not found during update or delete operations.
        Exception: For database access or query execution errors.
    """
    
    def __init__(self, sql_connection: ISQLConnection):
        self._sql_connection = sql_connection

    @override
    async def get_all(self) -> list[BrandTone]:
        async with self._sql_connection.session() as session:
            result = await session.execute(select(ToneModel))
            tones = result.scalars().all()
            return [
                BrandTone(
                    id=tone.id,
                    tone_name=tone.tone_name,
                    tone_description=tone.tone_description,
                    tone_created_at=tone.tone_created_at
                )
                for tone in tones
            ]
    
    @override
    async def get_by_id(self, tone_id: UUID) -> BrandTone:
        async with self._sql_connection.session() as session:
            query = select(ToneModel).where(ToneModel.id == tone_id)
            result = await session.execute(query)
            if tone := result.scalars().one_or_none():
                return BrandTone(
                    id=tone.id,
                    tone_name=tone.tone_name,
                    tone_description=tone.tone_description,
                    tone_created_at=tone.tone_created_at
                )
    
    @override
    async def insert(self, tone: BrandTone) -> BrandTone:
        try:
            async with self._sql_connection.session() as session:
                tone_in_db = ToneModel(**tone.to_dict())
                session.add(tone_in_db)
                await session.commit()
                await session.refresh(tone_in_db)
                return BrandTone(
                    tone_name=tone_in_db.tone_name,
                    tone_description=tone_in_db.tone_description,
                    tone_created_at=tone.tone_created_at,
                    id=tone_in_db.id
                )
        except Exception as e:
            raise e
    
    @override
    async def update(self, tone_id: UUID, tone_name: str, tone_desc: str) -> BrandTone:
        async with self._sql_connection.session() as session:
            query = select(ToneModel).where(ToneModel.id == tone_id)
            result = await session.execute(query)
            if tone := result.scalars().one_or_none():
                tone.tone_name = tone_name
                tone.tone_description = tone_desc
                await session.commit()
                await session.refresh(tone)
                return BrandTone(
                    tone_name=tone.tone_name,
                    tone_description=tone.tone_description,
                    tone_created_at=tone.tone_created_at,
                    id=tone.id
                )
            else:
                raise ToneNotFound('Tone not found')
    
    @override
    async def delete(self, tone_id: UUID) -> bool:
        async with self._sql_connection.session() as session:
            query = select(ToneModel).where(ToneModel.id == tone_id)
            result = await session.execute(query)
            if tone := result.scalars().one_or_none():
                await session.delete(tone)
                await session.commit()
                return True
            else:
                raise ToneNotFound('Tone not found')

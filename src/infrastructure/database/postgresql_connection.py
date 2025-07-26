import asyncio
from typing import (override,
                    AsyncGenerator)
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    AsyncSession,
                                    async_scoped_session)

from src.config import settings
from src.domain.interfaces.sql_connection import ISQLConnection


# ----------------------------------------------------------------------------
class PostgreSQLConnection(ISQLConnection):
    """
    Asynchronous PostgreSQL connection manager using SQLAlchemy.

    This class sets up an async SQLAlchemy engine and provides a scoped session factory.
    It implements the ISQLConnection interface, allowing other parts of the application
    to obtain database sessions in a safe and managed context.

    Attributes:
        _engine (AsyncEngine): The SQLAlchemy async engine.
        _async_session_factory (async_scoped_session): Scoped session factory based on asyncio tasks.
    """

    def __init__(self):
        self._engine = create_async_engine(str(settings.POSTGRES_DATABASE_URL),
                                           echo=False)
        self._async_session_factory = async_scoped_session(session_factory=sessionmaker(bind=self._engine,
                                                                                        expire_on_commit=False,
                                                                                        autocommit=False,
                                                                                        autoflush=False,
                                                                                        class_=AsyncSession),
                                                           scopefunc=asyncio.current_task)

    @override
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provides an asynchronous SQLAlchemy session within a context manager.

        Yields:
            AsyncSession: An active async session for performing database operations.

        Handles:
            - Rolls back the transaction in case of any exception.
            - Ensures the session is properly closed after use.

        Usage:
            async with postgres_connection.session() as session:
                # Use session for queries and transactions
        """
        session: AsyncSession = self._async_session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

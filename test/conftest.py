from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    AsyncSession,
                                    async_scoped_session)

from src.main import app
from src.di.container import Container
from src.domain.interfaces.sql_connection import ISQLConnection
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.presentation.rest.user.dependencies import get_current_user
from src.infrastructure.models.base_model import Base
from src.infrastructure.access_token.pyjwt_access_token import PyJWTAccessToken

from typing import AsyncGenerator, Any, override
from contextlib import asynccontextmanager
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from http import HTTPStatus
from datetime import timedelta

import fakeredis
import pytest_asyncio
import asyncio
import os
import time
import uuid


class TestDBConnection(ISQLConnection):
    def __init__(self):
        self._engine = create_async_engine(
            'sqlite+aiosqlite:///test_database.db',
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self._async_session_factory = async_scoped_session(
            sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
                class_=AsyncSession
            ),
            scopefunc=asyncio.current_task
        )

    async def _create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _drop_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session: AsyncSession = self._async_session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        await self._engine.dispose()


class TestRedisClient(ICacheClient):
    def __init__(self):
        self._r = fakeredis.aioredis.FakeRedis(decode_responses=True)

    async def store_code(self, key: str, value: str) -> Any:
        try:
            response = await self._r.set(name=key, value=value, ex=180, nx=True)
            return response
        except Exception as e:
            raise e

    async def retrieve_code(self, key: str) -> Any:
        try:
            value = await self._r.get(name=key)
            return value
        except Exception as e:
            raise e


class TestAsyncNotifyUser(INotifyUser):
    @override
    async def send_request(self, recipient: str, message: str, channel: str):
        response = MagicMock()
        response.status_code = HTTPStatus.OK
        return response


class FailingTestAsyncNotifyUser(INotifyUser):
    @override
    async def send_request(self, recipient: str, message: str, channel: str):
        response = MagicMock()
        response.status_code = HTTPStatus.FORBIDDEN
        return response


@pytest_asyncio.fixture(scope="session")
async def test_db():
    test_db = TestDBConnection()
    await test_db._create_all()
    yield test_db

    await test_db._drop_all()
    await test_db.close()

    try:
        await test_db._drop_all()
        await test_db.close()

        for _ in range(5):
            try:
                if os.path.exists("test_database.db"):
                    os.remove("test_database.db")
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            print("Warning: Could not delete test_database.db after retries")
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        raise


@pytest_asyncio.fixture
async def test_container(test_db):

    # override db
    container = Container()
    container.db_connection_provider.override(test_db)

    # override chace client
    fake_redis = TestRedisClient()
    container.cache_client_provider.override(fake_redis)

    container.wire(modules=[
        "src.presentation.rest.auth.router",
        "src.presentation.rest.user.router",
    ])

    yield container

    container.db_connection_provider.reset_override()
    container.cache_client_provider.reset_override()


@pytest_asyncio.fixture
async def client(test_container):
    app.container = test_container
    app.dependency_overrides[get_current_user] = lambda: {
        "phone_number": "+989170612747",
        "name": "user1",
        "family": "user1family",
        "latest_login": "2025-04-29T08:31:31.709000Z",
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_no_user(test_container):
    app.container = test_container

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()



def create_fake_access_token(sub: bool):
    pyjwt = PyJWTAccessToken()
    if sub:
        payload = {"sub": str(uuid.uuid4())}
    else:
        payload = {"test": "test"}
    not_exists_user_access_token = pyjwt.create_access_token(
        data=payload, expire_time=timedelta(minutes=10)
    )
    return not_exists_user_access_token

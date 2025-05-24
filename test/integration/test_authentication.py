from src.infrastructure.models.role_model import RoleModel
from src.infrastructure.models.user_model import UserModel
from src.application.utils.security import hash_password
from src.main import app

from ..conftest import create_fake_access_token

from fastapi.testclient import TestClient
from sqlalchemy.sql import text
from ..conftest import client, client_no_user, test_db, test_container, FailingTestAsyncNotifyUser, TestAsyncNotifyUser
from datetime import datetime, timedelta
import pytest
import uuid


# ------------------------------------------ route '/user/me'
@pytest.mark.asyncio
async def test_get_user_info_authenticated(client):
    
    response = await client.get('/user/me')
    assert response.status_code == 200
    assert response.json() == {
        "phone_number": "+989170612747",
        "name": "user1",
        "family": "user1family",
        "latest_login": "2025-04-29T08:31:31.709000Z",
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }


@pytest.mark.asyncio
async def test_get_user_info_not_authenticated():

    client = TestClient(app)
    
    response = client.get('/user/me')
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }


@pytest.mark.asyncio
async def test_get_user_info_authenticated_not_existed_user(client_no_user):

    headers = {
        'accept': 'application/json',
        'authorization': f'bearer {create_fake_access_token(sub=True)}',
    }
    
    response = await client_no_user.get('/user/me', headers=headers)

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found'}


@pytest.mark.asyncio
async def test_corrupted_access_token():

    client = TestClient(app)

    headers = {
        'accept': 'application/json',
        'authorization': f'bearer {create_fake_access_token(sub=False)}',
    }
    
    response = client.get('/user/me', headers=headers)

    assert response.status_code == 400
    assert response.json() == {'detail': "'sub'"}


# ------------------------------------------ route '/register'
@pytest.mark.asyncio
async def test_user_register_success(client, test_db, test_container):

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)
    
    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    payload = {
            "phone_number": "+989170001122",
            "name": "testname",
            "family": "testfamily",
            "password": "esi12345",
            "confirm_password": "esi12345"
        }

    try:
        response = await client.post('/register', json=payload)
        assert response.status_code == 201
        assert response.json() == {"phone_number": payload["phone_number"]}

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": f'{role_name}'}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()
            test_container.notify_user_provider.reset_override()


@pytest.mark.asyncio
async def test_user_register_user_already_exists(client, test_db):

    payload = {
        "phone_number": "+989170001122",
        "name": "testname",
        "family": "testfamily",
        "password": "esi12345",
        "confirm_password": "esi12345"
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name=payload["name"],
                           family=payload['family'],
                           hashed_password=payload["password"],
                           role_id=role.id,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/register', json=payload)

        assert response.status_code == 403
        assert response.json() == {"detail": f"User with phone number: {payload["phone_number"]} already exists"}

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_user_register_notification_service_not_available(client, test_db, test_container):

    role_name = 'user'

    failing_notif_service = FailingTestAsyncNotifyUser()
    test_container.notify_user_provider.override(failing_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    payload = {
        "phone_number": "+989170001122",
        "name": "testname",
        "family": "testfamily",
        "password": "esi12345",
        "confirm_password": "esi12345"
    }

    try:
        response = await client.post('/register', json=payload)
        
        assert response.status_code == 503
        assert response.json() == {'detail': 'Something went wrong'}


    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()
            test_container.notify_user_provider.reset_override()


# ------------------------------------------ route '/login/password'
@pytest.mark.asyncio
async def test_login_with_password_existed_user(client, test_db):

    payload = {
        'grant_type': 'password',
        'username': '+989170001122',
        'password': 'esi12345',
        'scope': '',
        'client_id': 'string',
        'client_secret': 'string'
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["username"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password(payload['password']),
                           role_id=role.id,
                           is_verified=True,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/login/password', data=payload)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()
        assert "role" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert response.json()["role"] == "user"
        assert response.json()["access_token"] != "" 

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload['username']}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_login_with_password_not_exist_user(client):
    payload = {
        'grant_type': 'password',
        'username': '+989170001121',
        'password': 'esi12345',
        'scope': '',
        'client_id': 'string',
        'client_secret': 'string'
    }

    response = await client.post('/login/password', data=payload)

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"User with phone number {payload['username']} not found"
    }


@pytest.mark.asyncio
async def test_login_with_password_existed_user_wrong_password(client, test_db):
    payload = {
        'grant_type': 'password',
        'username': '+989170001122',
        'password': 'esi123456',
        'scope': '',
        'client_id': 'string',
        'client_secret': 'string'
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["username"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('wrong_password'),
                           role_id=role.id,
                           is_verified=True,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/login/password', data=payload)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Phone number or password is incorrect"
        }

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload['username']}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_login_with_password_existed_user_not_verified(client, test_db):

    payload = {
        'grant_type': 'password',
        'username': '+989170001122',
        'password': 'esi12345',
        'scope': '',
        'client_id': 'string',
        'client_secret': 'string'
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["username"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password(payload['password']),
                           role_id=role.id,
                           is_verified=False,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:

        response = await client.post('/login/password', data=payload)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "User is not verified"
        }

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload['username']}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_login_with_password_existed_user_locked(client, test_db):

    payload = {
        'grant_type': 'password',
        'username': '+989170001122',
        'password': 'esi12345',
        'scope': '',
        'client_id': 'string',
        'client_secret': 'string'
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["username"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password(payload['password']),
                           role_id=role.id,
                           is_verified=False,
                            is_locked=True,
                           lock_expire_time=datetime.now() + timedelta(days=1),
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:

        response = await client.post('/login/password', data=payload)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "User is locked"
        }

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload['username']}'}
            )
            await session.commit()


# ------------------------------------------ route '/login/otp'
@pytest.mark.asyncio
async def test_login_with_otp_existed_user(client, test_db, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:    
        response = await client.post('/login/otp', json=payload)

        assert response.status_code == 200
        assert response.json() == True

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_login_with_otp_not_exist_user(client):
    payload = {
        'phone_number': '+989170001122'
    }

    response = await client.post('/login/otp', json=payload)

    assert response.status_code == 404
    assert response.json() == {'detail': f'User with phone number {payload["phone_number"]} not found'}


@pytest.mark.asyncio
async def test_login_with_otp_existed_user_otp_already_exists(client, test_db, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:    
        response = await client.post('/login/otp', json=payload)

        assert response.status_code == 200
        assert response.json() == True

        response = await client.post('/login/otp', json=payload)

        assert response.status_code == 403
        assert response.json() == {'detail': 'Verification code already exists'}

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_login_with_otp_existed_user_locked(client, test_db, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=True,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/login/otp', json=payload)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "User is locked"
        }

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_login_with_otp_notification_service_not_available(client, test_db, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = FailingTestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:    
        response = await client.post('/login/otp', json=payload)

        assert response.status_code == 503
        assert response.json() == {'detail': 'Something went wrong'}

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()
            

# ------------------------------------------ route '/code/resend'
@pytest.mark.asyncio
async def test_resend_code_exist_phone_number(client, test_db, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=True,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/code/resend', json=payload)
        assert response.status_code == 200
        assert response.json() == True

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_resend_code_not_exist_phone_number(client, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    response = await client.post('/code/resend', json=payload)
    assert response.status_code == 404
    assert response.json() == {
        "detail": f"User {payload["phone_number"]} not found"
    }


@pytest.mark.asyncio
async def test_resend_code_exist_phone_number_otp_already_exist(client, test_db, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=True,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/code/resend', json=payload)
        assert response.status_code == 200
        assert response.json() == True

        response = await client.post('/code/resend', json=payload)
        assert response.status_code == 403
        assert response.json() == {"detail": "Verification code already exist"}

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_resend_code_exist_phone_number_notification_service_not_available(client, test_db, test_container):
    payload = {
        'phone_number': '+989170001122'
    }

    role_name = 'user'

    fake_notif_service = FailingTestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=True,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/code/resend', json=payload)

        assert response.status_code == 503
        assert response.json() == {"detail": "Something went wrong"}

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


# ------------------------------------------ route '/code/submit'

@pytest.mark.asyncio
async def test_submit_code_not_exist_user(client):
    payload = {
        "phone_number": "+989170001122",
        "code": "2356"
    }

    response = await client.post('/code/submit', json=payload)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "User not found"
    }


@pytest.mark.asyncio
async def test_submit_exist_user_code_not_in_cache_client(client, test_db):
    payload = {
        "phone_number": "+989170001122",
        "code": "2356"
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=False,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:

        response = await client.post('/code/submit', json=payload)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Verification code expired"
        }

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_submit_exist_user_is_locked(client, test_db):
    payload = {
        "phone_number": "+989170001122",
        "code": "2356"
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=True,
                           lock_expire_time=datetime.now() + timedelta(days=1),
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:

        response = await client.post('/code/submit', json=payload)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "User is locked"
        }

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_submit_exist_user_wrong_code(client, test_db, test_container):
    payload = {
        "phone_number": "+989170001122",
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=False,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:

        response = await client.post('/code/resend', json=payload)

        assert response.status_code == 200
        assert response.json() == True

        payload.update({"code": "1234"})

        response = await client.post('/code/submit', json=payload)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Incorrect verification code"
        }

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_submit_exist_user_success(client, test_db, test_container):
    payload = {
        "phone_number": "+989170001122",
    }

    role_name = 'user'

    fake_notif_service = TestAsyncNotifyUser()
    test_container.notify_user_provider.override(fake_notif_service)

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["phone_number"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password('test12345'),
                           role_id=role.id,
                           is_verified=False,
                           is_locked=False,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:

        redis_client = test_container.cache_client_provider()
        await redis_client._r.flushall()

        response = await client.post('/code/resend', json=payload)

        assert response.status_code == 200
        assert response.json() == True

        code = await redis_client.retrieve_code(payload["phone_number"])
        payload.update({"code": str(code)})

        response = await client.post('/code/submit', json=payload)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()
        assert "role" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert response.json()["role"] == "user"
        assert response.json()["access_token"] != "" 

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload["phone_number"]}'}
            )
            await session.commit()


# ------------------------------------------ route '/refresh'
@pytest.mark.asyncio
async def test_refresh_token_success(client, test_db):
    
    payload = {
        'grant_type': 'password',
        'username': '+989170001122',
        'password': 'esi12345',
        'scope': '',
        'client_id': 'string',
        'client_secret': 'string'
    }

    role_name = 'user'

    async with test_db.session() as session:
        role = RoleModel(id=uuid.uuid4(), role_name=role_name)
        session.add(role)
        await session.commit()

    async with test_db.session() as session:
        user = UserModel(phone_number=payload["username"],
                           name='test-user',
                           family='test-user',
                           hashed_password=hash_password(payload['password']),
                           role_id=role.id,
                           is_verified=True,
                           id=uuid.uuid4())
        session.add(user)
        await session.commit()

    try:
        response = await client.post('/login/password', data=payload)

        assert response.status_code == 200
        assert "access_token" in response.json()

        refersh_token = response.json()['refresh_token']

        response = await client.post('/refresh', json={'refresh_token': refersh_token})

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()
        assert "role" in response.json()

    finally:
        async with test_db.session() as session:
            await session.execute(
                text("DELETE FROM Role WHERE role_name = :role_name"),
                {"role_name": role_name}
            )
            await session.execute(
                text("DELETE FROM User WHERE phone_number = :phone_number"),
                {"phone_number": f'{payload['username']}'}
            )
            await session.commit()

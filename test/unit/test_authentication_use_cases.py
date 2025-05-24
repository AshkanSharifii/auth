from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.get_current_user_use_case import GetCurrentUserUseCase
from src.application.use_cases.login_with_password_use_case import LoginWithPasswordUseCase
from src.application.use_cases.otp_login_use_case import OTPLoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.resend_code_use_case import ResendCodeUseCase
from src.application.use_cases.submit_verification_code_use_case import SubmitVerificationCodeUseCase


from src.domain.entities.user import User
from src.domain.entities.role import Role
from src.domain.exceptions import *

from src.application.utils.security import hash_password

from test.conftest import create_fake_access_token

from datetime import datetime, timedelta
from jwt.exceptions import ExpiredSignatureError
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

role = Role(id=1, role_name="user")


register_user = User(
        id=uuid4(),
        phone_number="+989170001122",
        name="test",
        family="test",
        role_id=role.id,
        hashed_password=hash_password('test12345'),
        is_locked=False,
        is_verified=False,
        login_retries=0,
        latest_login=None,
        lock_expire_time=None
    )

# ------------------------------------------ use case reigster
@pytest.mark.asyncio
async def test_register_user_success():

    mock_cache_client = AsyncMock()

    mock_user_repo = AsyncMock()
    mock_user_repo.insert.return_value = register_user
    mock_user_repo.get_by_phone_number.return_value = None

    mock_role_repo = AsyncMock()
    mock_role_repo.get_role_by_name.return_value = role

    mock_notify_user = AsyncMock()
    mock_notify_user.send_request.return_value.status_code = 200
    

    use_case = RegisterUserUseCase(
        user_repo=mock_user_repo,
        role_repo=mock_role_repo,
        notify_user=mock_notify_user,
        cache_client=mock_cache_client
    )

    result = await use_case.execute(
        phone_number=register_user.phone_number, 
        password=register_user.hashed_password, 
        name=register_user.name, 
        family=register_user.family
    )

    assert result == register_user
    mock_user_repo.get_by_phone_number.assert_called_once()
    mock_user_repo.insert.assert_called_once()
    mock_notify_user.send_request.assert_called_once()
    mock_cache_client.store_code.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_user_already_exists():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = MagicMock() # مقدار دهی لازم نیست

    use_case = RegisterUserUseCase(
        user_repo=mock_user_repo,
        role_repo=AsyncMock(),
        notify_user=AsyncMock(),
        cache_client=AsyncMock()
    )

    with pytest.raises(UserExist):
        await use_case.execute(
            phone_number=register_user.phone_number, 
            password=register_user.hashed_password, 
            name=register_user.name, 
            family=register_user.family
        )


@pytest.mark.asyncio
async def test_register_user_role_not_found():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = None

    mock_role_repo = AsyncMock()
    mock_role_repo.get_role_by_name.return_value = None

    use_case = RegisterUserUseCase(
        user_repo=mock_user_repo,
        role_repo=mock_role_repo,
        notify_user=AsyncMock(),
        cache_client=AsyncMock()
    )

    with pytest.raises(RoleNotFound):
        await use_case.execute(
            phone_number=register_user.phone_number, 
            password=register_user.hashed_password, 
            name=register_user.name, 
            family=register_user.family
        )


@pytest.mark.asyncio
async def test_register_user_sms_failed():

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = None
    mock_user_repo.insert.return_value = register_user

    mock_role_repo = AsyncMock()
    mock_role_repo.get_role_by_name.return_value = role

    mock_notify_user = AsyncMock()
    mock_notify_user.send_request.return_value.status_code = 500  # simulate failure

    use_case = RegisterUserUseCase(
        user_repo=mock_user_repo,
        role_repo=mock_role_repo,
        notify_user=mock_notify_user,
        cache_client=AsyncMock()
    )

    with pytest.raises(NotifyUserError):
        await use_case.execute(
            phone_number=register_user.phone_number, 
            password=register_user.hashed_password, 
            name=register_user.name, 
            family=register_user.family
        )


# ------------------------------------------ use case current user
@pytest.mark.asyncio
async def test_get_current_user():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_id.return_value = None

    mock_access_token = MagicMock()
    mock_access_token.decode_access_token.return_value = {'sub': str(uuid4())}

    token = create_fake_access_token(sub=True)

    use_case = GetCurrentUserUseCase(
        access_token=mock_access_token,
        user_repo=mock_user_repo
    )
    
    with pytest.raises(UserNotFound):
        await use_case.execute(token)


# ------------------------------------------ use case login with password
@pytest.mark.asyncio
async def test_user_login_with_success():
    mock_user_repo = AsyncMock()
    mock_access_token = MagicMock()
    mock_role_repo = AsyncMock()

    register_user.is_verified = True

    mock_user_repo.get_by_phone_number.return_value = register_user

    use_case = LoginWithPasswordUseCase(
        user_repo=mock_user_repo,
        access_token=mock_access_token,
        role_repo=mock_role_repo,
    )

    await use_case.execute(register_user.phone_number, 'test12345')

    mock_user_repo.get_by_phone_number.assert_called_once_with(phone_number=register_user.phone_number)
    mock_user_repo.update_user_login_status.assert_called_once_with(user_id=register_user.id, login=True)
    mock_access_token.create_access_token.assert_called_with(data={"sub": str(register_user.id)}, refresh_type=True)
    mock_role_repo.get_role_by_id.assert_called_once_with(role_id=register_user.role_id)


@pytest.mark.asyncio
async def test_user_login_user_not_found():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = None

    use_case = LoginWithPasswordUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
    )

    with pytest.raises(UserNotFound):
        await use_case.execute("09120000000", "test1234")


@pytest.mark.asyncio
async def test_user_login_user_locked_not_expired():
    locked_user = register_user
    locked_user.is_locked = True
    locked_user.lock_expire_time = datetime.now() + timedelta(minutes=5)

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = locked_user

    use_case = LoginWithPasswordUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
    )

    with pytest.raises(UserIsLocked):
        await use_case.execute(locked_user.phone_number, "test1234")


@pytest.mark.asyncio
async def test_user_login_not_verified():
    unverified_user = register_user
    unverified_user.is_verified = False

    unverified_user.is_locked = False
    unverified_user.lock_expire_time = None

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = unverified_user

    use_case = LoginWithPasswordUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
    )

    with pytest.raises(NotVerifiedUser):
        await use_case.execute(unverified_user.phone_number, "test1234")


@pytest.mark.asyncio
async def test_user_login_wrong_password():
    wrong_password_user = register_user
    wrong_password_user.is_verified = True

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = wrong_password_user

    use_case = LoginWithPasswordUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
    )

    with pytest.raises(CredentialError):
        await use_case.execute(wrong_password_user.phone_number, "wrong_password")



# ------------------------------------------ use case login with otp

@pytest.mark.asyncio
async def test_otp_login_success(monkeypatch):
    register_user.is_verified = True

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = register_user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = None

    mock_notify_user = AsyncMock()
    mock_notify_user.send_request.return_value.status_code = 200

    monkeypatch.setattr("src.application.use_cases.otp_login_use_case.generate_verification_code", lambda: "1234")
    monkeypatch.setattr("src.application.use_cases.otp_login_use_case.generate_message", lambda code: f"Your code is {code}")

    use_case = OTPLoginUseCase(
        user_repo=mock_user_repo,
        cache_client=mock_cache_client,
        notify_user=mock_notify_user,
    )

    result = await use_case.execute(register_user.phone_number)

    assert result is True
    mock_cache_client.store_code.assert_called_once_with(key=register_user.phone_number, value="1234")


@pytest.mark.asyncio
async def test_otp_login_user_not_found():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = None

    use_case = OTPLoginUseCase(
        user_repo=mock_user_repo,
        cache_client=AsyncMock(),
        notify_user=AsyncMock(),
    )

    with pytest.raises(UserNotFound):
        await use_case.execute(register_user.phone_number)


@pytest.mark.asyncio
async def test_otp_login_user_locked():
    user = MagicMock()
    user.is_locked = True

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = user

    use_case = OTPLoginUseCase(
        user_repo=mock_user_repo,
        cache_client=AsyncMock(),
        notify_user=AsyncMock(),
    )

    with pytest.raises(UserIsLocked):
        await use_case.execute(register_user)


@pytest.mark.asyncio
async def test_otp_login_code_already_exists():
    user = MagicMock()
    user.is_locked = False

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = "1234"

    use_case = OTPLoginUseCase(
        user_repo=mock_user_repo,
        cache_client=mock_cache_client,
        notify_user=AsyncMock(),
    )

    with pytest.raises(VerificationCodeExist):
        await use_case.execute(register_user)


@pytest.mark.asyncio
async def test_otp_login_notify_failed(monkeypatch):
    user = MagicMock()
    user.is_locked = False

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = None

    mock_notify_user = AsyncMock()
    mock_notify_user.send_request.return_value.status_code = 503

    monkeypatch.setattr("src.application.use_cases.otp_login_use_case.generate_verification_code", lambda: "1234")
    monkeypatch.setattr("src.application.use_cases.otp_login_use_case.generate_message", lambda code: f"Your code is {code}")

    use_case = OTPLoginUseCase(
        user_repo=mock_user_repo,
        cache_client=mock_cache_client,
        notify_user=mock_notify_user,
    )

    with pytest.raises(NotifyUserError):
        await use_case.execute(register_user.phone_number)


# ------------------------------------------ use case refresh

@pytest.mark.asyncio
async def test_refresh_token_success():
    user_id = uuid4()
    user = MagicMock()
    user.id = user_id
    user.role_id = 1

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_id.return_value = user

    mock_access_token = MagicMock()
    mock_access_token.decode_access_token.return_value = {'sub': str(user_id), 'type': 'refresh_token'}
    mock_access_token.create_access_token.return_value = "new.access.token"

    mock_role_repo = AsyncMock()
    mock_role_repo.get_role_by_id.return_value.role_name = "user"

    use_case = RefreshTokenUseCase(
        user_repo=mock_user_repo,
        access_token=mock_access_token,
        role_repo=mock_role_repo
    )

    result = await use_case.execute("valid.refresh.token")

    assert result == {
        'access_token': "new.access.token",
        'role': "user",
        'token_type': 'bearer'
    }
    mock_user_repo.update_user_login_status.assert_called_once_with(user_id=user_id, login=True)


@pytest.mark.asyncio
async def test_refresh_token_user_not_found():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_id.return_value = None

    mock_access_token = MagicMock()
    mock_access_token.decode_access_token.return_value = {'sub': str(uuid4()), 'type': 'refresh_token'}

    use_case = RefreshTokenUseCase(
        user_repo=mock_user_repo,
        access_token=mock_access_token,
        role_repo=AsyncMock()
    )

    with pytest.raises(UserNotFound):
        await use_case.execute("some.token")


@pytest.mark.asyncio
async def test_refresh_token_missing_type_field():
    mock_access_token = MagicMock()
    mock_access_token.decode_access_token.return_value = {'sub': str(uuid4())}

    use_case = RefreshTokenUseCase(
        user_repo=AsyncMock(),
        access_token=mock_access_token,
        role_repo=AsyncMock()
    )

    with pytest.raises(InvalidRefreshToken):
        await use_case.execute("token.without.type")


@pytest.mark.asyncio
async def test_refresh_token_wrong_type():
    mock_access_token = MagicMock()
    mock_access_token.decode_access_token.return_value = {'sub': str(uuid4()), 'type': 'access_token'}

    use_case = RefreshTokenUseCase(
        user_repo=AsyncMock(),
        access_token=mock_access_token,
        role_repo=AsyncMock()
    )

    with pytest.raises(InvalidRefreshToken):
        await use_case.execute("wrong.type.token")


@pytest.mark.asyncio
async def test_refresh_token_expired():
    mock_access_token = MagicMock()
    mock_access_token.decode_access_token.side_effect = ExpiredSignatureError()

    use_case = RefreshTokenUseCase(
        user_repo=AsyncMock(),
        access_token=mock_access_token,
        role_repo=AsyncMock()
    )

    with pytest.raises(ExpRefreshToken):
        await use_case.execute("expired.token")


# ------------------------------------------ use case login with otp

@pytest.mark.asyncio
async def test_resend_code_success():

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = register_user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = None 

    mock_notify_user = AsyncMock()
    mock_notify_user.send_request.return_value.status_code = 200

    use_case = ResendCodeUseCase(
        user_repo=mock_user_repo,
        cache_client=mock_cache_client,
        notify_user=mock_notify_user
    )

    result = await use_case.execute(register_user.phone_number)
    assert result is True

    mock_user_repo.get_by_phone_number.assert_called_once_with(phone_number=register_user.phone_number)
    mock_cache_client.store_code.assert_called_once()
    mock_notify_user.send_request.assert_called_once()


@pytest.mark.asyncio
async def test_resend_code_user_not_found():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = None

    use_case = ResendCodeUseCase(
        user_repo=mock_user_repo,
        cache_client=AsyncMock(),
        notify_user=AsyncMock()
    )

    with pytest.raises(UserNotFound):
        await use_case.execute(register_user.phone_number)


@pytest.mark.asyncio
async def test_resend_code_already_exists():
    user = MagicMock()
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = "1234"

    use_case = ResendCodeUseCase(
        user_repo=mock_user_repo,
        cache_client=mock_cache_client,
        notify_user=AsyncMock()
    )

    with pytest.raises(VerificationCodeExist):
        await use_case.execute(register_user.phone_number)


@pytest.mark.asyncio
async def test_resend_code_notify_failed():
    user = MagicMock()
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = None

    mock_notify_user = AsyncMock()
    mock_notify_user.send_request.return_value.status_code = 503

    use_case = ResendCodeUseCase(
        user_repo=mock_user_repo,
        cache_client=mock_cache_client,
        notify_user=mock_notify_user
    )

    with pytest.raises(NotifyUserError):
        await use_case.execute(register_user.phone_number)


# ------------------------------------------ use case submit code
@pytest.mark.asyncio
async def test_submit_verification_code_success():

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = register_user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = "1234"

    mock_access_token = MagicMock()
    mock_access_token.create_access_token.side_effect = ["access.token", "refresh.token"]

    mock_role_repo = AsyncMock()
    mock_role_repo.get_role_by_id.return_value = role

    use_case = SubmitVerificationCodeUseCase(
        user_repo=mock_user_repo,
        access_token=mock_access_token,
        role_repo=mock_role_repo,
        cache_client=mock_cache_client
    )

    result = await use_case.execute(register_user.phone_number, "1234")

    assert result == {
        "access_token": "access.token",
        "refresh_token": "refresh.token",
        "role": "user",
        "token_type": "bearer"
    }
    mock_user_repo.update_user_login_status.assert_called_once_with(user_id=register_user.id, login=True)


@pytest.mark.asyncio
async def test_submit_verification_code_user_not_found():
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = None

    use_case = SubmitVerificationCodeUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
        cache_client=AsyncMock()
    )

    with pytest.raises(UserNotFound):
        await use_case.execute(register_user.phone_number, "1234")


@pytest.mark.asyncio
async def test_submit_verification_code_user_locked():
    user = MagicMock()
    user.is_locked = True
    user.lock_expire_time = datetime.now() + timedelta(minutes=5)

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = user

    use_case = SubmitVerificationCodeUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
        cache_client=AsyncMock()
    )

    with pytest.raises(UserIsLocked):
        await use_case.execute("09120000000", "123456")


@pytest.mark.asyncio
async def test_submit_verification_code_expired():

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = register_user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = None

    use_case = SubmitVerificationCodeUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
        cache_client=mock_cache_client
    )

    with pytest.raises(VerificationCodeExpired):
        await use_case.execute(register_user.phone_number, "1234")


@pytest.mark.asyncio
async def test_submit_verification_code_incorrect():

    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_phone_number.return_value = register_user

    mock_cache_client = AsyncMock()
    mock_cache_client.retrieve_code.return_value = "1234"

    use_case = SubmitVerificationCodeUseCase(
        user_repo=mock_user_repo,
        access_token=MagicMock(),
        role_repo=AsyncMock(),
        cache_client=mock_cache_client
    )

    with pytest.raises(IncorrectVerificationCode):
        await use_case.execute(register_user.phone_number, "1236")
    
import secrets
import string
from passlib.context import CryptContext

from src.config import settings
from src.domain.entities.user import User
from src.domain.exceptions import UserIsLocked
from src.ports.repositories.user_repo import IUserRepository

# ----------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ----------------------------------------------------------------------------
def hash_password(password) -> str:
    return pwd_context.hash(password)


# ----------------------------------------------------------------------------
def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ----------------------------------------------------------------------------
def generate_verification_code() -> str:
    otp = ''.join(secrets.choice(string.digits) for _ in range(4))
    return otp


# ----------------------------------------------------------------------------
def generate_message(code: str) -> str:
    message = f"""
    پستینو
    کد تایید شما:{code}
    """
    return message

# ----------------------------------------------------------------------------
async def validate_user(user: User, user_repo: IUserRepository):
    if user.login_retries + 1 > settings.VALID_LOGIN_RETRIES:
        await user_repo.lock_user(user_id=user.id)
        raise UserIsLocked("User is locked")
    await user_repo.increase_login_attempts(user_id=user.id)

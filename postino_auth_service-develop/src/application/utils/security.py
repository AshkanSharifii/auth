import secrets
import string
from datetime import datetime, timedelta

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
    otp = "".join(secrets.choice(string.digits) for _ in range(4))
    return otp


# ----------------------------------------------------------------------------
async def validate_user(user: User, user_repo: IUserRepository):
    if user.login_retries + 1 > settings.VALID_LOGIN_RETRIES:
        await user_repo.update(
            user_id=user.id,
            user_new_data={
                "is_locket": True,
                "lock_expire_time": datetime.now() + timedelta(minutes=settings.LOCK_USER_MINUTES),
            },
        )
        raise UserIsLocked("User is locked")
    await user_repo.update(user_id=user.id, user_new_data={"login_retries": user.login_retries + 1})

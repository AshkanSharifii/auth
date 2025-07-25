import uuid
from datetime import datetime
from dataclasses import (dataclass,
                         field)

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class User(Base):
    """
    Domain entity representing a user within the application.

    Inherits from:
        Base: Provides utility methods like `from_dict` and `to_dict`.

    Attributes:
        phone_number (str): User's phone number used for identification and auth.
        name (str): User's first name.
        family (str): User's last name or surname.
        role_id (uuid.UUID): Unique identifier for the user's role or permissions group.
        latest_login (datetime | None): Datetime of the user's most recent auth. Optional.
        login_retries (int): Count of consecutive failed auth attempts.
        is_locked (bool): Whether the user's account is currently locked.
        lock_expire_time (datetime | None): When the lock on the account will expire. Optional.
        id (uuid.UUID): Unique user identifier. Automatically generated if not provided.
    """

    phone_number: str
    name: str
    family: str
    hashed_password: str
    role_id: uuid.UUID
    is_verified: bool = False
    latest_login: datetime | None = None
    login_retries: int = 0
    is_locked: bool = False
    lock_expire_time: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

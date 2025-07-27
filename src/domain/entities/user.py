import uuid
from datetime import datetime
from dataclasses import dataclass, field

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class User(Base):
    """
    Domain entity representing a user within the application.
    Simplified for email-only authentication system.

    Inherits from:
        Base: Provides utility methods like `from_dict` and `to_dict`.

    Attributes:
        email (str): User's email address (primary identifier and authentication method).
        name (str): User's first name.
        family (str): User's last name or surname.
        hashed_password (str): Hashed password for authentication.
        role_id (uuid.UUID): Unique identifier for the user's role or permissions group.
        position (str): User's job position/title.
        personal_code (str): Unique personal identifier.
        phone_number (str | None): User's phone number (optional, for contact only).
        is_verified (bool): Whether the user's account is verified.
        email_verified (bool): Whether the email is verified.
        phone_number_verified (bool): Whether the phone number is verified (optional).
        latest_login (datetime | None): Datetime of the user's most recent auth.
        login_retries (bool): Whether user has failed login attempts.
        lock_expire_time (datetime | None): When the lock on the account will expire.
        is_locked (bool): Whether the user's account is currently locked.
        is_active (bool): Whether the user's account is active.
        id (uuid.UUID): Unique user identifier. Automatically generated if not provided.
    """

    email: str
    name: str
    family: str
    hashed_password: str
    role_id: uuid.UUID
    position: str
    personal_code: str
    phone_number: str | None = None
    is_verified: bool = False
    email_verified: bool = False
    phone_number_verified: bool = False
    latest_login: datetime | None = None
    login_retries: bool = False
    lock_expire_time: datetime | None = None
    is_locked: bool = False
    is_active: bool = False
    id: uuid.UUID = field(default_factory=uuid.uuid4)
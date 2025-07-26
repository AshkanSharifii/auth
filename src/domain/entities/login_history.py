import uuid
from datetime import datetime
from dataclasses import dataclass, field

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class LoginHistory(Base):
    """
    Domain entity representing a user login history record.

    Attributes:
        user_id (uuid.UUID): The ID of the user who logged in.
        login_time (datetime): When the login occurred.
        ip_address (str): IP address from which login occurred.
        user_agent (str): Browser/device information.
        login_method (str): Method used for login (password, otp, etc.).
        success (bool): Whether the login attempt was successful.
        failure_reason (str | None): Reason for failure if login was unsuccessful.
        id (uuid.UUID): Unique identifier for the login record.
    """
    user_id: uuid.UUID
    login_time: datetime
    ip_address: str
    user_agent: str
    login_method: str
    success: bool
    failure_reason: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
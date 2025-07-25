import uuid
from dataclasses import (dataclass, field)

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class Permission(Base):
    """
    Represents a permission entity within the system.

    Attributes:
        title (str): A descriptive title of the permission, such as "create_user" or "view_reports".
        permission_code (int): Numeric code for the permission.
        id (uuid.UUID): A unique identifier for the permission. Automatically generated if not provided.
    """
    title: str
    permission_code: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)
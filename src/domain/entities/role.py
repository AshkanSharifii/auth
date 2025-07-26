import uuid
from dataclasses import (dataclass, field)

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class Role(Base):
    """
    Domain entity representing a user role in the system.

    Inherits from:
        Base: Provides utility methods for serialization and deserialization.

    Attributes:
        role_name (str): Name of the role (e.g., "super_admin", "admin", "manager", "expert", "employee", "user", "guest").
        id (uuid.UUID): Unique identifier for the role. Automatically generated.
    """
    role_name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
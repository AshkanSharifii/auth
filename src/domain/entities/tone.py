import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class BrandTone(Base):
    """
    Domain entity representing a brand tone in the system.

    Inherits from:
        Base: Provides utility methods for serialization and deserialization.

    Attributes:
        tone_name (str): Name of the brand tone (e.g., "professional", "casual").
        tone_description (str): Description of the brand tone.
        tone_created_at (datetime): Timestamp when the brand tone was created.
        id (uuid.UUID): Unique identifier for the brand tone. Automatically generated.
    """
    tone_name: str
    tone_description: str
    tone_created_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    
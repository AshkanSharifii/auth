import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class BrandIndustry(Base):
    """
    Domain entity representing a brand industry in the system.

    Inherits from:
        Base: Provides utility methods for serialization and deserialization.

    Attributes:
        industry_name (str): Name of the industry (e.g., "tech", "finance").
        industry_description (str): Description of the industry.
        industry_created_at (datetime): Timestamp when the industry was created.
        id (uuid.UUID): Unique identifier for the industry. Automatically generated.
    """
    industry_name: str
    industry_description: str
    industry_created_at: datetime
    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

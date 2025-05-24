import uuid
from dataclasses import dataclass, field

from src.domain.entities.base import Base


# ----------------------------------------------------------------------------
@dataclass
class Brand(Base):
    """
    Represents a brand entity associated with a user.

    Attributes:
        brand_name (str): The name of the brand.
        logo_obj_name (str): The object name of the brand logo.
        brand_desc (str | None): Description of the brand.
        brand_slogan (str | None): Slogan of the brand.
        brand_audience (str | None): Target audience of the brand.
        brand_color (str | None): Primary color of the brand.
        user_id (uuid.UUID): The unique identifier of the user who owns the brand.
        industry_id (uuid.UUID): The industry associated with the brand.
        tone_id (uuid.UUID): The tone associated with the brand.
        brand_logo_url (str | None): Optional URL to the brand's logo image.
        id (uuid.UUID): Unique identifier for the brand. Automatically generated if not provided.
    """

    brand_name: str

    brand_logo_url: str
    logo_obj_name: str

    user_id: uuid.UUID

    industry_name: str
    industry_id: uuid.UUID

    tone_name: str
    tone_id: uuid.UUID

    brand_desc: str | None = None
    brand_slogan: str | None = None
    brand_audience: str | None = None
    brand_color: str | None = None

    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

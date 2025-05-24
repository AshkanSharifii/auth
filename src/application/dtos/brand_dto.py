from uuid import UUID

from pydantic import BaseModel


# ----------------------------------------------------------------------------
class BrandBaseDTO(BaseModel):
    brand_name: str


# ----------------------------------------------------------------------------
class BrandDTO(BrandBaseDTO):
    id: UUID
    brand_logo_url: str | None = None
    user_id: UUID

# ----------------------------------------------------------------------------

class CreateUpdateBrandDTO(BaseModel):
    brand_name: str
    brand_logo_url: str

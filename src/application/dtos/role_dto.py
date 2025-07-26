from uuid import UUID
from pydantic import BaseModel


# ----------------------------------------------------------------------------
class RoleBaseDTO(BaseModel):
    role_name: str


# ----------------------------------------------------------------------------
class RoleDTO(RoleBaseDTO):
    id: UUID
from uuid import UUID
from pydantic import BaseModel


# ----------------------------------------------------------------------------
class PermissionBaseDTO(BaseModel):
    title: str
    permission_code: int


# ----------------------------------------------------------------------------
class PermissionDTO(PermissionBaseDTO):
    id: UUID

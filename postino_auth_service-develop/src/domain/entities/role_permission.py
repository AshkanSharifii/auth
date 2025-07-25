import uuid
from dataclasses import dataclass


# ----------------------------------------------------------------------------
@dataclass
class RolePermission:
    role_id: uuid.UUID
    permission_id: uuid.UUID

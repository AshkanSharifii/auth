from sqlalchemy import (Column,
                        String)
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import Base


# ----------------------------------------------------------------------------
class RoleModel(Base):
    __tablename__ = 'Role'

    role_name = Column(String, index=True, unique=True)

    users = relationship("UserModel", back_populates="role")

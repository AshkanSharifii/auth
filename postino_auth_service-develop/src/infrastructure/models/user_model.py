from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import Base


# ----------------------------------------------------------------------------
class UserModel(Base):
    __tablename__ = "User"

    phone_number = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    family = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    login_retries = Column(Integer, default=0)
    latest_login = Column(DateTime, nullable=True)
    is_locked = Column(Boolean, default=False)
    lock_expire_time = Column(DateTime, nullable=True)

    role_id = Column(UUID(as_uuid=True), ForeignKey("Role.id"), nullable=False)
    role = relationship("RoleModel", back_populates="users")

    brands = relationship("BrandModel", back_populates="user")

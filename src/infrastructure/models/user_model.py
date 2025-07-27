from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import Base


# ----------------------------------------------------------------------------
class UserModel(Base):
    __tablename__ = "User"

    # Primary authentication (required)
    email = Column(String, nullable=False, unique=True, index=True)

    # Optional contact information
    phone_number = Column(String, nullable=True, index=True)

    # User information
    name = Column(String, nullable=False)
    family = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    position = Column(String, nullable=False)
    personal_code = Column(String, nullable=False, unique=True, index=True)

    # Verification flags
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_number_verified = Column(Boolean, default=False)  # Optional

    # Login and security
    latest_login = Column(DateTime, nullable=True)
    login_retries = Column(Boolean, default=False)
    lock_expire_time = Column(DateTime, nullable=True)
    is_locked = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)

    # Role relationship
    role_id = Column(UUID(as_uuid=True), ForeignKey("Role.id"), nullable=False)
    role = relationship("RoleModel", back_populates="users")

    # Login history relationship
    login_histories = relationship("LoginHistoryModel", back_populates="user")
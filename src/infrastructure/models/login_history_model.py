from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import Base


# ----------------------------------------------------------------------------
class LoginHistoryModel(Base):
    __tablename__ = "LoginHistory"

    user_id = Column(UUID(as_uuid=True), ForeignKey("User.id"), nullable=False, index=True)
    login_time = Column(DateTime, nullable=False, index=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(Text, nullable=False)
    login_method = Column(String, nullable=False)  # 'password', 'otp', etc.
    success = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(String, nullable=True)

    # Relationship to user
    user = relationship("UserModel", back_populates="login_histories")
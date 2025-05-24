from sqlalchemy import TIMESTAMP, Column, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.infrastructure.models.base_model import Base


class IndustryModel(Base):
    __tablename__ = "BrandIndustry"

    industry_name = Column(String(100), nullable=False, unique=True)
    industry_description = Column(Text, nullable=True)
    industry_created_at = Column(TIMESTAMP, default=func.now())

    brands = relationship("BrandModel", back_populates="industry")

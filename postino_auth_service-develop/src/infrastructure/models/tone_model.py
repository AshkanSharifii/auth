from sqlalchemy import TIMESTAMP, Column, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.infrastructure.models.base_model import Base


class ToneModel(Base):
    __tablename__ = "BrandTone"

    tone_name = Column(String(100), nullable=False, unique=True)
    tone_description = Column(Text, nullable=True)
    tone_created_at = Column(TIMESTAMP, default=func.now())

    brands = relationship("BrandModel", back_populates="tone")

from sqlalchemy import UUID, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import Base


# ----------------------------------------------------------------------------
class BrandModel(Base):
    __tablename__ = "Brand"

    brand_name = Column(String, nullable=False)
    brand_logo_url = Column(String)
    logo_obj_name = Column(String)
    brand_desc = Column(Text)
    brand_slogan = Column(String, nullable=True)
    brand_audience = Column(String, nullable=True)
    brand_color = Column(String, nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("User.id"), index=True, nullable=False)
    user = relationship("UserModel", back_populates="brands")

    industry = relationship("IndustryModel", back_populates="brands", lazy="selectin")
    industry_id = Column(
        UUID(as_uuid=True), ForeignKey("BrandIndustry.id"), index=True, nullable=False
    )

    tone = relationship("ToneModel", back_populates="brands", lazy="selectin")
    tone_id = Column(UUID(as_uuid=True), ForeignKey("BrandTone.id"), index=True, nullable=False)

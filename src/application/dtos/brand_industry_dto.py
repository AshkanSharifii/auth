from pydantic import BaseModel

from typing import Optional


class BarndIndustryDto(BaseModel):
    name: str
    description: Optional[str]

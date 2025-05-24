from pydantic import BaseModel

from typing import Optional


class BarndToneDto(BaseModel):
    name: str
    description: Optional[str]

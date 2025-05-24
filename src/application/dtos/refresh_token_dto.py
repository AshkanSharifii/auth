from pydantic import BaseModel


class RefreshTokenDTO(BaseModel):
    refresh_token: str


class RefreshTokenOutDTO(BaseModel):
    access_token: str
    token_type: str
    role: str
    
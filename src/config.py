import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ----------------------------------------------------------------------------
load_dotenv()


# ----------------------------------------------------------------------------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore"  # This allows extra fields like APP_ENV
    )

    # Security
    VALID_LOGIN_RETRIES: int = 3
    LOCK_USER_MINUTES: int = 10

    # Database Config
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int

    POSTGRES_DATABASE_URL: PostgresDsn | None = None

    # Access token
    TOKEN_SECRET_KEY: str
    TOKEN_ALGORITHM: str
    TOKEN_EXPIRE_HOURS: int
    REFRESH_TOKEN_EXPIRE_HOURS: int

    # Redis Config (NEEDED FOR VERIFICATION CODES)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_KEY_EXPIRE_SECONDS: int = 300

    # Notification Service (NEEDED FOR SMS/EMAIL)
    NOTIFICATION_SERVICE_URL: str

    @field_validator("POSTGRES_DATABASE_URL", mode="after")
    def assemble_postgresql_url(cls, v: Optional[str], values: ValidationInfo):
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.data["DATABASE_USER"],
            password=values.data["DATABASE_PASSWORD"],
            host=values.data["DATABASE_HOST"],
            port=int(values.data["DATABASE_PORT"]),
            path=values.data["DATABASE_NAME"],
        )


# ----------------------------------------------------------------------------
class DevSettings(Settings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env.dev",
        extra="ignore"
    )


# ----------------------------------------------------------------------------
class ProdSettings(Settings):
    model_config = SettingsConfigDict(extra="ignore")


# ----------------------------------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    configs = {"dev": DevSettings, "prod": ProdSettings}
    get_config = configs.get(os.getenv("APP_ENV", "dev"))
    return get_config()


# ----------------------------------------------------------------------------
settings = get_settings()
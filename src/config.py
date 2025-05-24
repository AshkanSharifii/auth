import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from functools import lru_cache
from pydantic import (PostgresDsn,
                      field_validator,
                      ValidationInfo)
from pydantic_settings import (BaseSettings,
                               SettingsConfigDict)

# ----------------------------------------------------------------------------
load_dotenv()


# ----------------------------------------------------------------------------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True,
                                      env_file_encoding='utf-8')
    # Security
    VALID_LOGIN_RETRIES: int = 3
    LOCK_USER_MINUTES: int = 10

    # Database Config
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str

    POSTGRES_DATABASE_URL: PostgresDsn | None = None

    # Redis
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: str
    REDIS_KEY_EXPIRE_SECONDS: int

    # Access token
    TOKEN_SECRET_KEY: str
    TOKEN_ALGORITHM: str
    TOKEN_EXPIRE_HOURS: int
    REFRESH_TOKEN_EXPIRE_HOURS: int

    # Inter-service communication
    NOTIFICATION_SERVICE_URL: str

    # Object storage credentials
    OBJECT_STORAGE_ACCESS_KEY: str
    OBJECT_STORAGE_SECRET_KEY: str
    OBJECT_STORAGE_ENDPOINT_URL: str

    @field_validator('POSTGRES_DATABASE_URL',mode='after')
    def assemble_postgresql_url(cls, v: Optional[str], values: ValidationInfo):
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme='postgresql+asyncpg',
            username=values.data["DATABASE_USER"],
            password=values.data["DATABASE_PASSWORD"],
            host=values.data["DATABASE_HOST"],
            port=int(values.data["DATABASE_PORT"]),
            path=values.data["DATABASE_NAME"]
        )


# ----------------------------------------------------------------------------
class DevSettings(Settings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env.dev")


# ----------------------------------------------------------------------------
class ProdSettings(Settings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env.prod")


# ----------------------------------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    configs = {'dev': DevSettings,
               'prod': ProdSettings}
    get_config = configs.get(os.getenv('APP_ENV', 'dev'))
    return get_config()


# ----------------------------------------------------------------------------
settings = get_settings()

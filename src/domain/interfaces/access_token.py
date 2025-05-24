from uuid import UUID
from typing import Optional
from datetime import timedelta
from abc import ABC, abstractmethod


# ----------------------------------------------------------------------------
class IAccessToken(ABC):
    @abstractmethod
    def create_access_token(self, data: dict, expire_time: Optional[timedelta] = None, refresh_type: Optional[bool] = False) -> str:
        ...

    @abstractmethod
    def decode_access_token(self, access_token: str) -> dict:
        ...

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional


# ----------------------------------------------------------------------------
class IAccessToken(ABC):
    @abstractmethod
    def create_access_token(
        self,
        data: dict,
        expire_time: Optional[timedelta] = None,
        refresh_type: Optional[bool] = False,
    ) -> str: ...

    @abstractmethod
    def decode_access_token(self, access_token: str, check_type: bool = True) -> dict: ...

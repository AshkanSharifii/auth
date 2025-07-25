from abc import (ABC,
                 abstractmethod)
from typing import Any


# ----------------------------------------------------------------------------
class ICacheClient(ABC):
    @abstractmethod
    def store_code(self, key: str, value: str) -> Any:
        ...

    @abstractmethod
    def retrieve_code(self, key: str) -> Any:
        ...

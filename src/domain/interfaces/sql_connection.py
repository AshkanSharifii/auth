from abc import ABC, abstractmethod


# ----------------------------------------------------------------------------
class ISQLConnection(ABC):
    @abstractmethod
    def session(self):
        raise NotImplementedError

from abc import (ABC,
                 abstractmethod)


# ----------------------------------------------------------------------------
class INotifyUser(ABC):
    @abstractmethod
    def send_request(self, recipient: str, message: str, channel: str):
        ...

from abc import ABC, abstractmethod


# ----------------------------------------------------------------------------
class INotifyUser(ABC):
    """
    Interface for user notification services.
    Simplified for email-only notification system.
    """

    @abstractmethod
    async def send_email_otp(self, email: str, otp: str):
        """
        Send OTP via email.

        Args:
            email (str): The recipient's email address.
            otp (str): The OTP code to send.
        """
        ...
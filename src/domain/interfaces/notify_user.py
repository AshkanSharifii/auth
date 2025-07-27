from abc import ABC, abstractmethod


# ----------------------------------------------------------------------------
class INotifyUser(ABC):
    """
    Interface for user notification services.
    Simplified for email-only notification system with password reset support.
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

    @abstractmethod
    async def send_password_reset_email(self, email: str, otp: str, user_name: str = None):
        """
        Send password reset code via email.

        Args:
            email (str): The recipient's email address.
            otp (str): The password reset code to send.
            user_name (str, optional): The user's name for personalization.
        """
        ...
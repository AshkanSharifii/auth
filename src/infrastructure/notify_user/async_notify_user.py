from typing import override

import httpx

from src.config import settings
from src.domain.exceptions import NotifyUserError
from src.domain.interfaces.notify_user import INotifyUser


# ----------------------------------------------------------------------------
class AsyncNotifyUser(INotifyUser):
    """
    Email-only implementation of the INotifyUser interface.

    This class sends email notifications to users via an external notification service.
    Simplified for email-only OTP delivery system.
    """

    def __init__(self):
        self.__notification_service_url = settings.NOTIFICATION_SERVICE_URL

    @override
    async def send_email_otp(self, email: str, otp: str):
        """
        Sends an OTP code via email to the specified email address.

        Args:
            email (str): The recipient's email address.
            otp (str): The OTP code to send.

        Returns:
            httpx.Response: The HTTP response returned by the email service.

        Raises:
            NotifyUserError: If there is a network error, a non-successful HTTP status,
                             or any unexpected issue during the request.
        """
        payload = {
            "email": email,
            "otp": otp,
            "subject": "Your Verification Code - Postino",
            "template": "otp_verification",
            "sender_name": settings.EMAIL_FROM_NAME,
            "sender_email": settings.EMAIL_FROM_ADDRESS
        }

        try:
            async with httpx.AsyncClient(timeout=settings.EMAIL_SERVICE_TIMEOUT) as client:
                response = await client.post(
                    f"{self.__notification_service_url}/email/send/otp",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Postino-Auth-Service/1.0"
                    }
                )
                # Check for HTTP errors (4xx, 5xx)
                response.raise_for_status()
                return response

        except httpx.RequestError as e:
            # Catch network-related errors (e.g., connection issues, timeouts)
            raise NotifyUserError(f"Network error while sending email notification: {str(e)}")
        except httpx.HTTPStatusError as e:
            # Catch HTTP errors (non-2xx responses)
            raise NotifyUserError(f"Email service returned an error: HTTP {e.response.status_code}")
        except Exception as e:
            # Catch any other unexpected errors
            raise NotifyUserError(f"Unexpected error occurred while sending email: {str(e)}")
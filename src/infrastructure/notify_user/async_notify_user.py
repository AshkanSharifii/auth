import httpx
from typing import override

from src.config import settings
from src.domain.exceptions import NotifyUserError
from src.domain.interfaces.notify_user import INotifyUser


# ----------------------------------------------------------------------------
class AsyncNotifyUser(INotifyUser):
    """
    Asynchronous implementation of the INotifyUser interface using HTTPX.

    This class sends notifications to users via an external notification service.
    It supports different channels such as SMS, email, or others as configured.

    Attributes:
        __api_key (str): API key used to authenticate with the notification service.
        __notification_service_url (str): Base URL of the notification service endpoint.
    """

    def __init__(self):
        self.__notification_service_url = settings.NOTIFICATION_SERVICE_URL

    @override
    async def send_request(self, recipient: str, message: str, channel: str):
        """
        Sends a notification request to the external notification service.

        Args:
            recipient (str): The recipient identifier (e.g., phone number or email).
            message (str): The content of the message to send.
            channel (str): The channel through which the message should be sent (e.g., 'sms').

        Returns:
            httpx.Response: The HTTP response returned by the notification service.

        Raises:
            NotifyUserError: If there is a network error, a non-successful HTTP status,
                             or any unexpected issue during the request.
        """
        payload = {
            "recipient": recipient,
            "message": message,
            "channel": channel
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.__notification_service_url}/",
                    json=payload
                )
                # Check for HTTP errors (4xx, 5xx)
                response.raise_for_status()
                return response
        except httpx.RequestError as e:
            # Catch network-related errors (e.g., connection issues, timeouts)
            raise NotifyUserError(f"An error occurred while sending the notification: {str(e)}")
        except httpx.HTTPStatusError as e:
            # Catch HTTP errors (non-2xx responses)
            raise NotifyUserError(f"Notification service returned an error: {str(e)}")
        except Exception as e:
            # Catch any other unexpected errors
            raise NotifyUserError(f"Unexpected error occurred: {str(e)}")

from src.application.utils.security import generate_verification_code
from src.domain.exceptions import NotifyUserError, UserIsLocked, UserNotFound, VerificationCodeExist
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class OTPLoginUseCase:
    """
    Use case for email OTP authentication.

    Simplified for email-only OTP system:
    - Send OTP to email address
    - Cache OTP for verification
    - Handle user validation
    """

    def __init__(
            self, user_repo: IUserRepository, cache_client: ICacheClient, notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._notify_user = notify_user
        self._cache_client = cache_client

    async def execute(self, email: str) -> dict:
        """
        Send OTP to email address for authentication.

        Args:
            email (str): The user's email address.

        Returns:
            dict: Success message with OTP delivery confirmation.

        Raises:
            UserNotFound: If no user is associated with the email.
            UserIsLocked: If the user account is locked.
            VerificationCodeExist: If a valid OTP already exists.
            NotifyUserError: If sending the email fails.
        """
        try:
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

            if user.is_locked:
                raise UserIsLocked("User account is temporarily locked")

            # Check if OTP already exists
            cache_key = f"email_otp_{email}"
            code_exists = await self._cache_client.retrieve_code(key=cache_key)
            if code_exists:
                raise VerificationCodeExist("OTP already sent to this email address")

            # Generate and send OTP
            code = generate_verification_code()
            response = await self._notify_user.send_email_otp(email=email, otp=code)

            if response.status_code == 200:
                await self._cache_client.store_code(key=cache_key, value=code)
                return {
                    "success": True,
                    "message": f"OTP sent to email {email}",
                    "method": "email",
                    "email": email
                }
            else:
                raise NotifyUserError("Failed to send email OTP")
        except Exception as e:
            raise e
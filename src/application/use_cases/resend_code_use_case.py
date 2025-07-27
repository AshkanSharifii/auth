from src.application.utils.security import generate_verification_code
from src.domain.exceptions import NotifyUserError, UserNotFound, VerificationCodeExist
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class ResendCodeUseCase:
    """
    Use case for resending verification codes via email.

    Simplified for email-only verification system.
    """

    def __init__(
            self, user_repo: IUserRepository, cache_client: ICacheClient, notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._cache_client = cache_client
        self._notify_user = notify_user

    async def execute_email_otp(self, email: str) -> dict:
        """
        Resend OTP for email login.

        Args:
            email (str): The user's email address.

        Returns:
            dict: Success response with details.

        Raises:
            UserNotFound: If no user found with the email.
            VerificationCodeExist: If a verification code already exists.
            NotifyUserError: If email sending fails.
        """
        try:
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

            # Check if OTP already exists
            cache_key = f"email_otp_{email}"
            code_exist = await self._cache_client.retrieve_code(key=cache_key)
            if code_exist:
                raise VerificationCodeExist("OTP already exists. Please wait before requesting a new one.")

            # Generate and send new OTP
            code = generate_verification_code()
            response = await self._notify_user.send_email_otp(email=email, otp=code)

            if response.status_code == 200:
                await self._cache_client.store_code(key=cache_key, value=code)
                return {
                    "success": True,
                    "message": f"OTP resent to email {email}",
                    "method": "email",
                    "email": email
                }
            else:
                raise NotifyUserError("Failed to send email OTP")
        except Exception as e:
            raise e

    async def execute_email_verification(self, email: str) -> dict:
        """
        Resend verification code for email verification (registration).

        Args:
            email (str): The user's email address.

        Returns:
            dict: Success response with details.
        """
        try:
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

            # Check if verification code already exists
            cache_key = f"email_verification_{email}"
            code_exist = await self._cache_client.retrieve_code(key=cache_key)
            if code_exist:
                raise VerificationCodeExist(
                    "Verification code already exists. Please wait before requesting a new one.")

            # Generate and send new verification code
            code = generate_verification_code()
            response = await self._notify_user.send_email_otp(email=email, otp=code)

            if response.status_code == 200:
                await self._cache_client.store_code(key=cache_key, value=code)
                return {
                    "success": True,
                    "message": f"Verification code resent to email {email}",
                    "method": "email",
                    "email": email
                }
            else:
                raise NotifyUserError("Failed to send verification email")
        except Exception as e:
            raise e
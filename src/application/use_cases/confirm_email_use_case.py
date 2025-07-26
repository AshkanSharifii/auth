from src.application.utils.security import generate_verification_code
from src.domain.exceptions import NotifyUserError, UserNotFound, VerificationCodeExist
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class ConfirmEmailUseCase:
    """
    Use case for confirming user email verification.

    This class handles the email confirmation process, including:
    - Verifying that the user exists.
    - Generating and sending a verification code to the user's email.
    - Caching the verification code for later validation.

    Dependencies:
        user_repo (IUserRepository): Interface to access user data.
        cache_client (ICacheClient): Interface to manage cached verification codes.
        notify_user (INotifyUser): Interface to send email notifications.

    Methods:
        execute(email: str) -> bool:
            Orchestrates the email verification process by sending a code and caching it.
    """

    def __init__(
            self, user_repo: IUserRepository, cache_client: ICacheClient, notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._notify_user = notify_user
        self._cache_client = cache_client

    async def execute(self, email: str) -> bool:
        """
        Initiates the email verification process for the given email address.

        Args:
            email (str): The user's email address to verify.

        Returns:
            bool: True if the verification code was successfully sent and cached.

        Raises:
            UserNotFound: If no user is associated with the provided email.
            VerificationCodeExist: If a valid verification code already exists for the email.
            NotifyUserError: If sending the verification email fails.
        """
        try:
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")

            # Check if verification code already exists
            code_exists = await self._cache_client.retrieve_code(key=f"email_{email}")
            if code_exists:
                raise VerificationCodeExist("Verification code already exists")

            # Generate verification code
            code = generate_verification_code()

            # Here you would typically send email instead of SMS
            # For now, we'll use the existing notify_user interface
            # In a real implementation, you'd have a separate email service
            response = await self._notify_user.send_request(phone_number=user.phone_number, otp=code)

            if response.status_code == 200:
                # Store with email prefix to distinguish from phone codes
                await self._cache_client.store_code(key=f"email_{email}", value=code)
                return True
            else:
                raise NotifyUserError("Something went wrong sending email verification")
        except Exception as e:
            raise e
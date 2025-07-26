from src.application.utils.security import generate_verification_code
from src.domain.exceptions import (
    NotifyUserError,
    UserNotFound,
    VerificationCodeExist,
    VerificationCodeExpired,
    IncorrectVerificationCode
)
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class ConfirmPhoneUseCase:
    """
    Use case for confirming user phone number verification.

    This class handles the phone confirmation process, including:
    - Verifying that the user exists.
    - Generating and sending a verification code to the user's phone.
    - Caching the verification code for later validation.

    Dependencies:
        user_repo (IUserRepository): Interface to access user data.
        cache_client (ICacheClient): Interface to manage cached verification codes.
        notify_user (INotifyUser): Interface to send SMS notifications.

    Methods:
        execute(phone_number: str) -> bool:
            Orchestrates the phone verification process by sending a code and caching it.
    """

    def __init__(
            self, user_repo: IUserRepository, cache_client: ICacheClient, notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._notify_user = notify_user
        self._cache_client = cache_client

    async def execute(self, phone_number: str) -> bool:
        """
        Initiates the phone verification process for the given phone number.

        Args:
            phone_number (str): The user's phone number to verify.

        Returns:
            bool: True if the verification code was successfully sent and cached.

        Raises:
            UserNotFound: If no user is associated with the provided phone number.
            VerificationCodeExist: If a valid verification code already exists for the phone.
            NotifyUserError: If sending the verification SMS fails.
        """
        try:
            user = await self._user_repo.get_by_phone_number(phone_number=phone_number)
            if not user:
                raise UserNotFound(f"User with phone number {phone_number} not found")

            # Check if verification code already exists
            code_exists = await self._cache_client.retrieve_code(key=f"phone_{phone_number}")
            if code_exists:
                raise VerificationCodeExist("Verification code already exists")

            # Generate verification code
            code = generate_verification_code()

            # Send SMS verification code
            response = await self._notify_user.send_request(phone_number=phone_number, otp=code)

            if response.status_code == 200:
                # Store with phone prefix to distinguish from email codes
                await self._cache_client.store_code(key=f"phone_{phone_number}", value=code)
                return True
            else:
                raise NotifyUserError("Something went wrong sending phone verification")
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------
class SubmitPhoneVerificationUseCase:
    """
    Use case for submitting phone verification code.
    """

    def __init__(self, user_repo: IUserRepository, cache_client: ICacheClient):
        self._user_repo = user_repo
        self._cache_client = cache_client

    async def execute(self, phone_number: str, code: str) -> bool:
        """
        Verifies the phone verification code.

        Args:
            phone_number (str): The user's phone number.
            code (str): The verification code.

        Returns:
            bool: True if verification successful.

        Raises:
            UserNotFound: If user not found.
            VerificationCodeExpired: If code expired.
            IncorrectVerificationCode: If code is wrong.
        """
        try:
            user = await self._user_repo.get_by_phone_number(phone_number)
            if not user:
                raise UserNotFound("User not found")

            # Get verification code from cache
            verification_code = await self._cache_client.retrieve_code(key=f"phone_{phone_number}")
            if not verification_code:
                raise VerificationCodeExpired("Verification code expired")

            if code != verification_code:
                raise IncorrectVerificationCode("Incorrect verification code")

            # Update user phone verification status
            await self._user_repo.update(
                user_id=user.id,
                user_new_data={"phone_number_verified": True}
            )

            # Remove verification code from cache
            await self._cache_client.delete_code(key=f"phone_{phone_number}")
            return True
        except Exception as e:
            raise e
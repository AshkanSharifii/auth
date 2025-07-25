from src.application.utils.security import generate_verification_code
from src.domain.exceptions import NotifyUserError, UserIsLocked, UserNotFound, VerificationCodeExist
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class OTPLoginUseCase:
    """
    Use case for initiating auth via OTP (One-Time Password).

    This class handles the OTP auth process, including:
    - Verifying that the user exists and is not locked.
    - Ensuring no existing OTP code is active for the user.
    - Generating a new verification code.
    - Sending the OTP code to the user's phone number via SMS.
    - Caching the verification code for later validation.

    Dependencies:
        user_repo (IUserRepository): Interface to access user data.
        cache_client (ICacheClient): Interface to manage cached verification codes.
        notify_user (INotifyUser): Interface to send SMS notifications.

    Methods:
        execute(phone_number: str) -> bool:
            Orchestrates the OTP auth process by sending a code and caching it.
            Returns True if successful, otherwise raises an appropriate exception.
    """

    def __init__(
        self, user_repo: IUserRepository, cache_client: ICacheClient, notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._notify_user = notify_user
        self._cache_client = cache_client

    async def execute(self, phone_number: str) -> bool:
        """
        Initiates the OTP auth process for the given phone number.

        This method:
        - Retrieves the user by phone number.
        - Checks if the user exists and is not locked.
        - Ensures that no active OTP code already exists for the phone number.
        - Generates a new verification code.
        - Sends the verification code to the user's phone via SMS.
        - Stores the verification code in the cache for later validation.

        Args:
            phone_number (str): The user's phone number to receive the OTP.

        Returns:
            bool: True if the OTP was successfully sent and cached.

        Raises:
            UserNotFound: If no user is associated with the provided phone number.
            UserIsLocked: If the user is currently locked from accessing the system.
            VerificationCodeExist: If a valid OTP code is already cached for the user.
            NotifyUserError: If sending the OTP SMS fails.
        """
        try:
            user = await self._user_repo.get_by_phone_number(phone_number=phone_number)
            if not user:
                raise UserNotFound(f"User with phone number {phone_number} not found")
            if user.is_locked:
                raise UserIsLocked("User is locked")
            code_exists = await self._cache_client.retrieve_code(key=phone_number)
            if code_exists:
                raise VerificationCodeExist("Verification code already exists")
            code = generate_verification_code()
            response = await self._notify_user.send_request(phone_number=phone_number, otp=code)
            if response.status_code == 200:
                await self._cache_client.store_code(key=phone_number, value=code)
                return True
            else:
                raise NotifyUserError("Something went wrong")
        except Exception as e:
            raise e

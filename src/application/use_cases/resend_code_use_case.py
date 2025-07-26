from src.application.utils.security import generate_verification_code
from src.domain.exceptions import NotifyUserError, UserNotFound, VerificationCodeExist
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class ResendCodeUseCase:
    """
    Use case for resending a verification code to a user via SMS.

    This use case retrieves the user by their phone number, checks if a verification
    code already exists in the cache, and if not, generates a new code, sends it via
    the notification service, and stores it in the cache.

    Dependencies:
        - IUserRepository: Interface to access user data.
        - ICacheClient: Interface to interact with the cache storage.
        - INotifyUser: Interface to send messages to users via a specific channel (e.g., SMS).

    Raises:
        UserNotFound: If the user does not exist in the repository.
        VerificationCodeExist: If a valid verification code already exists in the cache.
        Exception: For any other unexpected errors.
    """

    def __init__(
        self, user_repo: IUserRepository, cache_client: ICacheClient, notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._cache_client = cache_client
        self._notify_user = notify_user

    async def execute(self, phone_number: str) -> bool:
        """
        Resends a verification code to the user associated with the given phone number.

        Args:
            phone_number (str): The user's phone number.

        Returns:
            bool: True if the code was successfully sent and stored, False otherwise.

        Raises:
            UserNotFound: If no user is found with the given phone number.
            VerificationCodeExist: If a verification code is already cached.
            Exception: If any error occurs during the process.
        """
        try:
            user = await self._user_repo.get_by_phone_number(phone_number=phone_number)
            if not user:
                raise UserNotFound(f"User {phone_number} not found")

            # Check code exists
            code_exist = await self._cache_client.retrieve_code(key=phone_number)
            if code_exist:
                raise VerificationCodeExist("Verification code already exist")

            code = generate_verification_code()
            response = await self._notify_user.send_request(phone_number=phone_number, otp=code)
            if response.status_code == 200:
                await self._cache_client.store_code(key=phone_number, value=code)
                return True
            else:
                raise NotifyUserError("Something went wrong")
        except Exception as e:
            raise e

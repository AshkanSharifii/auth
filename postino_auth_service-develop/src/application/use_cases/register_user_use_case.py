from typing import Optional

from src.application.utils.security import generate_verification_code, hash_password
from src.domain.entities.user import User
from src.domain.exceptions import NotifyUserError, RoleNotFound, UserExist
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.role_repo import IRoleRepository
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class RegisterUserUseCase:
    """
    Use case for registering a new user and sending a verification code.

    This class handles the registration process, including:
    - Validating that the user doesn't already exist.
    - Assigning the "user" role to the new user.
    - Creating and storing the user in the database.
    - Generating and sending a verification code via SMS.
    - Caching the verification code for later validation.

    Dependencies:
        user_repo (IUserRepository): Interface to access and persist user data.
        role_repo (IRoleRepository): Interface to retrieve role data.
        notify_user (INotifyUser): Interface to send SMS notifications.
        cache_client (ICacheClient): Interface for caching verification codes.

    Methods:
        execute(...) -> Optional[User]:
            Orchestrates the entire registration process and sends an OTP code.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        role_repo: IRoleRepository,
        notify_user: INotifyUser,
        cache_client: ICacheClient,
    ):
        self._user_repo = user_repo
        self._role_repo = role_repo
        self._notify_user = notify_user
        self._cache_client = cache_client

    async def execute(
        self,
        phone_number: str,
        email: str,
        name: str,
        family: str,
        position: str,
        personal_code: str,
        password: str
    ) -> Optional[User]:
        """
        Registers a new user and sends a verification code via SMS.

        This method performs the following actions:
        1. Checks if a user with the given phone number, email, or personal code already exists.
        2. Retrieves the default "user" role.
        3. Creates a new user with the provided details and the retrieved role.
        4. Generates a 4-digit verification code.
        5. Sends the code to the user's phone via SMS.
        6. Stores the code in cache for future verification.

        Args:
            phone_number (str): The user's phone number.
            email (str): The user's email address.
            name (str): The user's first name.
            family (str): The user's last name.
            position (str): The user's position/title.
            personal_code (str): The user's unique personal code.
            password (str): The user's password.

        Returns:
            Optional[User]: The created user object if registration is successful.

        Raises:
            UserExist: If a user with the given phone number, email, or personal code already exists.
            RoleNotFound: If the "user" role cannot be found in the system.
            Exception: If any unexpected error occurs during the process.
        """
        try:
            # Check if user exists by phone number
            user_by_phone = await self._user_repo.get_by_phone_number(phone_number=phone_number)
            if user_by_phone:
                raise UserExist(f"User with phone number: {phone_number} already exists")

            # Check if user exists by email
            user_by_email = await self._user_repo.get_by_email(email=email)
            if user_by_email:
                raise UserExist(f"User with email: {email} already exists")

            # Check if user exists by personal code
            user_by_code = await self._user_repo.get_by_personal_code(personal_code=personal_code)
            if user_by_code:
                raise UserExist(f"User with personal code: {personal_code} already exists")

            user_role = await self._role_repo.get_role_by_name(name="user")
            if not user_role:
                raise RoleNotFound("Role not found")

            # Hash password
            hashed_password = hash_password(password)

            user_in = User(
                phone_number=phone_number,
                email=email,
                name=name,
                family=family,
                hashed_password=hashed_password,
                role_id=user_role.id,
                position=position,
                personal_code=personal_code,
            )
            user = await self._user_repo.insert(user=user_in)

            # Generate verification code
            code = generate_verification_code()
            response = await self._notify_user.send_request(
                phone_number=user.phone_number, otp=code
            )
            if response.status_code == 200:
                await self._cache_client.store_code(key=phone_number, value=code)
                return user
            else:
                raise NotifyUserError("Something went wrong")

        except Exception as e:
            raise e
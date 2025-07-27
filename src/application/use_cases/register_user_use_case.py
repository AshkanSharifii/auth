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
    Use case for registering a new user with email-only authentication.

    This class handles the registration process:
    - Validates that the user doesn't already exist
    - Assigns the "user" role to the new user
    - Creates and stores the user in the database
    - Sends email verification OTP
    - Caches the verification code for later validation

    Phone numbers are optional for contact purposes only.
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
            email: str,
            name: str,
            family: str,
            position: str,
            personal_code: str,
            password: str,
            phone_number: Optional[str] = None
    ) -> Optional[User]:
        """
        Registers a new user and sends email verification OTP.

        Args:
            email (str): The user's email address (required, primary identifier).
            name (str): The user's first name.
            family (str): The user's last name.
            position (str): The user's position/title.
            personal_code (str): The user's unique personal code.
            password (str): The user's password.
            phone_number (Optional[str]): The user's phone number (optional, contact only).

        Returns:
            Optional[User]: The created user object if registration is successful.

        Raises:
            UserExist: If a user with the given email or personal code already exists.
            RoleNotFound: If the "user" role cannot be found in the system.
            NotifyUserError: If sending the email verification fails.
        """
        try:
            # Check if user exists by email (primary identifier)
            user_by_email = await self._user_repo.get_by_email(email=email)
            if user_by_email:
                raise UserExist(f"User with email: {email} already exists")

            # Check if user exists by personal code
            user_by_code = await self._user_repo.get_by_personal_code(personal_code=personal_code)
            if user_by_code:
                raise UserExist(f"User with personal code: {personal_code} already exists")

            # Check if user exists by phone number (only if phone number provided)
            if phone_number and phone_number.strip():
                user_by_phone = await self._user_repo.get_by_phone_number(phone_number=phone_number)
                if user_by_phone:
                    raise UserExist(f"User with phone number: {phone_number} already exists")

            # Get default user role
            user_role = await self._role_repo.get_role_by_name(name="user")
            if not user_role:
                raise RoleNotFound("Default 'user' role not found in system")

            # Hash password
            hashed_password = hash_password(password)

            # Create user entity
            user_in = User(
                email=email,
                phone_number=phone_number if phone_number and phone_number.strip() else None,
                name=name,
                family=family,
                hashed_password=hashed_password,
                role_id=user_role.id,
                position=position,
                personal_code=personal_code,
            )

            # Insert user into database
            user = await self._user_repo.insert(user=user_in)

            # Generate and send email verification OTP
            code = generate_verification_code()
            response = await self._notify_user.send_email_otp(
                email=email, otp=code
            )

            if response.status_code == 200:
                # Store verification code in cache with email-based key
                await self._cache_client.store_code(key=f"email_verification_{email}", value=code)
                return user
            else:
                # Log warning but don't fail registration
                print(f"Warning: Failed to send verification email to {email}")
                return user

        except Exception as e:
            raise e
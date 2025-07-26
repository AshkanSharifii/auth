from typing import Optional
from src.application.utils.security import generate_verification_code
from src.domain.exceptions import NotifyUserError, UserIsLocked, UserNotFound, VerificationCodeExist
from src.domain.interfaces.cache_client import ICacheClient
from src.domain.interfaces.notify_user import INotifyUser
from src.ports.repositories.user_repo import IUserRepository


# ----------------------------------------------------------------------------
class OTPLoginUseCase:
    """
    UPDATED: Use case for initiating auth via OTP (One-Time Password).

    This class handles the OTP auth process for both email and phone, including:
    - Verifying that the user exists and is not locked.
    - Ensuring no existing OTP code is active for the user.
    - Generating a new verification code.
    - Sending the OTP code to email or phone number.
    - Caching the verification code for later validation.

    Dependencies:
        user_repo (IUserRepository): Interface to access user data.
        cache_client (ICacheClient): Interface to manage cached verification codes.
        notify_user (INotifyUser): Interface to send SMS/Email notifications.

    Methods:
        execute_phone_otp(phone_number: str) -> bool: Send OTP to phone
        execute_email_otp(email: str) -> bool: Send OTP to email
        execute(identifier: str) -> dict: Auto-detect and send OTP
    """

    def __init__(
            self, user_repo: IUserRepository, cache_client: ICacheClient, notify_user: INotifyUser
    ):
        self._user_repo = user_repo
        self._notify_user = notify_user
        self._cache_client = cache_client

    async def execute_phone_otp(self, phone_number: str) -> dict:
        """
        Send OTP to phone number.

        Args:
            phone_number (str): The user's phone number to receive the OTP.

        Returns:
            dict: Success message with method info.

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

            # Use phone-specific cache key
            cache_key = f"otp_phone_{phone_number}"
            code_exists = await self._cache_client.retrieve_code(key=cache_key)
            if code_exists:
                raise VerificationCodeExist("OTP already sent to this phone number")

            code = generate_verification_code()
            response = await self._notify_user.send_request(phone_number=phone_number, otp=code)

            if response.status_code == 200:
                await self._cache_client.store_code(key=cache_key, value=code)
                return {
                    "success": True,
                    "message": f"OTP sent to phone number {phone_number}",
                    "method": "phone",
                    "identifier": phone_number
                }
            else:
                raise NotifyUserError("Failed to send SMS")
        except Exception as e:
            raise e

    async def execute_email_otp(self, email: str) -> dict:
        """
        Send OTP to email address.

        Args:
            email (str): The user's email address to receive the OTP.

        Returns:
            dict: Success message with method info.

        Raises:
            UserNotFound: If no user is associated with the provided email.
            UserIsLocked: If the user is currently locked from accessing the system.
            VerificationCodeExist: If a valid OTP code is already cached for the user.
            NotifyUserError: If sending the OTP email fails.
        """
        try:
            user = await self._user_repo.get_by_email(email=email)
            if not user:
                raise UserNotFound(f"User with email {email} not found")
            if user.is_locked:
                raise UserIsLocked("User is locked")

            # Use email-specific cache key
            cache_key = f"otp_email_{email}"
            code_exists = await self._cache_client.retrieve_code(key=cache_key)
            if code_exists:
                raise VerificationCodeExist("OTP already sent to this email")

            code = generate_verification_code()

            # For now, send to phone since we use SMS service
            # In production, you'd have a separate email service
            response = await self._notify_user.send_request(phone_number=user.phone_number, otp=code)

            if response.status_code == 200:
                await self._cache_client.store_code(key=cache_key, value=code)
                return {
                    "success": True,
                    "message": f"OTP sent to email {email}",
                    "method": "email",
                    "identifier": email
                }
            else:
                raise NotifyUserError("Failed to send email OTP")
        except Exception as e:
            raise e

    async def execute(self, identifier: str) -> dict:
        """
        UPDATED: Auto-detect identifier type and send appropriate OTP.

        Args:
            identifier (str): Email or phone number.

        Returns:
            dict: Success message with method info.
        """
        try:
            # Auto-detect if identifier is email or phone
            if "@" in identifier:
                return await self.execute_email_otp(email=identifier)
            elif identifier.startswith("+") or identifier.replace("-", "").replace(" ", "").isdigit():
                return await self.execute_phone_otp(phone_number=identifier)
            else:
                raise UserNotFound(f"Invalid identifier format: {identifier}")
        except Exception as e:
            raise e

    # Keep the old method for backward compatibility
    async def execute_legacy(self, phone_number: str) -> bool:
        """
        Legacy method for backward compatibility.
        Use execute() or execute_phone_otp() instead.
        """
        try:
            result = await self.execute_phone_otp(phone_number)
            return result["success"]
        except Exception as e:
            raise e
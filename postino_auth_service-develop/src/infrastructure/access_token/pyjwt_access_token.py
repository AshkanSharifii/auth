from datetime import datetime, timedelta
from typing import Optional, override

import jwt
from jwt.exceptions import InvalidTokenError

from src.config import settings
from src.domain.interfaces.access_token import IAccessToken


# ----------------------------------------------------------------------------
class PyJWTAccessToken(IAccessToken):
    """
    Implementation of the IAccessToken interface using PyJWT.

    This class provides methods to create and decode JWT access tokens,
    using configurations provided in the application settings.

    Attributes:
        __secret_key (str): The secret key used to sign tokens.
        __algorithm (str): The algorithm used to encode/decode JWTs.
    """

    def __init__(self):
        self.__secret_key = settings.TOKEN_SECRET_KEY
        self.__algorithm = settings.TOKEN_ALGORITHM

    @override
    def create_access_token(
        self,
        data: dict,
        expire_time: Optional[timedelta] = None,
        refresh_type: Optional[bool] = False,
    ) -> str:
        """
        Creates a JWT access token.

        Args:
            data (dict): The payload to encode in the token.
            expire_time (Optional[timedelta]): Custom expiration time. If not provided,
                the default expiration from settings is used.

        Returns:
            str: Encoded JWT token as a string.
        """
        to_encode = data.copy()
        if expire_time:
            expire = datetime.now() + expire_time
        else:
            expire = datetime.now() + timedelta(hours=settings.TOKEN_EXPIRE_HOURS)

        if refresh_type:
            expire = datetime.now() + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
            to_encode.update({"type": "refresh_token"})

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            payload=to_encode, key=self.__secret_key, algorithm=self.__algorithm
        )
        return encoded_jwt

    @override
    def decode_access_token(self, access_token: str, check_type: bool = True) -> Optional[dict]:
        """
        Decodes a JWT access token and returns the payload.

        Args:
            access_token (str): The JWT token to decode.

        Returns:
            Optional[dict]: The decoded payload if token is valid.

        Raises:
            InvalidTokenError: If the token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                jwt=access_token, key=self.__secret_key, algorithms=[self.__algorithm]
            )
            if check_type:
                if payload.get("type") == "refresh_token":
                    raise InvalidTokenError("Access token is actually a refresh token.")

            return payload

        except InvalidTokenError as e:
            raise e

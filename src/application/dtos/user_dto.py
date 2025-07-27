from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr, constr, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber


# ----------------------------------------------------------------------------
class UserBaseDTO(BaseModel):
    """Base DTO with email as primary identifier"""
    email: EmailStr


# ----------------------------------------------------------------------------
class SubmitCodeDTO(BaseModel):
    """Email OTP verification DTO"""
    email: EmailStr
    code: constr(min_length=4, max_length=4)  # type: ignore


# ----------------------------------------------------------------------------
class RegisterUserDTO(BaseModel):
    """User registration DTO - phone is optional for contact only"""
    email: EmailStr
    name: str
    family: str
    position: str
    personal_code: str
    password: str
    confirm_password: str
    phone_number: Optional[PhoneNumber] = None

    @field_validator("phone_number", mode="after")
    def validate_phone_number(cls, value):
        if value:
            value = value.split("tel:")[1].replace("-", "")
        return value

    @field_validator("confirm_password")
    def passwords_match(cls, confirm_password, values):
        password = values.data["password"]
        if password != confirm_password:
            raise ValueError("Password and Confirm Password do not match.")
        return confirm_password


# ----------------------------------------------------------------------------
class UserDTO(BaseModel):
    """Complete user DTO"""
    email: EmailStr
    name: str
    family: str
    position: str
    personal_code: str
    role_id: UUID
    is_verified: bool
    email_verified: bool
    phone_number_verified: bool
    is_active: bool
    latest_login: datetime | None = None
    id: UUID
    phone_number: Optional[str] = None


# ----------------------------------------------------------------------------
class UserMeDTO(UserDTO):
    """User profile DTO with role information"""
    role_name: str


# ----------------------------------------------------------------------------
class LoginDTO(BaseModel):
    """Email login DTO"""
    email: EmailStr
    password: str


# ----------------------------------------------------------------------------
class EmailOTPRequestDTO(BaseModel):
    """Email OTP request DTO"""
    email: EmailStr


# ----------------------------------------------------------------------------
class EmailOTPVerifyDTO(BaseModel):
    """Email OTP verification DTO"""
    email: EmailStr
    code: str
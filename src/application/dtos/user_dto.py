from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, constr, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber


# ----------------------------------------------------------------------------
class UserBaseDTO(BaseModel):
    phone_number: PhoneNumber
    email: EmailStr

    @field_validator("phone_number", mode="after")
    def validate_phone_number(cls, value):
        value = value.split("tel:")[1].replace("-", "")
        return value


# ----------------------------------------------------------------------------
class SubmitCodeDTO(UserBaseDTO):
    code: constr(min_length=4, max_length=4)  # type: ignore


# ----------------------------------------------------------------------------
class RegisterUserDTO(UserBaseDTO):
    name: str
    family: str
    position: str
    personal_code: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    def passwords_match(cls, confirm_password, values):
        password = values.data["password"]
        if password != confirm_password:
            raise ValueError("Password and Confirm Password do not match.")
        return password


# ----------------------------------------------------------------------------
class UserDTO(UserBaseDTO):
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


# ----------------------------------------------------------------------------
class UserMeDTO(UserDTO):
    role_name: str
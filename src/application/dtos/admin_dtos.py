from datetime import datetime
from uuid import UUID
from typing import List
from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber

from src.application.dtos.user_dto import UserDTO


# ----------------------------------------------------------------------------
class EmailVerificationDTO(BaseModel):
    email: EmailStr


# ----------------------------------------------------------------------------
class ConfirmUserDTO(BaseModel):
    user_id: UUID


# ----------------------------------------------------------------------------
class ActivateUserDTO(BaseModel):
    user_id: UUID
    is_active: bool


# ----------------------------------------------------------------------------
class AssignRoleDTO(BaseModel):
    user_id: UUID
    role_id: UUID


# ----------------------------------------------------------------------------
class UserWithRoleDTO(UserDTO):
    role_name: str


# ----------------------------------------------------------------------------
class GetUserByIdDTO(BaseModel):
    user_id: UUID


# ----------------------------------------------------------------------------
class UsersListResponseDTO(BaseModel):
    users: List[UserWithRoleDTO]
    total_count: int


# ----------------------------------------------------------------------------
class AdminActionResponseDTO(BaseModel):
    success: bool
    message: str


# ----------------------------------------------------------------------------
class PhoneVerificationDTO(BaseModel):
    phone_number: PhoneNumber

    @field_validator("phone_number", mode="after")
    def validate_phone_number(cls, value):
        value = value.split("tel:")[1].replace("-", "")
        return value


# ----------------------------------------------------------------------------
class SubmitPhoneVerificationDTO(BaseModel):
    phone_number: PhoneNumber
    code: str = Field(..., min_length=4, max_length=4)

    @field_validator("phone_number", mode="after")
    def validate_phone_number(cls, value):
        value = value.split("tel:")[1].replace("-", "")
        return value


# ----------------------------------------------------------------------------
class LoginHistoryDTO(BaseModel):
    user_id: UUID
    login_time: datetime
    ip_address: str
    user_agent: str
    login_method: str
    success: bool
    failure_reason: str | None = None
    id: UUID


# ----------------------------------------------------------------------------
class LoginHistoryListDTO(BaseModel):
    login_history: List[LoginHistoryDTO]
    total_count: int


# ----------------------------------------------------------------------------
class GetUserLoginHistoryDTO(BaseModel):
    user_id: UUID
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
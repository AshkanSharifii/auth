from datetime import datetime
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from src.application.dtos.user_dto import UserDTO


# ----------------------------------------------------------------------------
class EmailVerificationDTO(BaseModel):
    """Email verification request DTO"""
    email: EmailStr


# ----------------------------------------------------------------------------
class EmailVerificationSubmitDTO(BaseModel):
    """Email verification code submission DTO"""
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4)


# ----------------------------------------------------------------------------
class ConfirmUserDTO(BaseModel):
    """Admin confirm user DTO"""
    user_id: UUID


# ----------------------------------------------------------------------------
class ActivateUserDTO(BaseModel):
    """Admin activate/deactivate user DTO"""
    user_id: UUID
    is_active: bool


# ----------------------------------------------------------------------------
class AssignRoleDTO(BaseModel):
    """Admin assign role DTO"""
    user_id: UUID
    role_id: UUID


# ----------------------------------------------------------------------------
class UserWithRoleDTO(UserDTO):
    """User DTO with role information"""
    role_name: str


# ----------------------------------------------------------------------------
class GetUserByIdDTO(BaseModel):
    """Get user by ID DTO"""
    user_id: UUID


# ----------------------------------------------------------------------------
class UsersListResponseDTO(BaseModel):
    """List of users response DTO"""
    users: List[UserWithRoleDTO]
    total_count: int


# ----------------------------------------------------------------------------
class AdminActionResponseDTO(BaseModel):
    """Generic admin action response DTO"""
    success: bool
    message: str


# ----------------------------------------------------------------------------
class LoginHistoryDTO(BaseModel):
    """Login history DTO"""
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
    """Login history list DTO"""
    login_history: List[LoginHistoryDTO]
    total_count: int


# ----------------------------------------------------------------------------
class GetUserLoginHistoryDTO(BaseModel):
    """Get user login history DTO"""
    user_id: UUID
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
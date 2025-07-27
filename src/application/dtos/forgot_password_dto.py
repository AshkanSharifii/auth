from pydantic import BaseModel, EmailStr, Field


# ----------------------------------------------------------------------------
class ForgotPasswordRequestDTO(BaseModel):
    """Request DTO for forgot password - send reset code to email"""
    email: EmailStr


# ----------------------------------------------------------------------------
class ForgotPasswordVerifyDTO(BaseModel):
    """Verify reset code DTO"""
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4)


# ----------------------------------------------------------------------------
class ResetPasswordDTO(BaseModel):
    """Reset password with code DTO"""
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    def passwords_match(self) -> bool:
        return self.new_password == self.confirm_password


# ----------------------------------------------------------------------------
class ForgotPasswordResponseDTO(BaseModel):
    """Generic forgot password response DTO"""
    success: bool
    message: str
    email: str
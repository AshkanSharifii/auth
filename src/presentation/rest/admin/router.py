from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dtos.admin_dtos import (
    EmailVerificationDTO,
    ConfirmUserDTO,
    ActivateUserDTO,
    AssignRoleDTO,
    UserWithRoleDTO,
    UsersListResponseDTO,
    AdminActionResponseDTO,
    LoginHistoryListDTO,
    LoginHistoryDTO
)
from src.application.use_cases.otp_login_use_case import OTPLoginUseCase
from src.application.use_cases.admin_use_cases import (
    ConfirmUserBySuperAdminUseCase,
    ActivateUserBySuperAdminUseCase,
    GetAllUsersUseCase,
    GetSpecificUserUseCase,
    AssignRoleToUserUseCase
)
from src.application.use_cases.login_history_use_case import GetLoginHistoryUseCase
from src.di.container import Container
from src.domain.exceptions import (
    UserNotFound,
    RoleNotFound,
    VerificationCodeExist,
    NotifyUserError
)
from src.presentation.rest.admin.dependencies import get_current_super_admin_user

# ----------------------------------------------------------------------------
router = APIRouter()


# ----------------------------------------------------------------------------
@router.post("/email/send-verification", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def send_email_verification(
        *,
        otp_login_use_case: OTPLoginUseCase = Depends(
            Provide[Container.otp_login_use_case_provider]
        ),
        email_dto: EmailVerificationDTO,
        admin_data: tuple = Depends(get_current_super_admin_user)
):
    """
    Send email verification code to user. (SUPER ADMIN ONLY)
    """
    try:
        admin_user, admin_role = admin_data
        response = await otp_login_use_case.execute(email=email_dto.email)
        return AdminActionResponseDTO(
            success=True,
            message="Email verification code sent successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VerificationCodeExist as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotifyUserError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ----------------------------------------------------------------------------
@router.post("/confirm-user", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def confirm_user_by_super_admin(
        *,
        confirm_user_use_case: ConfirmUserBySuperAdminUseCase = Depends(
            Provide[Container.confirm_user_by_super_admin_use_case_provider]
        ),
        confirm_dto: ConfirmUserDTO,
        admin_data: tuple = Depends(get_current_super_admin_user)
):
    """
    Super admin confirms/verifies a user account.
    """
    try:
        admin_user, admin_role = admin_data
        response = await confirm_user_use_case.execute(
            user_id=confirm_dto.user_id,
            admin_user=admin_user
        )
        return AdminActionResponseDTO(
            success=True,
            message="User confirmed successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ----------------------------------------------------------------------------
@router.post("/activate-user", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def activate_user_by_super_admin(
        *,
        activate_user_use_case: ActivateUserBySuperAdminUseCase = Depends(
            Provide[Container.activate_user_by_super_admin_use_case_provider]
        ),
        activate_dto: ActivateUserDTO,
        admin_data: tuple = Depends(get_current_super_admin_user)
):
    """
    Super admin activates or deactivates a user account.
    """
    try:
        admin_user, admin_role = admin_data
        response = await activate_user_use_case.execute(
            user_id=activate_dto.user_id,
            is_active=activate_dto.is_active,
            admin_user=admin_user
        )
        action = "activated" if activate_dto.is_active else "deactivated"
        return AdminActionResponseDTO(
            success=True,
            message=f"User {action} successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ----------------------------------------------------------------------------
@router.get("/users", status_code=status.HTTP_200_OK, response_model=UsersListResponseDTO)
@inject
async def get_all_users(
        *,
        get_all_users_use_case: GetAllUsersUseCase = Depends(
            Provide[Container.get_all_users_use_case_provider]
        ),
        admin_data: tuple = Depends(get_current_super_admin_user),
        limit: int = 100,
        offset: int = 0
):
    """
    Get all users in the system (SUPER ADMIN ONLY).
    """
    try:
        admin_user, admin_role = admin_data
        user_role_pairs = await get_all_users_use_case.execute(admin_user=admin_user)

        # Convert to DTOs
        users_dto = []
        for user, role in user_role_pairs:
            user_dto = UserWithRoleDTO(
                email=user.email,
                phone_number=user.phone_number,  # Optional field
                name=user.name,
                family=user.family,
                position=user.position,
                personal_code=user.personal_code,
                role_id=user.role_id,
                is_verified=user.is_verified,
                email_verified=user.email_verified,
                phone_number_verified=user.phone_number_verified,
                is_active=user.is_active,
                latest_login=user.latest_login,
                id=user.id,
                role_name=role.role_name if role else "Unknown"
            )
            users_dto.append(user_dto)

        return UsersListResponseDTO(
            users=users_dto,
            total_count=len(users_dto)
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------------------------------------------------------
@router.get("/users/{user_id}", status_code=status.HTTP_200_OK, response_model=UserWithRoleDTO)
@inject
async def get_specific_user(
        *,
        user_id: str,
        get_specific_user_use_case: GetSpecificUserUseCase = Depends(
            Provide[Container.get_specific_user_use_case_provider]
        ),
        admin_data: tuple = Depends(get_current_super_admin_user)
):
    """
    Get a specific user by ID (SUPER ADMIN ONLY).
    """
    try:
        admin_user, admin_role = admin_data
        from uuid import UUID
        user_uuid = UUID(user_id)

        user, role = await get_specific_user_use_case.execute(
            user_id=user_uuid,
            admin_user=admin_user
        )

        return UserWithRoleDTO(
            email=user.email,
            phone_number=user.phone_number,  # Optional field
            name=user.name,
            family=user.family,
            position=user.position,
            personal_code=user.personal_code,
            role_id=user.role_id,
            is_verified=user.is_verified,
            email_verified=user.email_verified,
            phone_number_verified=user.phone_number_verified,
            is_active=user.is_active,
            latest_login=user.latest_login,
            id=user.id,
            role_name=role.role_name if role else "Unknown"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")


# ----------------------------------------------------------------------------
@router.get("/users/{user_id}/login-history", status_code=status.HTTP_200_OK, response_model=LoginHistoryListDTO)
@inject
async def get_user_login_history(
        *,
        user_id: str,
        get_login_history_use_case: GetLoginHistoryUseCase = Depends(
            Provide[Container.get_login_history_use_case_provider]
        ),
        admin_data: tuple = Depends(get_current_super_admin_user),
        limit: int = 50,
        offset: int = 0
):
    """
    Get login history for a specific user (SUPER ADMIN ONLY).
    """
    try:
        admin_user, admin_role = admin_data
        from uuid import UUID
        user_uuid = UUID(user_id)

        login_history = await get_login_history_use_case.execute(
            user_id=user_uuid,
            admin_user=admin_user,
            limit=limit,
            offset=offset
        )

        # Convert to DTOs
        history_dtos = []
        for history in login_history:
            history_dto = LoginHistoryDTO(
                user_id=history.user_id,
                login_time=history.login_time,
                ip_address=history.ip_address,
                user_agent=history.user_agent,
                login_method=history.login_method,
                success=history.success,
                failure_reason=history.failure_reason,
                id=history.id
            )
            history_dtos.append(history_dto)

        return LoginHistoryListDTO(
            login_history=history_dtos,
            total_count=len(history_dtos)
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")


# ----------------------------------------------------------------------------
@router.post("/assign-role", status_code=status.HTTP_200_OK, response_model=AdminActionResponseDTO)
@inject
async def assign_role_to_user(
        *,
        assign_role_use_case: AssignRoleToUserUseCase = Depends(
            Provide[Container.assign_role_to_user_use_case_provider]
        ),
        assign_dto: AssignRoleDTO,
        admin_data: tuple = Depends(get_current_super_admin_user)
):
    """
    Super admin assigns a role to a user.
    """
    try:
        admin_user, admin_role = admin_data
        response = await assign_role_use_case.execute(
            user_id=assign_dto.user_id,
            role_id=assign_dto.role_id,
            admin_user=admin_user
        )
        return AdminActionResponseDTO(
            success=True,
            message="Role assigned successfully"
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RoleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
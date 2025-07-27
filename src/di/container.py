from dependency_injector import containers, providers

from src.application.use_cases.get_current_user_use_case import GetCurrentUserUseCase
from src.application.use_cases.login_with_password_use_case import LoginWithPasswordUseCase
from src.application.use_cases.otp_login_use_case import OTPLoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.resend_code_use_case import ResendCodeUseCase
from src.application.use_cases.submit_verification_code_use_case import (
    SubmitVerificationCodeUseCase,
)
from src.application.use_cases.admin_use_cases import (
    ConfirmUserBySuperAdminUseCase,
    ActivateUserBySuperAdminUseCase,
    GetAllUsersUseCase,
    GetSpecificUserUseCase,
    AssignRoleToUserUseCase
)
from src.application.use_cases.login_history_use_case import (
    RecordLoginHistoryUseCase,
    GetLoginHistoryUseCase,
    GetMyLoginHistoryUseCase
)

from src.infrastructure.access_token.pyjwt_access_token import PyJWTAccessToken
from src.infrastructure.cache_client.redis_client import RedisClient
from src.infrastructure.database.postgresql_connection import PostgreSQLConnection
from src.infrastructure.notify_user.async_notify_user import AsyncNotifyUser
from src.infrastructure.repository.role_repo import RoleRepository
from src.infrastructure.repository.user_repo import UserRepository
from src.infrastructure.repository.login_history_repo import LoginHistoryRepository


# ----------------------------------------------------------------------------
class Container(containers.DeclarativeContainer):
    """
    Complete dependency injection container for email-only authentication system.
    Includes all use cases with full functionality.
    """

    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.presentation.rest.auth.router",
            "src.presentation.rest.user.router",
            "src.presentation.rest.admin.router",
        ]
    )

    # Infrastructure providers
    sql_connection_provider = providers.Singleton(PostgreSQLConnection)

    # Repository providers
    user_repository_provider = providers.Factory(
        UserRepository, sql_connection=sql_connection_provider
    )
    role_repository_provider = providers.Factory(
        RoleRepository, sql_connection=sql_connection_provider
    )
    login_history_repository_provider = providers.Factory(
        LoginHistoryRepository, sql_connection=sql_connection_provider
    )

    # Service providers
    access_token_provider = providers.Factory(PyJWTAccessToken)
    notify_user_provider = providers.Factory(AsyncNotifyUser)
    cache_client_provider = providers.Singleton(RedisClient)

    # Core authentication use cases
    register_user_use_case_provider = providers.Factory(
        RegisterUserUseCase,
        user_repo=user_repository_provider,
        role_repo=role_repository_provider,
        notify_user=notify_user_provider,
        cache_client=cache_client_provider,
    )

    # Login with password use case (includes flexible login and OTP verification)
    login_with_password_use_case_provider = providers.Factory(
        LoginWithPasswordUseCase,
        user_repo=user_repository_provider,
        access_token=access_token_provider,
        role_repo=role_repository_provider,
        cache_client=cache_client_provider,
        notify_user=notify_user_provider,
    )

    # Email OTP login use case
    otp_login_use_case_provider = providers.Factory(
        OTPLoginUseCase,
        user_repo=user_repository_provider,
        cache_client=cache_client_provider,
        notify_user=notify_user_provider,
    )

    # Submit verification code (supports multiple verification types)
    submit_verification_code_use_case_provider = providers.Factory(
        SubmitVerificationCodeUseCase,
        user_repo=user_repository_provider,
        access_token=access_token_provider,
        role_repo=role_repository_provider,
        cache_client=cache_client_provider,
    )

    # Resend code use case
    resend_code_use_case_provider = providers.Factory(
        ResendCodeUseCase,
        user_repo=user_repository_provider,
        cache_client=cache_client_provider,
        notify_user=notify_user_provider,
    )

    # Get current user use case
    get_current_user_use_case = providers.Factory(
        GetCurrentUserUseCase,
        user_repo=user_repository_provider,
        role_repo=role_repository_provider,
        access_token=access_token_provider,
    )

    # Refresh token use case
    refresh_token_use_case_provider = providers.Factory(
        RefreshTokenUseCase,
        user_repo=user_repository_provider,
        access_token=access_token_provider,
        role_repo=role_repository_provider,
    )

    # Admin management use cases
    confirm_user_by_super_admin_use_case_provider = providers.Factory(
        ConfirmUserBySuperAdminUseCase,
        user_repo=user_repository_provider,
    )

    activate_user_by_super_admin_use_case_provider = providers.Factory(
        ActivateUserBySuperAdminUseCase,
        user_repo=user_repository_provider,
    )

    get_all_users_use_case_provider = providers.Factory(
        GetAllUsersUseCase,
        user_repo=user_repository_provider,
        role_repo=role_repository_provider,
    )

    get_specific_user_use_case_provider = providers.Factory(
        GetSpecificUserUseCase,
        user_repo=user_repository_provider,
        role_repo=role_repository_provider,
    )

    assign_role_to_user_use_case_provider = providers.Factory(
        AssignRoleToUserUseCase,
        user_repo=user_repository_provider,
        role_repo=role_repository_provider,
    )

    # Login history use cases
    record_login_history_use_case_provider = providers.Factory(
        RecordLoginHistoryUseCase,
        login_history_repo=login_history_repository_provider,
    )

    get_login_history_use_case_provider = providers.Factory(
        GetLoginHistoryUseCase,
        login_history_repo=login_history_repository_provider,
        user_repo=user_repository_provider,
    )

    get_my_login_history_use_case_provider = providers.Factory(
        GetMyLoginHistoryUseCase,
        login_history_repo=login_history_repository_provider,
    )
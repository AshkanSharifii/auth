from dependency_injector import containers, providers

from src.application.use_cases.delete_user_brand_use_case import DeleteUserBrandUseCase
from src.application.use_cases.get_current_user_use_case import GetCurrentUserUseCase
from src.application.use_cases.login_with_password_use_case import LoginWithPasswordUseCase
from src.application.use_cases.otp_login_use_case import OTPLoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.resend_code_use_case import ResendCodeUseCase
from src.application.use_cases.create_user_brand_use_case import CreateUserBrandUseCase
from src.application.use_cases.update_user_brand_use_case import UpdateUserBrandUseCase
from src.application.use_cases.industries_list_use_case import GetBrandIndustriesUseCase
from src.application.use_cases.tones_list_use_case import GetBrandTonesUseCase
from src.application.use_cases.update_industry_use_case import UpdateBrandIndustryUseCase
from src.application.use_cases.delete_industry_use_case import DeleteBrandIndustryUseCase
from src.application.use_cases.create_industry_use_case import CreateBrandIndustryUseCase
from src.application.use_cases.create_tone_use_case import CreateBrandToneUseCase
from src.application.use_cases.update_tone_use_case import UpdateBrandToneUseCase
from src.application.use_cases.delete_tone_use_case import DeleteBrandToneUseCase
from src.application.use_cases.submit_verification_code_use_case import (
    SubmitVerificationCodeUseCase,
)
from src.infrastructure.object_storage.object_storage import S3ObjectStorage
from src.infrastructure.access_token.pyjwt_access_token import PyJWTAccessToken
from src.infrastructure.cache_client.redis_client import RedisClient
from src.infrastructure.database.postgresql_connection import PostgreSQLConnection
from src.infrastructure.notify_user.async_notify_user import AsyncNotifyUser
from src.infrastructure.repository.brand_repo import BrandRepository
from src.infrastructure.repository.industry_repo import IndustryRepository
from src.infrastructure.repository.tone_repo import BrandToneRepository
from src.infrastructure.repository.role_repo import RoleRepository
from src.infrastructure.repository.user_repo import UserRepository


# ----------------------------------------------------------------------------
class Container(containers.DeclarativeContainer):
    """
    Dependency injection container for the application.

    Defines and wires all the infrastructure and application-level components,
    such as repositories, use cases, token providers, notification services, and database connections.

    Attributes:
        wiring_config (WiringConfiguration): Specifies the modules where dependencies will be injected.

        sql_connection_provider (Singleton): Provides a single instance of the PostgreSQL connection.
        user_repository_provider (Factory): Factory for creating UserRepository instances.
        role_repository_provider (Factory): Factory for creating RoleRepository instances.
        brand_repository_provider (Factory): Factory for creating BrandRepository instances.
        access_token_provider (Factory): Factory for creating access token utility (PyJWTAccessToken).
        notify_user_provider (Factory): Factory for creating notification service client (AsyncNotifyUser).
        cache_client_provider (Singleton): Singleton Redis cache client provider.

        register_user_use_case_provider (Factory): Factory for creating the RegisterUserUseCase, with dependencies injected.
    """

    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.presentation.rest.auth.router",
            "src.presentation.rest.user.router",
            "src.presentation.rest.brands.router",
            "src.presentation.rest.industries.router",
            "src.presentation.rest.tones.router",
        ]
    )

    # SQL connection
    sql_connection_provider = providers.Singleton(PostgreSQLConnection)

    # User repository
    user_repository_provider = providers.Factory(
        UserRepository, sql_connection=sql_connection_provider
    )

    # Role repository
    role_repository_provider = providers.Factory(
        RoleRepository, sql_connection=sql_connection_provider
    )

    # Brand repository
    brand_repository_provider = providers.Factory(
        BrandRepository, sql_connection=sql_connection_provider
    )

    # Industry repository
    industry_repository_provider = providers.Factory(
        IndustryRepository, sql_connection=sql_connection_provider
    )

    # Tone repository
    tone_repository_provider = providers.Factory(
        BrandToneRepository, sql_connection=sql_connection_provider
    )

    # Access token provider
    access_token_provider = providers.Factory(PyJWTAccessToken)

    # Notify user provider
    notify_user_provider = providers.Factory(AsyncNotifyUser)

    # Cache client
    cache_client_provider = providers.Singleton(RedisClient)

    # Object storage client
    object_storage_provider = providers.Singleton(S3ObjectStorage)

    # Register user use case
    register_user_use_case_provider = providers.Factory(
        RegisterUserUseCase,
        user_repo=user_repository_provider,
        role_repo=role_repository_provider,
        notify_user=notify_user_provider,
        cache_client=cache_client_provider,
    )

    # Login with password use case
    login_with_password_use_case_provider = providers.Factory(
        LoginWithPasswordUseCase,
        user_repo=user_repository_provider,
        access_token=access_token_provider,
        role_repo=role_repository_provider,
    )

    # Login otp use case
    otp_login_use_case_provider = providers.Factory(
        OTPLoginUseCase,
        user_repo=user_repository_provider,
        cache_client=cache_client_provider,
        notify_user=notify_user_provider,
    )

    # Submit verification code use case
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
        brand_repo=brand_repository_provider,
        access_token=access_token_provider,
    )

    # Refresh token use case
    refresh_token_use_case_provider = providers.Factory(
        RefreshTokenUseCase,
        user_repo=user_repository_provider,
        access_token=access_token_provider,
        role_repo=role_repository_provider,
    )

    # Create user brand use case
    create_user_brand_use_case_provider = providers.Factory(
        CreateUserBrandUseCase,
        brand_repo=brand_repository_provider,
        object_storage=object_storage_provider,
        industry_repo=industry_repository_provider,
        tone_repo=tone_repository_provider,
    )

    # Update user brand use case
    update_user_brand_use_case_provicer = providers.Factory(
        UpdateUserBrandUseCase,
        brand_repo=brand_repository_provider,
        object_storage=object_storage_provider,
        industry_repo=industry_repository_provider,
        tone_repo=tone_repository_provider,
    )

    # Delete user brand use case
    delete_user_brand_use_case_provicer = providers.Factory(
        DeleteUserBrandUseCase,
        brand_repo=brand_repository_provider,
        object_storage=object_storage_provider
    )

    # get brand industries use case
    get_brand_industries_use_case = providers.Factory(
        GetBrandIndustriesUseCase,
        industry_repo=industry_repository_provider
    )

    # get brand tones use case
    get_brand_tones_use_case = providers.Factory(
        GetBrandTonesUseCase,
        tone_repo=tone_repository_provider,
    )

    # create brand industry
    create_brand_industry_use_case = providers.Factory(
        CreateBrandIndustryUseCase,
        industry_repo=industry_repository_provider,
        role_repo=role_repository_provider,
    )

    # update brand industry
    update_brand_industry_use_case = providers.Factory(
        UpdateBrandIndustryUseCase,
        industry_repo=industry_repository_provider,
        role_repo=role_repository_provider,
    )

    # delete brand industry
    delete_brand_industry_use_case = providers.Factory(
        DeleteBrandIndustryUseCase,
        industry_repo=industry_repository_provider,
        role_repo=role_repository_provider,
    )

    # create brand tone
    create_brand_tone_use_case = providers.Factory(
        CreateBrandToneUseCase,
        tone_repo=tone_repository_provider,
        role_repo=role_repository_provider,
    )

    # update brand tone
    update_brand_tone_use_case = providers.Factory(
        UpdateBrandToneUseCase,
        tone_repo=tone_repository_provider,
        role_repo=role_repository_provider,
    )

    # delete brand tone
    delete_brand_tone_use_case = providers.Factory(
        DeleteBrandToneUseCase,
        tone_repo=tone_repository_provider,
        role_repo=role_repository_provider,
    )

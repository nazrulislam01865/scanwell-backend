from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.environment import Environment


class Settings(BaseSettings):
    app_name: str = "ScanWell API"
    app_env: Environment = Environment.DEVELOPMENT
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+asyncpg://"
        "scanwell:Shuvessa@localhost:5432/scanwell"
    )

    cors_origins: list[str] = Field(
        default_factory=list
    )

    secret_key: str = (
        "change-this-development-secret-"
        "before-production"
    )

    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "scanwell-api"
    jwt_audience: str = "scanwell-mobile"

    access_token_minutes: int = 15
    refresh_token_days: int = 30

    verification_code_minutes: int = 10
    verification_code_max_attempts: int = 5

    auth_expose_development_codes: bool = False

    # ------------------------------
    # Central Email Configuration
    # ------------------------------

    email_driver: str = "log"
    
    # Resend
    resend_api_key: str | None = None

    resend_timeout_seconds: int = 15

    email_from_name: str = "ScanWell"

    email_from_address: str = (
        "no-reply@scanwell.local"
    )




    # SMTP
    smtp_host: str | None = None

    smtp_port: int = 587

    smtp_username: str | None = None

    smtp_password: str | None = None

    smtp_use_tls: bool = True

    smtp_use_ssl: bool = False

    smtp_timeout_seconds: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def expose_development_codes(self) -> bool:
        return (
            self.app_env
            == Environment.DEVELOPMENT
            and self.auth_expose_development_codes
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
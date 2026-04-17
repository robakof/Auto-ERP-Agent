from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEY = "change-me-to-random-32-char-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://serce:serce_dev@localhost:5432/serce"

    # JWT
    secret_key: str = _INSECURE_DEFAULT_KEY
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8081"

    # Business rules
    initial_heart_grant: int = 5
    heart_balance_cap: int = 50
    request_default_expiry_days: int = 30

    # Environment
    env: str = "development"
    log_level: str = "INFO"

    # hCaptcha
    hcaptcha_secret: str = ""

    # Email (Resend.com) — empty api_key = mock mode
    resend_api_key: str = ""
    email_from: str = "noreply@serce.app"
    email_verification_url: str = "http://localhost:3000/verify-email"
    password_reset_url: str = "http://localhost:3000/reset-password"
    email_verification_expire_hours: int = 24
    password_reset_expire_minutes: int = 60

    # SMS (SMSAPI.pl) — empty token = mock mode
    smsapi_token: str = ""
    smsapi_sender: str = "Serce"
    phone_otp_expire_minutes: int = 10
    phone_otp_max_attempts: int = 5

    @model_validator(mode="after")
    def _check_secret_key_in_prod(self) -> "Settings":
        if self.env not in ("development", "test") and self.secret_key == _INSECURE_DEFAULT_KEY:
            raise ValueError(
                "SECRET_KEY must be set to a secure random value in non-dev environments. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

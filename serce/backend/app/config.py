from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://serce:serce_dev@localhost:5432/serce"

    # JWT
    secret_key: str = "change-me-to-random-32-char-string"
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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

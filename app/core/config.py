from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Order & Inventory API"
    API_V1_STR: str = "/api/v1"
    
    # Security Configurations
    SECRET_KEY: str = "SUPER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # PostgreSQL Database Credentials
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ecommerce_db"
    POSTGRES_PORT: int = 5432

    @property
    def ASYNC_DATABASE_URI(self) -> str:
        """
        Constructs the asyncpg PostgreSQL connection string dynamically.
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
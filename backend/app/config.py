from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Expense Manager API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/expense_manager"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="EXPENSE_")


settings = Settings()

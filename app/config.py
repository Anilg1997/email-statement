from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://bankuser:bankpass@localhost:5432/bank_editor"
    host: str = "0.0.0.0"
    port: int = 8080
    secret_key: str = "change-me-to-a-random-secret-key"

    # SMTP defaults (can be overridden via API)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Bank Statement Service"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

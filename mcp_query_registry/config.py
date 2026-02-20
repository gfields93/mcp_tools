from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    oracle_user: str
    oracle_password: str
    oracle_dsn: str
    pool_min: int = Field(default=1)
    pool_max: int = Field(default=10)
    hard_max_rows: int = Field(default=2000)
    audit_log_path: str = Field(default="audit.log")
    environment: str = Field(default="local")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

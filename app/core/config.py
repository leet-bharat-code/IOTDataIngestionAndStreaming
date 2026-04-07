from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "iot_platform"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

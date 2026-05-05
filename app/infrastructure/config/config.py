from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_SCHEMA: str
    REDIS_URL: str = "redis://localhost:6379"
    CORS_ORIGINS: list[str] = []
    NAVER_SEARCH_CLIENT_ID: str = ""
    NAVER_SEARCH_CLIENT_SECRET: str = ""
    NAVER_DATALAB_CLIENT_ID: str = ""
    NAVER_DATALAB_CLIENT_SECRET: str = ""
    NAVER_MAP_CLIENT_ID: str = ""
    NAVER_MAP_CLIENT_SECRET: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    SERVICE_NAME: str = "MJE"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_SCHEMA}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

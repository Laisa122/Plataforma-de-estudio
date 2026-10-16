"""Configuración global de la aplicación StudySync.

Carga variables de entorno utilizando Pydantic Settings v2.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Clase de configuración con valores por defecto y lectura de entorno."""

    APP_NAME: str = "StudySync"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "cambia-esta-clave-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./studysync.db"

    # Configuración de servidor SMTP para envío de correos
    SMTP_HOST: str = "sandbox.smtp.mailtrap.io"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@studysync.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Retorna una instancia cacheada de la configuración de la aplicación."""
    return Settings()

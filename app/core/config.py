from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class ClerkSettings(EnvBaseSettings):
    PUBLISHABLE_KEY_PATH: str = "app/keys/JWKS_PUBLISHABLE.pem"
    JWT_ALGORITHM: str = "RS256"
    JWT_VERIFICATION: bool = True


class ModelSettings(EnvBaseSettings):
    MODEL_PATH: str = "app/models/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    IMAGE_WIDTH: int = 640
    IMAGE_HEIGHT: int = 640


class ServerSettings(EnvBaseSettings):
    PROJECT: str = "Chroma-Worker"
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class Settings(ClerkSettings, ModelSettings, ServerSettings):
    pass


settings = Settings()

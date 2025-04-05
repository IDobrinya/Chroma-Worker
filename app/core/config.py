from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class ClerkSettings(EnvBaseSettings):
    PUBLISHABLE_KEY_PATH: str = "app/keys/PUBLISHABLE.pem"
    JWT_ALGORITHM: str = "RS256"
    JWT_VERIFICATION: bool = True


class ModelSettings(EnvBaseSettings):
    MODEL_PATH: str = "app/models/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    IMAGE_WIDTH: int = 640
    IMAGE_HEIGHT: int = 640


class ServerSettings(EnvBaseSettings):
    PROJECT: str = "Chroma-Worker"
    HOST: str = "localhost"
    PORT: int = 80


class Settings(ClerkSettings, ModelSettings, ServerSettings):
    SAVE_RESULTS: bool = False
    RESULTS_FOLDER: str = "results"


settings = Settings()

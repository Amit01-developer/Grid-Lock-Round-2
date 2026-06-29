from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "TraffiSense AI"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", pattern="^(development|staging|production|test)$")
    debug: bool = False

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/traffisense_ai"
    )
    db_pool_size: int = Field(default=10, ge=1, le=50)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_auto_create_tables: bool = False

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    upload_dir: Path = BACKEND_DIR / "storage" / "uploads"
    max_upload_mb: int = Field(default=20, ge=1, le=100)
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]

    ai_processing_enabled: bool = False
    yolo_model_path: Path | None = None
    yolo_confidence_threshold: float = Field(default=0.35, ge=0.05, le=0.95)
    yolo_image_size: int = Field(default=960, ge=320, le=1920)
    ocr_languages: list[str] = ["en"]
    ocr_min_confidence: float = Field(default=0.25, ge=0.0, le=1.0)
    evidence_dir_name: str = "evidence"

    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", "allowed_image_types", "ocr_languages", mode="before")
    @classmethod
    def split_csv(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("yolo_model_path", mode="before")
    @classmethod
    def empty_path_as_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        if value.startswith("postgresql://") and "+psycopg" not in value:
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("sqlite:///./"):
            relative_path = value.removeprefix("sqlite:///./")
            return f"sqlite:///{BACKEND_DIR / relative_path}"
        return value

    @field_validator("upload_dir", "yolo_model_path", mode="after")
    @classmethod
    def resolve_backend_relative_path(cls, value: Path | None) -> Path | None:
        if value is None:
            return value
        return value if value.is_absolute() else BACKEND_DIR / value

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

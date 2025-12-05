import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

load_dotenv()


class Settings(BaseModel):
    """Central application configuration."""

    app_env: str = Field(default=os.getenv("APP_ENV", "local"))
    app_name: str = Field(default="google-authz")
    app_version: str = Field(default=os.getenv("APP_VERSION", "0.1.0"))

    sample_user_email: str = Field(default=os.getenv("SAMPLE_USER_EMAIL", "rion@pleasantmattress.com"))

    google_service_account_file: Path = Field(
        default=Path(os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "private/gworkspace-465416-361687040922.json"))
    )
    google_delegated_user: Optional[str] = Field(default=os.getenv("GOOGLE_WORKSPACE_DELEGATED_USER"))
    google_customer_id: Optional[str] = Field(default=os.getenv("GOOGLE_WORKSPACE_CUSTOMER_ID"))
    google_auth_schema: str = Field(default=os.getenv("GOOGLE_WORKSPACE_AUTH_SCHEMA", "Authorization"))

    request_timeout_seconds: int = Field(default=int(os.getenv("WORKSPACE_REQUEST_TIMEOUT", "30")))

    class Config:
        allow_population_by_field_name = True

    @field_validator("google_service_account_file")
    def validate_service_account_path(cls, value: Path) -> Path:
        if not value.exists():
            logging.getLogger(__name__).warning("Service account file %s was not found.", value)
        return value


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance so FastAPI dependency injection can reuse it."""
    delegated_user = os.getenv("GOOGLE_WORKSPACE_DELEGATED_USER")
    if not delegated_user:
        raise RuntimeError("GOOGLE_WORKSPACE_DELEGATED_USER must be set (try updating your .env).")
    return Settings()

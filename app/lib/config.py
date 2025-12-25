import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

load_dotenv()


def _split_env_list(name: str, default: str = "") -> List[str]:
    raw = os.getenv(name, default)
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


class Settings(BaseModel):
    """Central application configuration."""

    model_config = ConfigDict(validate_assignment=True)

    app_env: str = Field(default=os.getenv("APP_ENV", "local"))
    app_name: str = Field(default="google-authz")
    app_version: str = Field(default=os.getenv("APP_VERSION", "0.1.0"))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    sample_user_email: str = Field(default=os.getenv("SAMPLE_USER_EMAIL", "rion@pleasantmattress.com"))

    google_service_account_file: Path = Field(
        default=Path(os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "private/gworkspace-465416-361687040922.json"))
    )
    google_delegated_user: Optional[str] = Field(default=os.getenv("GOOGLE_WORKSPACE_DELEGATED_USER"))
    google_customer_id: Optional[str] = Field(default=os.getenv("GOOGLE_WORKSPACE_CUSTOMER_ID"))
    google_auth_schema: str = Field(default=os.getenv("GOOGLE_WORKSPACE_AUTH_SCHEMA", "Authorization"))
    additional_scopes: List[str] = Field(default_factory=lambda: _split_env_list("ADDITIONAL_SCOPES"))
    allowed_origins: List[str] = Field(default_factory=lambda: _split_env_list("ALLOWED_ORIGINS"))

    request_timeout_seconds: int = Field(default=int(os.getenv("WORKSPACE_REQUEST_TIMEOUT", "30")))
    authz_allowed_networks: List[str] = Field(
        default_factory=lambda: _split_env_list("AUTHZ_ALLOWED_NETWORKS", "0.0.0.0/0")
    )
    authz_rate_limit_requests: int = Field(default=int(os.getenv("AUTHZ_RATE_LIMIT_REQUESTS", "60")))
    authz_rate_limit_window_seconds: int = Field(default=int(os.getenv("AUTHZ_RATE_LIMIT_WINDOW_SECONDS", "60")))

    google_oauth_client_id: Optional[str] = Field(default=os.getenv("GOOGLE_OAUTH_CLIENT_ID"))
    google_oauth_client_secret: Optional[str] = Field(default=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"))
    google_oauth_redirect_uri: Optional[str] = Field(default=os.getenv("GOOGLE_OAUTH_REDIRECT_URI"))
    allowed_hosted_domain: Optional[str] = Field(default=os.getenv("ALLOWED_HOSTED_DOMAIN"))
    post_login_redirect_url: str = Field(default=os.getenv("POST_LOGIN_REDIRECT_URL", "/me"))
    oauth_state_cookie_name: str = Field(default=os.getenv("OAUTH_STATE_COOKIE_NAME", "ga_oauth_state"))
    oauth_state_ttl_seconds: int = Field(default=int(os.getenv("OAUTH_STATE_TTL_SECONDS", "600")))

    redis_url: Optional[str] = Field(default=os.getenv("REDIS_URL"))
    redis_location: str = Field(default=os.getenv("REDIS_LOCATION", "sidecar"))
    effectiveauth_ttl_seconds: int = Field(default=int(os.getenv("EFFECTIVEAUTH_TTL_SECONDS", "300")))
    cache_warm_threshold_seconds: int = Field(default=int(os.getenv("CACHE_WARM_THRESHOLD_SECONDS", "60")))

    session_signing_secret: Optional[str] = Field(default=os.getenv("SESSION_SIGNING_SECRET"))
    session_cookie_name: str = Field(default=os.getenv("SESSION_COOKIE_NAME", "ga_session"))
    session_ttl_seconds: int = Field(default=int(os.getenv("SESSION_TTL_SECONDS", "3600")))
    session_refresh_threshold_seconds: int = Field(
        default=int(os.getenv("SESSION_REFRESH_THRESHOLD_SECONDS", "300"))
    )
    session_cookie_secure: bool = Field(
        default=os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
        or os.getenv("APP_ENV", "local") not in {"local", "development"}
    )
    session_cookie_samesite: str = Field(default=os.getenv("SESSION_COOKIE_SAMESITE", "lax"))

    @field_validator("additional_scopes", mode="before")
    def parse_additional_scopes(cls, value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [scope.strip() for scope in value.split(",") if scope.strip()]
        if isinstance(value, (list, tuple)):
            parsed = []
            for scope in value:
                scope_str = str(scope).strip()
                if scope_str:
                    parsed.append(scope_str)
            return parsed
        return []

    @field_validator("allowed_origins", mode="before")
    def parse_allowed_origins(cls, value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, tuple)):
            parsed = []
            for origin in value:
                origin_str = str(origin).strip()
                if origin_str:
                    parsed.append(origin_str)
            return parsed
        return []

    @field_validator("authz_allowed_networks", mode="before")
    def parse_allowed_networks(cls, value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, (list, tuple)):
            parsed = []
            for entry in value:
                entry_str = str(entry).strip()
                if entry_str:
                    parsed.append(entry_str)
            return parsed
        return []

    @field_validator("google_service_account_file")
    def validate_service_account_path(cls, value: Path) -> Path:
        if not value.exists():
            logging.getLogger(__name__).warning("Service account file %s was not found.", value)
        return value


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance so FastAPI dependency injection can reuse it."""
    settings = Settings()
    missing = []
    if not settings.google_delegated_user:
        missing.append("GOOGLE_WORKSPACE_DELEGATED_USER")
    if not settings.google_oauth_client_id:
        missing.append("GOOGLE_OAUTH_CLIENT_ID")
    if not settings.google_oauth_client_secret:
        missing.append("GOOGLE_OAUTH_CLIENT_SECRET")
    if not settings.google_oauth_redirect_uri:
        missing.append("GOOGLE_OAUTH_REDIRECT_URI")
    if not settings.session_signing_secret:
        missing.append("SESSION_SIGNING_SECRET")
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing) + ". "
            "Update your .env or deployment secrets."
        )
    return settings

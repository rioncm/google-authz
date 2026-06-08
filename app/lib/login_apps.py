from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, Field, field_validator


class LoginApp(BaseModel):
    app: str
    display_name: str | None = None
    app_domains: list[str] = Field(default_factory=list)
    app_redirects: list[str] = Field(default_factory=list)
    session_cookie_domain: str | None = None
    required_login_permission: str | None = None

    @field_validator("app")
    @classmethod
    def normalize_app(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("app is required")
        return normalized

    @field_validator("app_domains", "app_redirects", mode="before")
    @classmethod
    def normalize_string_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("value must be a string or list of strings")

    @field_validator("app_domains")
    @classmethod
    def normalize_domains(cls, value: list[str]) -> list[str]:
        return [domain.lower() for domain in value]

    @field_validator("app_redirects")
    @classmethod
    def validate_redirects(cls, value: list[str]) -> list[str]:
        redirects: list[str] = []
        for redirect in value:
            parsed = urlparse(redirect)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("app_redirects must be absolute https URLs")
            if parsed.username or parsed.password:
                raise ValueError("app_redirects must not include user info")
            redirects.append(redirect)
        return redirects


class LoginAppRegistry:
    def __init__(self, apps: list[LoginApp] | None = None) -> None:
        self._apps = {app.app: app for app in apps or []}

    @classmethod
    def from_file(cls, path: Path) -> "LoginAppRegistry":
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        if not isinstance(payload, dict):
            raise ValueError("login apps config must be a mapping")
        raw_apps = payload.get("login_apps") or []
        if not isinstance(raw_apps, list):
            raise ValueError("login_apps must be a list")
        return cls([LoginApp.model_validate(app) for app in raw_apps])

    def validate_redirect(self, app_name: str, redirect_uri: str) -> LoginApp:
        app = self._apps.get(app_name.strip().lower())
        if app is None:
            raise ValueError("Unknown login app")

        parsed = urlparse(redirect_uri)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("redirect_uri must be an absolute https URL")
        if parsed.username or parsed.password:
            raise ValueError("redirect_uri must not include user info")
        if redirect_uri not in app.app_redirects:
            raise ValueError("redirect_uri is not approved for this app")
        if app.app_domains and parsed.hostname and parsed.hostname.lower() not in app.app_domains:
            raise ValueError("redirect_uri host is not approved for this app")
        return app

    def cookie_domains(self) -> set[str]:
        return {app.session_cookie_domain for app in self._apps.values() if app.session_cookie_domain}

    def as_dict(self) -> dict[str, Any]:
        return {"login_apps": [app.model_dump() for app in self._apps.values()]}

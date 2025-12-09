import time
import uuid
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response
from jose import JWTError, jwt
from pydantic import BaseModel

from app.lib.config import Settings


class InternalSession(BaseModel):
    session_id: str
    subject: str
    email: str
    cache_key: str
    issued_at: int
    expires_at: int


class SessionError(Exception):
    """Raised when session cookies are invalid or expired."""


class SessionManager:
    """Issue and validate internal JWT sessions."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.session_signing_secret or ""
        self._ttl = settings.session_ttl_seconds
        self._cookie_name = settings.session_cookie_name
        self._secure_cookie = settings.session_cookie_secure
        cookie_policy = (settings.session_cookie_samesite or "").lower()
        if not cookie_policy:
            cookie_policy = "none" if self._secure_cookie else "lax"
        if self._secure_cookie and cookie_policy == "lax":
            cookie_policy = "none"
        self._samesite = cookie_policy
        self._refresh_threshold = settings.session_refresh_threshold_seconds
        self._algorithm = "HS256"

    def create_session(self, subject: str, email: str, cache_key: str) -> InternalSession:
        issued_at = int(time.time())
        expires_at = issued_at + self._ttl
        return InternalSession(
            session_id=str(uuid.uuid4()),
            subject=subject,
            email=email,
            cache_key=cache_key,
            issued_at=issued_at,
            expires_at=expires_at,
        )

    def encode(self, session: InternalSession) -> str:
        payload = session.model_dump()
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> InternalSession:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            session = InternalSession(**payload)
        except JWTError as exc:
            raise SessionError("Invalid session token") from exc
        if session.expires_at <= int(time.time()):
            raise SessionError("Session expired")
        return session

    def set_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=self._cookie_name,
            value=token,
            httponly=True,
            secure=self._secure_cookie,
            samesite=self._samesite,
            max_age=self._ttl,
            path="/",
        )

    def clear_cookie(self, response: Response) -> None:
        response.delete_cookie(key=self._cookie_name, path="/")

    def get_token_from_request(self, request: Request) -> Optional[str]:
        return request.cookies.get(self._cookie_name)

    def requires_refresh(self, session: InternalSession) -> bool:
        return (session.expires_at - int(time.time())) <= self._refresh_threshold


async def require_session_token(request: Request, manager: SessionManager) -> InternalSession:
    token = manager.get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token")
    try:
        return manager.decode(token)
    except SessionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

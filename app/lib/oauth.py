import secrets
from typing import Dict, Literal, Optional, Tuple, cast
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from fastapi.responses import Response
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import httpx
from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer

from app.lib.config import Settings

CookieSameSite = Literal["lax", "strict", "none"]
ALLOWED_SAMESITE_VALUES: Tuple[CookieSameSite, ...] = ("lax", "strict", "none")
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class OAuthState:
    def __init__(self, state: str, nonce: str) -> None:
        self.state = state
        self.nonce = nonce


class OAuthStateManager:
    """Signed cookie helper for OAuth state + nonce."""

    def __init__(self, settings: Settings) -> None:
        self._serializer = URLSafeTimedSerializer(
            settings.session_signing_secret or "",
            salt="google-authz-oauth",
        )
        self._cookie_name = settings.oauth_state_cookie_name
        self._cookie_max_age = settings.oauth_state_ttl_seconds
        self._secure_cookie = settings.session_cookie_secure
        raw_samesite = (settings.session_cookie_samesite or "").lower()
        if raw_samesite in ALLOWED_SAMESITE_VALUES:
            matched_samesite = cast(CookieSameSite, raw_samesite)
        else:
            matched_samesite = None
        self._samesite: Optional[CookieSameSite] = matched_samesite

    def generate(self) -> OAuthState:
        return OAuthState(state=secrets.token_urlsafe(32), nonce=secrets.token_urlsafe(32))

    def save_to_response(self, response: Response, state: OAuthState) -> None:
        token = self._serializer.dumps({"state": state.state, "nonce": state.nonce})
        response.set_cookie(
            key=self._cookie_name,
            value=token,
            max_age=self._cookie_max_age,
            httponly=True,
            secure=self._secure_cookie,
            samesite=self._samesite,
            path="/",
        )

    def clear_cookie(self, response: Response) -> None:
        response.delete_cookie(self._cookie_name, path="/")

    def load_from_request(self, request: Request) -> Optional[OAuthState]:
        token = request.cookies.get(self._cookie_name)
        if not token:
            return None
        try:
            payload = self._serializer.loads(token, max_age=self._cookie_max_age)
            return OAuthState(state=payload["state"], nonce=payload["nonce"])
        except (BadSignature, BadTimeSignature):
            return None


class OAuthService:
    """Handles Google OAuth flow + ID token validation."""

    # Use fully-qualified Google scopes so OAuth consent doesn't rewrite them at runtime
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self, settings: Settings, state_manager: OAuthStateManager) -> None:
        self._settings = settings
        self._state_manager = state_manager
        self._client_config: Dict[str, Dict[str, str]] = {
            "web": {
                "client_id": settings.google_oauth_client_id or "",
                "project_id": "google-authz",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_secret": settings.google_oauth_client_secret or "",
            }
        }

    def _build_flow(self) -> Flow:
        flow = Flow.from_client_config(self._client_config, scopes=self.SCOPES)
        flow.redirect_uri = self._settings.google_oauth_redirect_uri
        return flow

    def build_authorization_url(self, state: OAuthState) -> str:
        flow = self._build_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state.state,
        )
        allowed_domain = self._settings.allowed_hosted_domain
        if allowed_domain:
            separator = "&" if "?" in auth_url else "?"
            domain_query = urlencode({"hd": allowed_domain})
            auth_url = f"{auth_url}{separator}{domain_query}"
        return auth_url

    def exchange_code_for_user(self, code: str, expected_state: OAuthState) -> Dict[str, str]:
        flow = self._build_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        credential_id_token = getattr(credentials, "id_token", None)
        if not credential_id_token:
            raise HTTPException(status_code=400, detail="Missing ID token in OAuth response.")
        request = GoogleRequest()
        audiences = self._allowed_audiences()
        token_info = id_token.verify_oauth2_token(
            credential_id_token,
            request,
            audiences[0] if len(audiences) == 1 else audiences,
        )
        return self._validate_token_info(token_info, expected_state)

    def verify_id_token(self, raw_token: str) -> Dict[str, str]:
        request = GoogleRequest()
        audiences = self._allowed_audiences()
        token_info = id_token.verify_oauth2_token(
            raw_token,
            request,
            audiences[0] if len(audiences) == 1 else audiences,
        )
        return self._validate_token_info(token_info, None)

    def verify_access_token(self, raw_token: str) -> Dict[str, str]:
        token_info = self._fetch_access_token_info(raw_token)
        email = token_info.get("email")
        if not email:
            userinfo = self._fetch_userinfo(raw_token)
            token_info.update({k: v for k, v in userinfo.items() if v is not None})
            email = token_info.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Access token missing email.")
        self._validate_access_token_info(token_info)
        return token_info

    def _validate_token_info(self, token_info: Dict[str, str], expected_state: Optional[OAuthState]) -> Dict[str, str]:
        hosted_domain = token_info.get("hd")
        if self._settings.allowed_hosted_domain and hosted_domain != self._settings.allowed_hosted_domain:
            raise HTTPException(status_code=403, detail="Workspace domain is not allowed.")
        if expected_state:
            token_state = token_info.get("state")
            if token_state and token_state != expected_state.state:
                raise HTTPException(status_code=400, detail="OAuth state mismatch.")
            token_nonce = token_info.get("nonce")
            if token_nonce and token_nonce != expected_state.nonce:
                raise HTTPException(status_code=400, detail="OAuth nonce mismatch.")
        return token_info

    def _validate_access_token_info(self, token_info: Dict[str, str]) -> None:
        email = token_info.get("email") or ""
        if self._settings.allowed_hosted_domain:
            domain = email.split("@")[-1] if "@" in email else ""
            if domain != self._settings.allowed_hosted_domain:
                raise HTTPException(status_code=403, detail="Workspace domain is not allowed.")

    def _fetch_access_token_info(self, raw_token: str) -> Dict[str, str]:
        response = httpx.get(
            TOKENINFO_URL,
            params={"access_token": raw_token},
            timeout=5.0,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        return response.json()

    def _fetch_userinfo(self, raw_token: str) -> Dict[str, str]:
        response = httpx.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {raw_token}"},
            timeout=5.0,
        )
        if response.status_code != 200:
            return {}
        return response.json()

    def _allowed_audiences(self) -> list[str]:
        audiences = [self._settings.google_oauth_client_id or ""]
        audiences.extend(self._settings.google_oauth_allowed_audiences or [])
        return [aud for aud in audiences if aud]

    @property
    def state_manager(self) -> OAuthStateManager:
        return self._state_manager

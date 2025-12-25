import asyncio
import logging
import random
from contextlib import asynccontextmanager
from typing import Dict, List, Tuple

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, model_validator

from app.lib.cache import EffectiveAuthCache, CacheRecord, build_cache
from app.lib.config import Settings, get_settings
from app.lib.logging_config import configure_logging
from app.lib.models import EffectiveAuth, WorkspaceAuthResponse
from app.lib.oauth import OAuthService, OAuthStateManager
from app.lib.network import NetworkACL
from app.lib.rate_limit import RateLimiter
from app.lib.session import InternalSession, SessionManager, require_session_token
from app.lib.workspace import (
    WorkspaceAuthorizationService,
    WorkspaceDirectoryClient,
    WorkspaceError,
)

logger = logging.getLogger(__name__)

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    directory_client = WorkspaceDirectoryClient(settings)
    workspace_service = WorkspaceAuthorizationService(directory_client, settings)
    cache = await build_cache(settings)
    session_manager = SessionManager(settings)
    oauth_state_manager = OAuthStateManager(settings)
    oauth_service = OAuthService(settings, oauth_state_manager)
    network_acl = NetworkACL(settings.authz_allowed_networks or ["0.0.0.0/0"])
    rate_limiter = RateLimiter(settings.authz_rate_limit_requests, settings.authz_rate_limit_window_seconds)

    app.state.settings = settings
    app.state.workspace_service = workspace_service
    app.state.auth_cache = cache
    app.state.session_manager = session_manager
    app.state.oauth_service = oauth_service
    app.state.network_acl = network_acl
    app.state.rate_limiter = rate_limiter

    logger.info("Application startup complete. Cache backend: %s", settings.redis_url or "in-memory")
    try:
        yield
    finally:
        await cache.close()
        logger.info("Cache backend closed. Shutdown complete.")


app = FastAPI(lifespan=lifespan, title=settings.app_name, version=settings.app_version)

if settings.allowed_origins:
    allow_credentials = True
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Authorization", "Content-Type"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )


RBAC_VERBS = {"create", "read", "update", "delete", "list", "approve", "manage"}


def error_payload(code: str, message: str) -> Dict[str, str]:
    return {"error": message, "error_code": code}


class TestAuthRequest(BaseModel):
    email: str | None = None


class AuthzTokenPayload(BaseModel):
    id_token: str | None = None
    session_token: str | None = None
    access_token: str | None = None

    @model_validator(mode="after")
    def validate_token_choice(self):
        tokens = [bool(self.id_token), bool(self.session_token), bool(self.access_token)]
        if sum(tokens) != 1:
            raise ValueError("Provide exactly one of id_token, session_token, or access_token.")
        return self


class AuthzRequest(AuthzTokenPayload):
    pass


class AuthzResponse(BaseModel):
    effective_auth: EffectiveAuth
    source: str


class AuthzCheckRequest(AuthzTokenPayload):
    module: str
    action: str

    @field_validator("module")
    @classmethod
    def validate_module(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("module is required.")
        return value

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in RBAC_VERBS:
            raise ValueError("action must be a valid RBAC verb.")
        return normalized


class AuthzCheckResponse(BaseModel):
    authorized: bool
    decision: str
    evaluated_permission: str
    permitted_actions: List[str]
    source: str
    reason: str | None = None


class SessionMetadata(BaseModel):
    issued_at: int
    expires_at: int
    requires_refresh: bool


class SessionResponse(BaseModel):
    effective_auth: EffectiveAuth
    cache_status: str
    session: SessionMetadata


class SessionRefreshRequest(BaseModel):
    force: bool = True


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_workspace_service(request: Request) -> WorkspaceAuthorizationService:
    return request.app.state.workspace_service


def get_cache(request: Request) -> EffectiveAuthCache:
    return request.app.state.auth_cache


def get_session_manager(request: Request) -> SessionManager:
    return request.app.state.session_manager


def get_oauth_service(request: Request) -> OAuthService:
    return request.app.state.oauth_service


def get_network_acl(request: Request) -> NetworkACL:
    return request.app.state.network_acl


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def cache_key_for_email(email: str) -> str:
    return f"auth:{email.lower()}"


def get_request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
        if candidate:
            return candidate
    if request.client and request.client.host:
        return request.client.host
    return None


def ensure_origin_allowed(request: Request, allowed_origins: List[str]) -> None:
    if not allowed_origins:
        return
    origin = request.headers.get("origin") or request.headers.get("Origin")
    if not origin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload("origin_required", "Origin header required."),
        )
    if origin not in allowed_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload("origin_not_allowed", "Origin is not allowed."),
        )


async def enforce_authz_request_guards(
    request: Request,
    network_acl: NetworkACL,
    rate_limiter: RateLimiter,
) -> str:
    client_ip = get_request_ip(request)
    if not client_ip:
        logger.warning("Rejecting authz request without client IP.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload("ip_missing", "Client network not allowed."),
        )
    if not network_acl.is_allowed(client_ip):
        logger.warning("Rejecting authz request from disallowed IP %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload("network_not_allowed", "Client network not allowed."),
        )
    allowed = await rate_limiter.allow(client_ip)
    if not allowed:
        logger.warning("Rate limit exceeded for %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_payload("rate_limited", "Rate limit exceeded."),
        )
    return client_ip


async def resolve_effective_auth_for_cache_key(
    email: str,
    cache_key: str,
    cache: EffectiveAuthCache,
    workspace_service: WorkspaceAuthorizationService,
    settings: Settings,
) -> Tuple[EffectiveAuth, str]:
    record: CacheRecord | None = await cache.get(cache_key)
    if record:
        ttl_remaining = record.ttl_remaining
        if ttl_remaining > settings.cache_warm_threshold_seconds:
            return record.effective_auth, "cache_hit"
        logger.info(
            "Cache warm refresh for %s (remaining TTL %.0fs < threshold %ss)",
            email,
            ttl_remaining,
            settings.cache_warm_threshold_seconds,
        )
    effective_auth = await fetch_and_cache_effective_auth(
        email, workspace_service, cache, settings.effectiveauth_ttl_seconds, cache_key=cache_key
    )
    status_label = "cache_refresh" if record else "cache_miss"
    return effective_auth, status_label


def map_cache_source(status_label: str) -> str:
    return "cache" if status_label == "cache_hit" else "refreshed"


def normalize_permission_parts(module: str, action: str) -> Tuple[str, str]:
    normalized_module = WorkspaceAuthorizationService._slugify(module)
    normalized_action = action.strip().lower()
    return normalized_module, normalized_action


def gather_module_permissions(effective_auth: EffectiveAuth, module: str) -> List[str]:
    prefix = f"{module}:"
    return sorted(perm for perm in effective_auth.permissions if perm.startswith(prefix))


def permission_eval_response(
    authorized: bool,
    evaluated_permission: str,
    permitted_actions: List[str],
    cache_source: str,
    reason: str | None = None,
) -> AuthzCheckResponse:
    decision = "granted" if authorized else "denied"
    return AuthzCheckResponse(
        authorized=authorized,
        decision=decision,
        evaluated_permission=evaluated_permission,
        permitted_actions=permitted_actions,
        source=cache_source,
        reason=reason,
    )


def build_session_response(
    session: InternalSession,
    effective_auth: EffectiveAuth,
    cache_status: str,
    session_manager: SessionManager,
) -> SessionResponse:
    metadata = SessionMetadata(
        issued_at=session.issued_at,
        expires_at=session.expires_at,
        requires_refresh=session_manager.requires_refresh(session),
    )
    return SessionResponse(effective_auth=effective_auth, cache_status=cache_status, session=metadata)


def resolve_identity_from_payload(
    payload: AuthzTokenPayload,
    session_manager: SessionManager,
    oauth_service: OAuthService,
) -> Tuple[str, str, str]:
    if payload.session_token:
        try:
            session = session_manager.decode(payload.session_token)
        except Exception as exc:
            logger.warning("Invalid session token supplied to /authz: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_payload("invalid_session_token", "Invalid session token."),
            ) from exc
        cache_key = session.cache_key or cache_key_for_email(session.email)
        return session.email.lower(), cache_key, "session"
    if payload.access_token:
        try:
            token_info = oauth_service.verify_access_token(payload.access_token)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Access token verification failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_payload("invalid_access_token", "Invalid access token."),
            ) from exc
        email = token_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_payload("missing_email_claim", "Access token missing email."),
            )
        return email.lower(), cache_key_for_email(email), "access_token"
    if not payload.id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_payload("missing_id_token", "id_token is required."),
        )
    try:
        token_info = oauth_service.verify_id_token(payload.id_token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("ID token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload("invalid_id_token", "Invalid ID token."),
        ) from exc
    email = token_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_payload("missing_email_claim", "ID token missing email claim."),
        )
    return email.lower(), cache_key_for_email(email), "id_token"


async def fetch_and_cache_effective_auth(
    email: str,
    workspace_service: WorkspaceAuthorizationService,
    cache: EffectiveAuthCache,
    ttl_seconds: int,
    cache_key: str | None = None,
    retries: int = 1,
) -> EffectiveAuth:
    attempt = 0
    while True:
        try:
            effective_auth, _, _ = await run_in_threadpool(workspace_service.fetch_effective_auth, email)
            break
        except WorkspaceError as exc:
            attempt += 1
            if attempt > retries:
                logger.exception("Workspace fetch failed for %s", email)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=error_payload("workspace_unavailable", str(exc)),
                ) from exc
            delay = random.uniform(0.2, 0.5)
            logger.warning("Workspace fetch retry %s for %s after %.2fs", attempt, email, delay)
            await asyncio.sleep(delay)
    key = cache_key or cache_key_for_email(effective_auth.email)
    await cache.set(key, effective_auth, ttl_seconds)
    return effective_auth


async def resolve_effective_auth_for_session(
    session: InternalSession,
    cache: EffectiveAuthCache,
    workspace_service: WorkspaceAuthorizationService,
    settings: Settings,
) -> Tuple[EffectiveAuth, str]:
    effective_auth, status = await resolve_effective_auth_for_cache_key(
        session.email,
        session.cache_key,
        cache,
        workspace_service,
        settings,
    )
    if status != "cache_hit":
        logger.info("Cache refresh for %s due to %s", session.email, status)
    return effective_auth, status


@app.get("/health")
def health(settings: Settings = Depends(get_app_settings)) -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env, "version": settings.app_version}


@app.get("/live")
def live() -> dict[str, str]:
    return {"status": "live"}


@app.post("/authz/test", response_model=WorkspaceAuthResponse)
async def get_authorization_profile(
    payload: TestAuthRequest,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
) -> WorkspaceAuthResponse:
    email = (payload.email or settings.sample_user_email).strip().lower()
    try:
        effective_auth, raw_user, raw_groups = await run_in_threadpool(
            workspace_service.fetch_effective_auth, email
        )
    except WorkspaceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return WorkspaceAuthResponse(
        requested_email=email,
        effective_auth=effective_auth,
        raw_user=raw_user,
        raw_groups=raw_groups,
    )


@app.get("/login")
async def login(oauth_service: OAuthService = Depends(get_oauth_service)) -> Response:
    state = oauth_service.state_manager.generate()
    auth_url = oauth_service.build_authorization_url(state)
    response = RedirectResponse(url=auth_url, status_code=303)
    oauth_service.state_manager.save_to_response(response, state)
    return response


@app.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str,
    state: str,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
    cache: EffectiveAuthCache = Depends(get_cache),
    session_manager: SessionManager = Depends(get_session_manager),
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> Response:
    stored_state = oauth_service.state_manager.load_from_request(request)
    if not stored_state or stored_state.state != state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")

    token_info = oauth_service.exchange_code_for_user(code, stored_state)
    email = token_info.get("email")
    subject = token_info.get("sub")
    if not email or not subject:
        raise HTTPException(status_code=400, detail="ID token missing required claims.")

    cache_key = cache_key_for_email(email)
    effective_auth = await fetch_and_cache_effective_auth(
        email, workspace_service, cache, settings.effectiveauth_ttl_seconds, cache_key=cache_key
    )

    session = session_manager.create_session(subject=subject, email=effective_auth.email, cache_key=cache_key)
    token = session_manager.encode(session)

    response = RedirectResponse(url=settings.post_login_redirect_url, status_code=303)
    session_manager.set_cookie(response, token)
    oauth_service.state_manager.clear_cookie(response)
    logger.info("Login success for %s (cache key %s)", effective_auth.email, cache_key)
    return response


@app.post("/logout")
async def logout(
    request: Request,
    response: Response,
    cache: EffectiveAuthCache = Depends(get_cache),
    session_manager: SessionManager = Depends(get_session_manager),
) -> Response:
    token = session_manager.get_token_from_request(request)
    if token:
        try:
            session = session_manager.decode(token)
            await cache.delete(session.cache_key)
        except Exception:
            logger.warning("Failed to decode session during logout.")
    session_manager.clear_cookie(response)
    response.status_code = 204
    return response


@app.get("/me")
async def me(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
    cache: EffectiveAuthCache = Depends(get_cache),
    session_manager: SessionManager = Depends(get_session_manager),
):
    session = await require_session_token(request, session_manager)
    effective_auth, cache_status = await resolve_effective_auth_for_session(
        session, cache, workspace_service, settings
    )
    return {"effective_auth": effective_auth, "cache_status": cache_status}


@app.get("/session", response_model=SessionResponse)
async def session_details(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
    cache: EffectiveAuthCache = Depends(get_cache),
    session_manager: SessionManager = Depends(get_session_manager),
):
    session = await require_session_token(request, session_manager)
    effective_auth, cache_status = await resolve_effective_auth_for_session(
        session, cache, workspace_service, settings
    )
    return build_session_response(session, effective_auth, cache_status, session_manager)


@app.post("/session/refresh", response_model=SessionResponse)
async def session_refresh(
    request: Request,
    payload: SessionRefreshRequest,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
    cache: EffectiveAuthCache = Depends(get_cache),
    session_manager: SessionManager = Depends(get_session_manager),
):
    ensure_origin_allowed(request, settings.allowed_origins)
    session = await require_session_token(request, session_manager)
    effective_auth = await fetch_and_cache_effective_auth(
        session.email,
        workspace_service,
        cache,
        settings.effectiveauth_ttl_seconds,
        cache_key=session.cache_key,
    )
    cache_status = "cache_refresh"
    return build_session_response(session, effective_auth, cache_status, session_manager)


@app.post("/authz", response_model=AuthzResponse)
async def authz(
    request: Request,
    payload: AuthzRequest,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
    cache: EffectiveAuthCache = Depends(get_cache),
    session_manager: SessionManager = Depends(get_session_manager),
    oauth_service: OAuthService = Depends(get_oauth_service),
    network_acl: NetworkACL = Depends(get_network_acl),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> AuthzResponse:
    client_ip = await enforce_authz_request_guards(request, network_acl, rate_limiter)
    email, cache_key, token_type = resolve_identity_from_payload(payload, session_manager, oauth_service)
    effective_auth, cache_status = await resolve_effective_auth_for_cache_key(
        email, cache_key, cache, workspace_service, settings
    )
    source_label = map_cache_source(cache_status)
    logger.info("Authz fetch for %s from %s (token=%s, source=%s)", email, client_ip, token_type, cache_status)
    return AuthzResponse(effective_auth=effective_auth, source=source_label)


@app.post("/authz/check", response_model=AuthzCheckResponse)
async def authz_check(
    request: Request,
    payload: AuthzCheckRequest,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
    cache: EffectiveAuthCache = Depends(get_cache),
    session_manager: SessionManager = Depends(get_session_manager),
    oauth_service: OAuthService = Depends(get_oauth_service),
    network_acl: NetworkACL = Depends(get_network_acl),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> Response | AuthzCheckResponse:
    client_ip = await enforce_authz_request_guards(request, network_acl, rate_limiter)
    email, cache_key, token_type = resolve_identity_from_payload(payload, session_manager, oauth_service)
    effective_auth, cache_status = await resolve_effective_auth_for_cache_key(
        email, cache_key, cache, workspace_service, settings
    )
    normalized_module, normalized_action = normalize_permission_parts(payload.module, payload.action)
    evaluated_permission = f"{normalized_module}:{normalized_action}"
    permitted_actions = gather_module_permissions(effective_auth, normalized_module)
    authorized = evaluated_permission in permitted_actions
    cache_source = map_cache_source(cache_status)
    result = permission_eval_response(
        authorized,
        evaluated_permission,
        permitted_actions,
        cache_source,
        reason=None if authorized else "permission_missing",
    )
    log_message = "granted" if authorized else "denied"
    logger.info(
        "Authz check %s for %s requesting %s (token=%s, source=%s, ip=%s)",
        log_message,
        email,
        evaluated_permission,
        token_type,
        cache_status,
        client_ip,
    )
    if authorized:
        return result
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=result.model_dump())

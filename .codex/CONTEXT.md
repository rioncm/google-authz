# google-authz Context

This repo is the server side of the shared Google Workspace authorization flow. It centralizes Google OAuth login, Workspace Directory lookups, EffectiveAuth caching, signed session cookies, and permission checks for internal apps.

## Current Shape

- FastAPI app entrypoint: `app/main.py`.
- Central settings: `app/lib/config.py`.
- Workspace lookup and EffectiveAuth construction: `app/lib/workspace.py`, `app/lib/models.py`.
- OAuth and state handling: `app/lib/oauth.py`.
- Signed session token/cookie handling: `app/lib/session.py`.
- Cache abstraction: `app/lib/cache.py`, with Redis or in-memory behavior.
- Browser app registry: `app/lib/login_apps.py`.
- Deployment examples: `kubernetes/`, `docs/kubernetes/`, and `docs/deployment.md`.
- Browser app login documentation: `docs/browser-app-login.md`.
- Endpoint docs: `docs/authz-endpoints.md`.

The Graphify knowledge graph lives in `graphify-out/`. The latest report at `graphify-out/GRAPH_REPORT.md` identifies the main hubs as `Settings`, `EffectiveAuth`, `WorkspaceAuthorizationService`, `OAuthService`, `SessionManager`, `WorkspaceDirectoryClient`, `OAuthStateManager`, and `EffectiveAuthCache`. Treat inferred graph edges as navigation hints, not proof.

## Auth Flows To Preserve

There are two separate auth patterns. Keep them separate in code and docs.

1. Existing token-based API authorization:
   - Callers already authenticated to Google Workspace, such as Apps Script, pass a Google OAuth access token.
   - Apps Script uses `ScriptApp.getOAuthToken()`.
   - Local APIs call this service through `google-authz-client` with `token_type="access_token"`.
   - `/authz` and `/authz/check` accept exactly one token field: `id_token`, `session_token`, or `access_token`.

2. Browser app login:
   - First-party browser apps enter through `GET /login/app?app=<app>&redirect_uri=<url>`.
   - `/login/app` validates the app id and exact redirect URL against a ConfigMap-backed YAML registry.
   - `LOGIN_APPS_CONFIG_FILE` defaults to `/etc/google-authz/login-apps.yaml`.
   - OAuth state carries the approved app redirect metadata through Google OAuth.
   - `/auth/callback` sets the configured session cookie and redirects back to the approved app URL.
   - Browser apps use the cookie value as a `session_token` for `/authz` and `/authz/check`.
   - The cookie contains a signed session token, not the full RBAC document.

Do not blur `/login/app` into existing `/login` behavior unless explicitly asked. The browser-login work was intentionally isolated to avoid breaking API-token callers.

## Important Contracts

- `AuthzTokenPayload` in `app/main.py` requires exactly one of `id_token`, `session_token`, or `access_token`.
- `/authz/check` validates actions against `RBAC_VERBS = {"create", "read", "update", "delete", "list", "approve", "manage"}`.
- `LoginAppRegistry.validate_redirect()` requires absolute HTTPS redirects, no userinfo, exact match in `app_redirects`, and host match in `app_domains` when configured.
- `required_login_permission` in login app config is currently a registry/documentation hint; consuming apps must still enforce their own entry permission.
- `Settings.get_settings()` raises on missing required environment variables, including Google OAuth config and `SESSION_SIGNING_SECRET`.
- Network ACLs and rate limits are part of `/authz` request guarding; do not silently bypass them in production code.

## Relationship To Client Repo

The sibling repo `../google-authz-client` contains the Python integration library. Server changes that affect request/response shape, token names, cookie assumptions, or permission semantics usually need matching client docs/tests.

Known compatibility rule: the client handles both nested `/authz` responses with `effective_auth` and older top-level permission payloads. Preserve that compatibility unless a breaking change is intentional and documented.

## Verification Notes

- Server tests may need an environment with FastAPI dependencies and test tools installed.
- Prior local verification used `conda run -n authz ...` for server import/test checks when available.
- Import-time settings require real or dummy required env vars because `app/main.py` calls `get_settings()` at module import.
- For graph navigation, start with `graphify-out/GRAPH_REPORT.md`, then inspect `graphify-out/graph.json` only when a precise edge/source is needed.

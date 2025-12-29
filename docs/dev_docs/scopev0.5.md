# scope v0.5 – Python Integration Library

## Objective
Ship an installable Python package that makes consuming google-authz trivial for FastAPI, Flask, and Django APIs. The library must expose dependency helpers so endpoints can express authorization requirements declaratively (e.g., `Depends(require_permission("inventory:read"))`).

## Requirements
1. **Package structure**
   - Name: `google_authz_client` (working title).
   - Pure-Python package published to internal artifact registry (PyPI-compatible).
   - Supports Python 3.10+.
   - Provides async + sync HTTP clients using `httpx` with pluggable base URL and timeouts.

2. **Core API**
   - `GoogleAuthzClient` with methods:
     - `fetch_effective_auth(id_token|session_token)` → `EffectiveAuth`.
     - `check_permission(module, action, token)` → returns bool + permitted actions.
   - Automatic token discovery:
     - FastAPI dependency to read cookies/header.
     - Flask/Django middlewares to extract session token or Authorization header.
   - Built-in caching (optional) per-request so multiple permission checks reuse the same `/authz` response.

3. **FastAPI helper dependencies**
   - `depends_current_user = Depends(current_user())` returning `EffectiveAuth`, raising HTTP 401/403 automatically.
   - `require_permission("module:action")` returning a dependency that:
     - Calls `/authz/check`.
     - Raises `HTTPException(403)` when denied.
     - Injects either the EffectiveAuth or permitted actions into the route function for further logic.
   - Support stacking multiple permission dependencies or providing a list (`any_of`, `all_of` helpers).

4. **Flask/Django decorators**
   - Decorator `@require_permission("module:action")` that wraps view functions, handling token extraction and 403 responses.
   - Middleware to attach `g.current_user` / `request.user` with EffectiveAuth if requested.

5. **Configuration**
   - Accepts base URL, TLS verification flag, and optional shared secret header (if future versions add one).
   - Built-in retry/backoff logic with sensible defaults.
   - Exposes typed settings object so frameworks can load from env vars easily.

6. **Developer experience**
   - README section with copy-paste examples:
     ```python
     from google_authz_client.fastapi import require_permission

     @router.post("/inventory", dependencies=[Depends(require_permission("inventory:create"))])
     async def create_item():
         ...
     ```
   - End-to-end sample application (FastAPI) using Depends helpers, included in `examples/`.
   - Type hints + mypy configuration.

7. **Testing**
   - Unit tests using mocked `/authz` responses.
   - Integration test hitting a local google-authz instance (docker-compose) verifying both fetch and check flows.
   - CI workflow for lint/test/publish.

## Non-Goals
- Frontend SDKs or JS helpers (future work).
- Automatic schema management (still configured in Admin Console).

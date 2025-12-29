# google-authz – v0.2 Local Notes

## Environment (.env)

Minimum variables for the login + caching flow (see `docs/config.md` for the full catalog):

```
APP_ENV=local
APP_VERSION=0.2.0
LOG_LEVEL=DEBUG

GOOGLE_SERVICE_ACCOUNT_FILE=private/gworkspace-465416-361687040922.json
GOOGLE_WORKSPACE_DELEGATED_USER=admin@pleasantmattress.com
GOOGLE_WORKSPACE_CUSTOMER_ID=C0123456
GOOGLE_WORKSPACE_AUTH_SCHEMA=Authorization

GOOGLE_OAUTH_CLIENT_ID=<workspace-oauth-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<workspace-oauth-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
ALLOWED_HOSTED_DOMAIN=pleasantmattress.com

SESSION_SIGNING_SECRET=<32+ random bytes>
SESSION_COOKIE_NAME=ga_session

SAMPLE_USER_EMAIL=rion@pleasantmattress.com
POST_LOGIN_REDIRECT_URL=/me

# Optional: point at a running Redis; omit to fall back to in-memory cache.
# REDIS_URL=redis://localhost:6379/0
```

The `private/` directory is git-ignored—drop your Workspace service-account JSON there for local runs. The OAuth client (ID/secret/redirect URI) must match an app configured in the Google Cloud console with `http://localhost:8000/auth/callback` registered.

## Running the FastAPI app

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Manual flow

1. Navigate to `http://localhost:8000/login`. You’ll be redirected to Workspace SSO; the app sets an ephemeral state/nonce cookie.
2. After Google redirects back to `/auth/callback`, the server validates the ID token, fetches Workspace attributes, stores the normalized `EffectiveAuth` in cache (Redis or in-memory), issues an internal JWT cookie, and redirects to `/me`.
3. `GET /me` returns the cached `EffectiveAuth` plus a cache status (`cache_hit`, `cache_miss`, or `cache_refresh`). Repeated calls should stay in-cache until the TTL expires.
4. `POST /logout` clears the internal session cookie and evicts the cached `EffectiveAuth`. Call `/login` again to restart the flow.

Additional endpoints:
- `GET /health` – readiness probe.
- `GET /live` – liveness probe.
- `POST /authz/test` – still available for manual lookups with `{ "email": "user@example.com" }`, bypassing the login flow for debugging.

# Browser App Login

`google-authz` supports two authentication/authorization patterns:

- Token-based API authorization for callers that are already authenticated to Google Workspace, such as Apps Script passing `ScriptApp.getOAuthToken()` to an internal API.
- Browser app login for first-party web apps that need AuthZ to establish a session and redirect users back to the app.

Browser app login is isolated on `GET /login/app` so the existing `/login`, `/authz`, and `/authz/check` behavior remains non-breaking.

## Flow

1. A user opens a first-party browser app such as Little Helpers.
2. The app sends unauthenticated users to:

```text
https://auth.pminc.me/login/app?app=helpers&redirect_uri=https%3A%2F%2Fhelpers.k8.pminc.me%2F
```

3. AuthZ validates `app` and `redirect_uri` against the server-owned login app registry.
4. AuthZ stores the approved app metadata in the signed OAuth state cookie.
5. AuthZ redirects the user to Google OAuth.
6. Google redirects back to AuthZ `/auth/callback`.
7. AuthZ fetches and caches the user's `EffectiveAuth`.
8. AuthZ creates a signed session token containing identity and lookup metadata.
9. AuthZ sets the configured session cookie and redirects to the approved app URL.
10. The app uses the cookie value as a `session_token` for `/authz` and `/authz/check`.

The cookie does not contain the full RBAC document. It contains a signed session token with fields such as subject, email, cache key, issued time, and expiry. RBAC data is resolved by AuthZ from cache or Google Workspace when the app calls `/authz`.

## Login App Registry

Browser apps are configured through a YAML registry, intended to be mounted from a Kubernetes ConfigMap. The default path is:

```text
/etc/google-authz/login-apps.yaml
```

Set `LOGIN_APPS_CONFIG_FILE` only when a different mount path is needed.

Example:

```yaml
login_apps:
  - app: helpers
    display_name: Little Helpers
    app_domains:
      - helpers.pminc.me
      - helpers.k8.pminc.me
    app_redirects:
      - https://helpers.pminc.me/
      - https://helpers.k8.pminc.me/
    session_cookie_domain: .pminc.me
    required_login_permission: helpers:login
```

Field notes:

- `app`: Stable application id passed to `/login/app`.
- `display_name`: Human-readable name for operators and docs.
- `app_domains`: Approved hostnames for the app.
- `app_redirects`: Exact approved redirect URLs. The requested `redirect_uri` must match one of these values.
- `session_cookie_domain`: Optional cookie domain for sibling subdomain apps, such as `.pminc.me`.
- `required_login_permission`: Optional documentation/future enforcement field. The app should still enforce its own entry permission.

## Endpoint

```http
GET /login/app?app=<app>&redirect_uri=<absolute_https_url>
```

Validation:

- `app` must exist in the registry.
- `redirect_uri` must be an absolute HTTPS URL.
- `redirect_uri` must not contain userinfo.
- `redirect_uri` must exactly match one of the app's `app_redirects`.
- The redirect host must be present in `app_domains` when domains are configured.

Invalid requests fail with HTTP 400 before Google OAuth begins.

## Consuming App Implementation

For a FastAPI browser app using `google-authz-client`:

```python
from google_authz_client.client import AsyncGoogleAuthzClient
from google_authz_client.fastapi import current_user, require_permission

authz_client = AsyncGoogleAuthzClient(
    base_url="https://auth.pminc.me",
    verify_tls=True,
    token_type="session_token",
)

current_user_dep = current_user(
    authz_client,
    cookie_name="ga_session",
)

login_required = require_permission(
    "helpers:login",
    client=authz_client,
    cookie_name="ga_session",
)
```

To build the login URL with the settings helper:

```python
from google_authz_client.config import GoogleAuthzSettings

settings = GoogleAuthzSettings(
    base_url="https://auth.pminc.me",
    token_type="session_token",
)

login_url = settings.login_app_url(
    "helpers",
    "https://helpers.k8.pminc.me/",
)
```

Applications should use `/authz` for menu construction and `/authz/check` or route dependencies for action enforcement. They should not decode the session cookie locally.

## Existing API Token Flow

The Apps Script/API flow remains unchanged:

1. Apps Script obtains a Google OAuth access token.
2. Apps Script sends `Authorization: Bearer <token>` to a local API endpoint.
3. The local API uses `google-authz-client` with `token_type="access_token"`.
4. The client calls `/authz` or `/authz/check`.
5. AuthZ validates the access token and evaluates Workspace RBAC.

Browser login does not replace this flow and does not require Apps Script clients to call `/login/app`.

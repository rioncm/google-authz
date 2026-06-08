# Helpers Login Integration Review

This document outlines recommended updates to `google-authz` and `google-authz-client` so browser applications such as Little Helpers can use the centralized login flow without adding application-specific workarounds.

## Context

Little Helpers delegates Google login and authorization to `google-authz`.

`google-authz` should be treated as a general authorization clearinghouse for multiple first-party applications. Each consuming application configures and uses the client library locally, but browser login starts with an HTTP request to the shared AuthZ server. That means redirect handling is a server-level trust decision, not only a client-library configuration concern.

The current production-critical use case is API authorization for applications whose callers are already authenticated to Google Workspace. For example, Apps Script obtains the current user's OAuth access token with `ScriptApp.getOAuthToken()`, passes it to an internal API in the `Authorization: Bearer ...` header, and that API uses `google-authz-client` with `token_type="access_token"` to enforce RBAC on local endpoints. Any browser-login enhancement must be non-breaking for this access-token validation flow.

The intended browser flow is:

1. User opens Little Helpers.
2. Little Helpers sends unauthenticated users to `https://auth.pminc.me/login/app?app=helpers&redirect_uri=...`.
3. `google-authz` completes Google OAuth.
4. `google-authz` sets a signed session cookie.
5. Browser returns to Little Helpers.
6. Little Helpers uses the session cookie as a `session_token` when calling `/authz`.
7. Little Helpers checks for `helpers:login` and renders the app shell.

The server already implements most of this workflow. The gaps are mainly around making the browser return path and session cookie usable by a sibling application domain, and aligning the Python client with the server's current response contract.

## Existing API Authorization Flow To Preserve

The existing API flow is:

1. User is already authenticated in a Google Workspace client such as Apps Script.
2. The Workspace client obtains an OAuth access token.
3. The Workspace client calls an internal API endpoint with `Authorization: Bearer <access_token>`.
4. The internal API uses `google-authz-client` with `token_type="access_token"`.
5. The client posts to `google-authz` `/authz` or `/authz/check`.
6. `google-authz` validates the token, derives Workspace RBAC, and returns the authorization decision.
7. The internal API allows or rejects the local endpoint request.

Compatibility requirements:

- Do not change the request contract for `/authz` or `/authz/check`.
- Do not change the meaning of `id_token`, `access_token`, or `session_token` payloads.
- Do not require browser cookies for API authorization.
- Do not require Apps Script or OSAS-style clients to call `/login`.
- Do not remove the existing `Authorization: Bearer ...` discovery behavior in the client library.
- Keep `token_type="access_token"` working exactly as it does today for Apps Script backed endpoints.

Browser login should be treated as an additional session-establishment flow, not a replacement for token-based API authorization.

## Browser Session And RBAC Lookup

The browser login cookie should not contain the full RBAC document.

The current server session model is appropriate:

1. OAuth callback validates the Google user.
2. AuthZ fetches and caches the user's `EffectiveAuth`.
3. AuthZ creates a signed internal session token containing identity and lookup metadata such as subject, email, cache key, issued time, and expiry.
4. AuthZ stores that signed token in the browser session cookie.
5. The consuming app sends the cookie value back to AuthZ as `session_token`.
6. `/authz` decodes the session token, uses email/cache key to retrieve or refresh `EffectiveAuth`, and returns the RBAC data.
7. `/authz/check` follows the same session-token identity path and returns an authorization decision.

This keeps the cookie small and avoids stale permission data living in the browser. Menus and actions in a browser app should be driven by `/authz` or `/authz/check` responses, not by decoding the cookie locally.

For Little Helpers, the consuming app should configure the client side of this flow as:

```text
GOOGLE_AUTHZ_TOKEN_TYPE=session_token
GOOGLE_AUTHZ_COOKIE_NAME=ga_session
```

The `/login/app` work should preserve the existing session token payload shape. Any approved app id, redirect URL, or cookie-domain metadata needed during OAuth should live in signed OAuth state or server-side app registry configuration, not in the long-lived RBAC identity model unless later needed for audit/debug.

## Current Gaps

### 1. Browser app login needs an app registry, not more redirect env vars

`google-authz` redirects after OAuth using `POST_LOGIN_REDIRECT_URL`, which defaults to `/me`.

That default is useful for manual testing and should remain the no-parameter `/login` behavior. For first-party browser applications, though, a single static redirect does not scale cleanly. AuthZ is a clearinghouse for multiple applications, so browser app login should be modeled as a separate flow with an explicit app registry.

Recommended update:

- Keep existing `/login` behavior unchanged for manual/default login.
- Add a dedicated browser app endpoint, tentatively `GET /login/app`.
- Require an application identifier such as `app=helpers`.
- Validate the requested app and redirect details against a server-side app registry loaded from a ConfigMap-backed YAML file.
- Persist only the approved app id and return URL in the signed OAuth state cookie and use it in `/auth/callback`.
- Reject unknown apps, unapproved domains, and unapproved redirect URLs with a clear 400 response before OAuth begins.
- Keep `/authz` and `/authz/check` focused on token validation and RBAC decisions.

Recommended ConfigMap-backed registry shape:

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

Notes:

- The exact field names can be adjusted, but the important model is an app-keyed registry owned by the AuthZ server deployment.
- `app_redirects` should be exact URLs when possible. Exact redirects are simpler to reason about than broad origin matching.
- `app_domains` can be used as an additional sanity check or to support future app-owned callback paths.
- `session_cookie_domain` may be global or app-specific. App-specific is more flexible if future apps live under different parent domains.
- `required_login_permission` is optional for AuthZ itself. Little Helpers can still enforce `helpers:login` locally after redirect. Keeping it in the registry may be useful for future AuthZ-side checks or documentation.

Recommended endpoint contract:

```http
GET /login/app?app=helpers&redirect_uri=https%3A%2F%2Fhelpers.k8.pminc.me%2F
```

Validation steps:

1. Load the app registry from the mounted ConfigMap file.
2. Find the requested `app`.
3. Parse and normalize the requested `redirect_uri`.
4. Confirm the redirect URL exactly matches one of the app's configured `app_redirects`.
5. Optionally confirm the redirect host is included in `app_domains`.
6. Store approved app id, redirect URL, and any cookie-domain metadata in the OAuth state cookie.
7. Redirect to Google OAuth.

Why server validation is required:

- The `/login/app` request is browser-controllable; anyone can craft `https://auth.pminc.me/login/app?app=helpers&redirect_uri=...`.
- The application's client-library configuration is not authoritative for that inbound browser request.
- Trusting the supplied URL without server validation creates an open redirect after a successful Google login.
- Validating at AuthZ keeps the central login service responsible for which first-party applications may receive authenticated users.
- Existing network restrictions protect AuthZ API access, but they do not replace redirect validation for browser-initiated login URLs.

The client library may help applications construct the login URL, but the AuthZ server should still independently validate the requested destination.

Endpoint shape recommendation:

- Prefer a dedicated `/login/app` endpoint for browser application login.
- Leave existing `/login` behavior unchanged.
- Do not require additional key exchange or app secrets for this flow; validation comes from the server-owned app registry.
- Token validation endpoints remain unchanged.

Non-breaking route behavior:

- `GET /login` with no return URL continues to use `POST_LOGIN_REDIRECT_URL`.
- `GET /login/app?app=<app>&redirect_uri=<url>` validates the app and redirect URL against the registry.
- Invalid return URLs fail before OAuth begins.
- `/authz`, `/authz/check`, `/session`, and `/me` keep their existing roles.

### 2. Session cookie domain should come from app-aware configuration

For a cookie issued by `auth.pminc.me` to be sent to `helpers.k8.pminc.me`, it must be scoped to a shared parent domain such as `.pminc.me`.

Current session settings cover cookie name, TTL, secure flag, and SameSite behavior. They do not expose cookie domain. For `/login/app`, cookie domain should be resolved from the validated app registry entry, with optional global defaults only where useful.

Recommended server update:

- Allow the browser app registry to declare `session_cookie_domain`.
- Pass the resolved domain as `domain=` when setting and clearing the session cookie.
- Leave the default empty/`None` for non-app login and local development so single-host deployments keep host-only cookies.
- Avoid adding one env var per app; the ConfigMap registry is the maintenance point for app-specific browser login behavior.

Recommended docs update:

- Document `session_cookie_domain` in the app registry schema.
- Note that sibling-subdomain browser apps require a parent-domain cookie.

Recommended Helpers registry entry:

```yaml
login_apps:
  - app: helpers
    session_cookie_domain: .pminc.me
```

`SameSite=None` is the conservative browser setting for cross-site or sibling-app auth flows. If testing confirms same-site subdomain navigation works with the existing policy, this can be narrowed, but the deployment should be explicit either way.

### 3. Client `/authz` parser does not match the server response

The server's documented `/authz` response shape is:

```json
{
  "effective_auth": {
    "email": "user@example.com",
    "functions": ["helpers:login"],
    "permissions": ["helpers:login"],
    "groups": [],
    "custom_schemas": {},
    "fetched_at": "2026-06-08T16:00:00"
  },
  "source": "cache"
}
```

The current Python client parser expects an older/different shape:

```json
{
  "subject": "user@example.com",
  "permissions": {
    "helpers": ["login"]
  }
}
```

This means applications using `current_user()` can fail or receive incomplete permissions when pointed at the current server contract.

Recommended client update:

- Parse the current server shape first: `payload["effective_auth"]`.
- Treat `email` as the subject when no explicit `subject` exists.
- Accept flat permission strings such as `["helpers:login"]`.
- Normalize permissions internally to the existing client model, for example:

```python
EffectiveAuth(
    subject="user@example.com",
    permissions={"helpers": ["login"]},
    raw=payload,
)
```

- Keep backward compatibility with the older top-level dict shape.
- Add tests for both response shapes.
- Verify that OSAS-style `token_type="access_token"` callers continue to pass `Authorization: Bearer ...` and receive the same route authorization behavior.

This preserves the current client API while making it compatible with the current server.

### 4. Client settings helper should expose token type

The server supports `id_token`, `session_token`, and `access_token`.

The client constructors support `token_type`, but the settings builder does not currently expose/pass it. Browser apps using the AuthZ session cookie need `session_token`.

Recommended client update:

- Add `token_type` to `GoogleAuthzSettings`.
- Load it from `GOOGLE_AUTHZ_TOKEN_TYPE`.
- Pass it through `build_client()` and `build_async_client()`.
- Default remains `id_token` for backward compatibility.
- Do not change explicit constructor usage such as `AsyncGoogleAuthzClient(token_type="access_token")`.

Recommended consuming-app configuration:

```text
GOOGLE_AUTHZ_TOKEN_TYPE=session_token
GOOGLE_AUTHZ_COOKIE_NAME=ga_session
```

### 5. FastAPI helper defaults do not match the server cookie name

The server defaults to `SESSION_COOKIE_NAME=ga_session`.

The FastAPI client helpers default to `cookie_name="session"`.

This is configurable by callers, so it is not blocking, but it makes the default browser session workflow less discoverable.

Recommended client/docs update:

- Keep helper defaults unchanged if backward compatibility matters.
- Document browser-session usage clearly:

```python
current_user(client, cookie_name="ga_session")
require_permission("helpers:login", client=client, cookie_name="ga_session")
```

Alternative:

- Change the helper default to `ga_session` in a major/minor release with clear release notes.

## Recommended Implementation Order

1. Server/deployment: add a ConfigMap-backed browser app login registry.
2. Server: add dedicated `/login/app` endpoint and keep existing `/login` behavior unchanged.
3. Server: validate requested app and redirect URL against the registry before OAuth begins.
4. Server: add `SESSION_COOKIE_DOMAIN` support, using app registry metadata where appropriate.
5. Server/client tests: prove existing access-token `/authz` and `/authz/check` behavior still works.
6. Client: update `/authz` parser to accept the current server response shape without changing request semantics.
7. Client: add `GOOGLE_AUTHZ_TOKEN_TYPE` support to settings builder.
8. Client/docs: optionally add a helper for constructing `/login/app?app=...&redirect_uri=...`.
9. Docs: update `docs/config.md`, `docs/authz-endpoints.md`, and client README/examples.

This order gets the browser login flow working first, then removes application workarounds.

## Proposed Acceptance Checks

Server/browser checks:

- Opening `https://helpers.k8.pminc.me/` redirects unauthenticated users to Little Helpers `/login`.
- Clicking Login with Google sends the browser to `https://auth.pminc.me/login/app?app=helpers&redirect_uri=...`.
- The AuthZ `/login/app` request validates `helpers` against the app registry.
- An unknown app is rejected before Google OAuth begins.
- An unapproved `/login/app?...&redirect_uri=...` URL is rejected before Google OAuth begins.
- After Google OAuth, the browser returns to `https://helpers.k8.pminc.me/`.
- Browser devtools show `ga_session` scoped to `.pminc.me`.
- Little Helpers receives `ga_session` and renders for a user with `helpers:login`.
- A user without `helpers:login` receives a clear 403/unauthorized page.

Client checks:

- OSAS-style `AsyncGoogleAuthzClient(token_type="access_token")` still sends access-token payloads.
- Apps Script style `Authorization: Bearer <google_oauth_token>` requests still authorize local API routes through `/authz/check`.
- `fetch_effective_auth()` parses the current server `/authz` shape.
- `fetch_effective_auth()` still parses the older top-level permission-map shape.
- `require_permission("helpers:login")` passes when `/authz/check` authorizes it.
- `GoogleAuthzSettings().build_async_client()` honors `GOOGLE_AUTHZ_TOKEN_TYPE=session_token`.

## Non-goals

- Do not move OAuth handling into Little Helpers.
- Do not make Little Helpers parse AuthZ internals long-term.
- Do not require every consuming app to hardcode raw `/authz` calls.
- Do not allow arbitrary unvalidated redirect URLs on `/login/app`.
- Do not trust client- or browser-supplied redirect URLs without server-side validation.
- Do not break the existing Apps Script and local API endpoint authorization path.
- Do not change `/authz` and `/authz/check` into browser-login endpoints.
- Do not require app-level key exchange for first-party browser app login.

## Open Questions

- Should the return parameter be named `redirect_uri` for familiarity, or `return_to` to distinguish it from Google OAuth's own callback URI?
- Should `app_redirects` require exact URL matches only, or should `app_domains` allow path-level flexibility?
- Should `session_cookie_domain` be global, app-specific, or both with app-specific override?
- Should AuthZ enforce `required_login_permission` during `/auth/callback`, or should consuming apps remain solely responsible for app-entry permissions?
- Should the client expose both flat permissions and module/action maps, or keep only the existing map-based model?
- Should `ga_session` become the client helper default cookie name, or remain explicit in consuming apps?

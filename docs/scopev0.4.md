# scope v0.4 – Application Completion & Multi-Client Support

## Objective
Finish the service so it can be the primary auth/authorization backend for React/Vite front ends and downstream FastAPI/Flask/Django APIs. v0.4 closes the remaining product gaps: browser session UX, OAuth token reuse across heterogeneous clients (Sheets, Docs add-ons), and deployment guidance for other teams.

## Requirements
1. **Frontend session workflow**
   - Define the browser interaction model for login/logout.
   - Provide a JSON endpoint (e.g., `GET /session`) that returns the current EffectiveAuth + session metadata so React apps can hydrate state after page refresh.
   - Expose a `POST /session/refresh` (or reuse `/me`) that forces cache refresh when TTL is near expiry.
   - Ensure session cookies are marked `SameSite=None; Secure` when served behind HTTPS so Vite/React apps hosted on different subdomains remain logged in.

2. **CORS & Origin controls**
   - Add configurable `ALLOWED_ORIGINS` env var (comma-separated) to set FastAPI `CORSMiddleware`.
   - Support both browser (cookie) and token-based calls to `/authz` when invoked from add-ons that cannot send cookies.
   - Document CSRF expectations (state parameter already in OAuth; ensure session endpoints reject non-JSON or missing Origin/CSRF token if necessary).

3. **OAuth token passthrough for 3rd-party front ends**
   - Provide a documented flow for add-ons (Google Sheets/Docs) that already have an ID token:
     - Example: add-on obtains Workspace ID token → calls `/authz/check` with module/action → caches permitted_actions client-side.
     - Clarify TTL expectations and refresh cadence.

4. **Operational hardening for `/authz`**
   - Metrics/logs for which modules/actions are requested (to detect missing permissions).
   - Configurable retry behavior when Workspace fetch fails (one retry with jitter, then propagate 502/504).
   - Better error payloads: include machine-readable `error_code`.

5. **Documentation & onboarding**
   - Step-by-step guide for:
     1. Configuring Google OAuth credentials.
     2. Creating Authorization & EmployeeInfo schemas.
     3. Deploying with Docker/K8s, including new env vars.
     4. Connecting a sample React app (login button → /session fetch).
     5. Connecting a server-side API that relies on `/authz/check`.
   - Provide diagrams (sequence diagram for login, permission check).

6. **Testing**
   - Integration tests covering the React flow (simulate browser session) and a Sheets-style token-only flow.
   - Unit tests for new configuration parsing (origins, session settings).
   - Smoke tests for `/authz` rate limiting + network ACL enforcement.

## Non-Goals
- Creating the reusable Python library (v0.5 covers that).
- Publishing the repo publicly (v0.6).

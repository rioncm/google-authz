# Project Instructions

## Primary Guidance
- Follow the programming [style guide](style_guide.md)

## Project Specific 

Use the real code and docs in this repo as the source of truth. The Graphify output is useful for orientation, but it includes inferred edges that must be verified against source before changing behavior.

## Working Style

- Stay narrowly scoped to the user-named file, endpoint, config, or behavior before broad repo exploration.
- Preserve the split between browser session login and access-token API authorization.
- When changing an endpoint contract, audit `../google-authz-client` for matching client behavior and tests.
- Do not invent fallback values for auth tokens, redirect URIs, permissions, or user-entered fields. Auth failures should be explicit.
- Keep route behavior backwards-compatible unless the user explicitly asks for a breaking change.
- Prefer small, focused tests around auth boundary changes.

## Server-Specific Guardrails

- Keep `/login/app` as the first-party browser app entrypoint and leave existing `/login`, `/authz`, and `/authz/check` semantics intact unless directed otherwise.
- Keep `/authz` and `/authz/check` accepting exactly one token field: `id_token`, `session_token`, or `access_token`.
- Keep Apps Script/local API callers on `token_type="access_token"`; they should not need `/login/app` or browser cookies.
- Keep browser apps on `token_type="session_token"` with the configured cookie name, normally `ga_session`.
- Do not decode or rely on session cookie contents in consuming apps; RBAC comes from `/authz` and `/authz/check`.
- Validate login app redirects with exact approved URLs and HTTPS-only behavior.
- Treat Kubernetes ConfigMap examples for `login-apps.yaml` as deployment-facing contract, not throwaway examples.

## Common Files

- `app/main.py`: FastAPI app, request/response models, endpoint behavior, guard helpers.
- `app/lib/config.py`: environment-backed settings and required-env checks.
- `app/lib/login_apps.py`: browser app registry and redirect validation.
- `app/lib/oauth.py`: Google OAuth and signed OAuth state flow.
- `app/lib/session.py`: internal signed session token and cookie support.
- `app/lib/workspace.py`: Google Workspace Directory and EffectiveAuth resolution.
- `docs/browser-app-login.md`: authoritative narrative for `/login/app`.
- `kubernetes/`: deployment manifests, including login app ConfigMap examples.

## Verification

- Before importing `app.main`, provide required env vars or use the repo's expected local environment.
- Use focused pytest runs when dependencies are available.
- If pytest is unavailable in the active environment, at least run a compile/import check with required env vars set and report the limitation.
- When validating browser login changes, cover both invalid redirect rejection and successful approved redirect state/cookie behavior.
- When validating token API changes, cover `access_token` callers so Apps Script-style workflows remain non-breaking.

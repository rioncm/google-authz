# google-authz – Environment Variables

These variables cover the “final form” of the service: Google Workspace login, Redis caching, internal JWT sessions, and operational knobs. Use `.env` for local dev (python-dotenv loads it) and Kubernetes secrets for production. Defaults shown below are suggestions—override as needed.

## Core App

| Variable | Description | Example |
| --- | --- | --- |
| `APP_ENV` | Deployment environment label. | `production`, `development`, `local` |
| `APP_VERSION` | Reported by `/health`. | `0.2.0` |
| `LOG_LEVEL` | Python logging level. | `INFO` |
| `HOST` / `PORT` | Bind interface/port for Gunicorn (Docker defaults to `0.0.0.0:8000`). | `0.0.0.0` / `8000` |
| `APP_MODULE` | ASGI module path for Gunicorn. | `app.main:app` |

## Google OAuth (Login Flow)

| Variable | Description | Example |
| --- | --- | --- |
| `GOOGLE_OAUTH_CLIENT_ID` | Web client ID from Google Cloud console. | `123.apps.googleusercontent.com` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Matching client secret (store in Secret). | `super-secret` |
| `GOOGLE_OAUTH_REDIRECT_URI` | Must match OAuth client (local default `http://localhost:8000/auth/callback`). | `https://auth.example.com/auth/callback` |
| `ALLOWED_HOSTED_DOMAIN` | Restrict logins to Workspace domain. | `pleasantmattress.com` |

## Workspace / Admin SDK

| Variable | Description | Example |
| --- | --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to mounted JSON credentials. | `/etc/credentials.json` |
| `GOOGLE_WORKSPACE_DELEGATED_USER` | Admin user for domain-wide delegation. | `admin@pleasantmattress.com` |
| `GOOGLE_WORKSPACE_CUSTOMER_ID` | Workspace customer ID used for Directory API. | `C0123456` |
| `GOOGLE_WORKSPACE_AUTH_SCHEMA` | Custom schema that holds Home Department, User Functions, etc. | `Authorization` |
| `ADDITIONAL_SCOPES` | Comma-separated Directory scopes appended to the defaults (EmployeeInfo + Authorization). Leave blank to use defaults only. | `https://www.googleapis.com/auth/admin.directory.user.readonly` |
| `WORKSPACE_REQUEST_TIMEOUT` | Seconds to wait on Admin SDK calls. | `30` |

## Redis / EffectiveAuth Cache

| Variable | Description | Example |
| --- | --- | --- |
| `REDIS_URL` | Connection string. Use `redis://localhost:6379/0` for dev or a hosted instance. | `redis://redis.google-authz:6379/0` |
| `REDIS_LOCATION` | Optional hint (“sidecar”, “external”) for logging/metrics. | `external` |
| `EFFECTIVEAUTH_TTL_SECONDS` | Cache lifetime for EffectiveAuth objects. | `300` |
| `CACHE_WARM_THRESHOLD_SECONDS` | When TTL drops below this, refresh from Workspace. | `60` |

## Sessions / Tokens

| Variable | Description | Example |
| --- | --- | --- |
| `SESSION_SIGNING_SECRET` | HMAC secret for internal JWT cookie (keep 32+ random bytes). | `base64string` |
| `SESSION_COOKIE_NAME` | Cookie name for internal session token. | `ga_session` |
| `SESSION_TTL_SECONDS` | Internal token lifetime. | `3600` |
| `SESSION_REFRESH_THRESHOLD_SECONDS` | When to refresh EffectiveAuth in cache relative to expiry. | `300` |

## Authorization Endpoint (/authz, /authz/check)

| Variable | Description | Example |
| --- | --- | --- |
| `AUTHZ_ALLOWED_NETWORKS` | IPv4 network ACL for `/authz` endpoints. Supports `*`/`0.0.0.0/0` (allow all), CIDRs (`10.0.0.0/16`), single hosts (`10.42.0.5`), comma-separated lists, and ranges using `start|end`. Defaults to open access—lock down in production. | `10.42.0.0/16,10.10.5.12,192.168.1.10|192.168.1.20` |
| `AUTHZ_RATE_LIMIT_REQUESTS` | Requests allowed per client IP within the window. | `60` |
| `AUTHZ_RATE_LIMIT_WINDOW_SECONDS` | Duration of the rate-limit window in seconds. | `60` |

## Frontend / CORS

| Variable | Description | Example |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | Comma-separated list of origins allowed via CORS. Required when serving React/Vite apps from a different host or when POSTing to `/session/refresh`. Leave blank to disable CORS. | `https://tools.example.com,https://admin.example.com` |

## Dev / Testing Helpers

| Variable | Description | Example |
| --- | --- | --- |
| `SAMPLE_USER_EMAIL` | Default email for `/authz/test`. | `rion@pleasantmattress.com` |
| `ENABLE_DEV_ROUTES` | Toggle extra debug routes. | `false` |

Mount the service account JSON into the container (Docker: `-v ~/.config/gworkspace.json:/secrets/sa.json:ro` and set `GOOGLE_SERVICE_ACCOUNT_FILE=/secrets/sa.json`). In Kubernetes, the sample manifests mount `google-service-secret` at `/etc/credentials.json`.

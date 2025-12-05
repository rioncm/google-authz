# v0.2 — Google Login + Session + Caching

Goal: End-to-end login flow and cached authorization.

Deliverables
	•	Implement OIDC login with Google Workspace:
		•	/login redirect – initiate OAuth 2.0 Authorization Code flow against Workspace (needs client_id, client_secret, redirect URI). Store nonce + state in signed cookie/session for CSRF protection.
		•	/auth/callback token exchange – exchange code for tokens via google-auth-oauthlib, persist ID token + refresh token (if granted) short term for debugging.
		•	ID token validation – verify signature, audience, issuer, nonce; enforce hd or hosted domain.
		•	Build EffectiveAuth from Workspace data on login – reuse WorkspaceAuthorizationService to hydrate EffectiveAuth immediately after successful login before setting session.
	•	Redis (or memory cache fallback) integration:
		•	Connection via url env var (e.g., REDIS_URL=redis://localhost:6379/0). Provide in-memory `dict` cache for local/dev when Redis unavailable.
		•	Store EffectiveAuth with TTL (configurable, default 5 minutes) keyed by user email or internal subject.
		•	Add cache metrics logging (hit/miss) for debugging.
	•	Internal JWT/session cookie:
		•	Issue signed internal token after login (HS256 secret from env; include EffectiveAuth cache key + expiry).
		•	HTTP-only, Secure (when not localhost), SameSite=Lax cookie; configurable name `GA_AUTH_TOKEN`.
		•	Middleware to validate internal session – decode JWT, check expiry, fetch EffectiveAuth from cache (refresh when ttl close to zero). Return 401/403 otherwise.
	•	Simple protected test endpoint:
		•	/me → returns EffectiveAuth for the current session, indicates cache hit/miss.
		•	Add `GET /logout` (optional) to clear cookie + cache entry for manual testing.
	•	Logging of login success/failure
		•	Log state validation failures, token exchange errors, Workspace fetch failures, session refresh events at INFO/WARN.

Implementation Notes
	1. OAuth client configuration:
		•	Needs Google Cloud OAuth client (Web) with redirect `http://localhost:8000/auth/callback`.
		•	Secrets supplied via dotenv (`GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`).
		•	Hosted domain restriction via `hd=pleasantmattress.com`.
		•	Store PKCE verifier + state in signed cookie (`itsdangerous` or FastAPI session middleware).
	2. Redis cache abstraction:
		•	Create `CacheBackend` protocol + implementations (`RedisCache`, `InMemoryCache`).
		•	Configurable TTL env var `EFFECTIVEAUTH_TTL_SECONDS`.
		•	Add background task to refresh cached EffectiveAuth when TTL < threshold?
	3. Session/token layer:
		•	Define `InternalSession` model (sub, email, issued_at, expires_at, cache_key).
		•	Use `python-jose` or `pyjwt` for signing.
		•	Rotate signing key via env `SESSION_SIGNING_SECRET` (must exist).
		•	Middleware attaches `request.state.effective_auth`.
	4. Error handling:
		•	Uniform error responses for auth failures.
		•	Rate-limit login attempts? (future, just log for now).

Open Questions / Decisions Needed
	1. OAuth client: do we already have client_id/secret + redirect URIs registered, or should we generate new ones? Where should secrets live in K8s?
	2. Redis: is external Redis available for dev/staging, or should we bundle docker-compose? Preferred config naming?
	3. Session lifetime: desired TTL for internal token vs EffectiveAuth cache (same or different?). Proposed defaults: session 1h, cache 5m. OK?
	4. Logout semantics: should `/logout` also revoke Google refresh tokens or just clear internal session?
	5. Do we need to support X-Internal-Token header for service-to-service calls in this sprint, or defer to v0.4?

Success Criteria
	•	A user logs into the app via Google → receives internal session → /me shows normalized EffectiveAuth.
	•	Refreshing the page does not refetch Workspace data unless TTL expires.

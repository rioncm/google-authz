# google-authz – Roadmap (v0.1 → v1.0)

v0.1 — Foundation & Local Prototyping

Goal: Running locally with minimal functionality and ability to fetch Workspace authorization data.

Deliverables
	•	Basic FastAPI or lightweight Python service scaffold:
	•	/health endpoint
    •   /live endpoint for kubernetes
	•	Project layout, logging setup, config loading
	•	Workspace integration:
	•	Load service account
	•	Call Admin SDK (Directory API) with domain-wide delegation
	•	Fetch:
	•	Basic user profile
	•	Custom Authorization schema attributes
	•	Group membership
	•	Initial EffectiveAuth object defined (schema only)
	•	Hard-coded test endpoint that:
	•	Accepts an email
	•	Returns raw Workspace data + mapped EffectiveAuth (no login yet)
	•	No caching
	•	No authentication flow
	•	Single process, local only

Success Criteria
	•	Can run uvicorn app.main:app and fetch authorization info from Workspace.
	•	Can map custom attributes → functions → permissions.

⸻

v0.2 — Google Login + Session + Caching

Goal: End-to-end login flow and cached authorization.

Deliverables
	•	Implement OIDC login with Google Workspace:
	•	/login redirect
	•	/auth/callback token exchange
	•	ID token validation
	•	Build EffectiveAuth from Workspace data on login
	•	Redis (or memory cache fallback) integration:
    •   Redis configuration from env settings
	•	Store EffectiveAuth with TTL
	•	Internal JWT/session cookie:
	•	Issue signed internal token after login
	•	Middleware to validate internal session
	•	Simple protected test endpoint:
	•	/me → returns EffectiveAuth
	•	Logging of login success/failure

Success Criteria
	•	A user logs into the app via Google → receives internal session → /me shows normalized EffectiveAuth.
	•	Refreshing the page does not refetch Workspace data unless TTL expires.

⸻

v0.3 — Standalone Authorization Endpoint

Goal: Allow other internal APIs to retrieve EffectiveAuth without handling login.

Deliverables
	•	/authz endpoint:
	•	Accepts a valid Workspace token or internal JWT.
	•	Validates Google token signature & issuer.
	•	Retrieves EffectiveAuth from cache (or fetches if missing).
	•	Access limited to internal trusted callers (network-level ACL, shared secret, or mTLS).
	•	Basic operational guardrails (rate limits, logging) specific to the new endpoint.

Success Criteria
	•	Another internal service can POST a Workspace ID token to /authz and get back EffectiveAuth.

⸻

v0.4 — Client Integration Library & Helpers

Goal: Make authorization and permission checks easy for downstream services without embedding that logic into google-authz itself.

Deliverables
	•	A small Python package (internal registry):
	•	Token validation helper
	•	Function to call /authz and return EffectiveAuth
	•	`get_current_user()` and `require_permission("module:action")` helpers for FastAPI/Flask apps
	•	Normalization rules documented (e.g., Permission attributes → permissions list, manager flag derivations)
	•	Example usage snippets and README updates

Success Criteria
	•	A second API can integrate with google-authz using only the library and minimal custom code.
	•	Permission checks happen inside client apps via the shared helpers.

⸻

v0.5 — Authorization Patterns & Samples

Goal: Demonstrate consistent, enforced authorization flows using the integration library.

Deliverables
	•	Reference implementations showing:
	•	Protecting endpoints with `require_permission`
	•	Handling derived permissions (dept manager flag, etc.) through configuration
	•	End-to-end tests that exercise 403 responses when permissions are missing
	•	Playbook documentation describing how internal teams should model permissions/custom attributes

Success Criteria
	•	Internal services or tools app can rely on documented patterns to implement permission enforcement confidently.

⸻

v0.6 — Hardening & Operational Maturity

Goal: Production readiness.

Deliverables
	•	Replace environment-variable secrets with proper secret storage (K3s secret, etc.)
	•	Structured logging with request IDs
	•	Rate limiting / throttling on Workspace fetches
	•	Improved error modes:
	•	Distinguish between Workspace outage vs. user profile issues
	•	Deployment-ready Docker image:
	•	Gunicorn + Uvicorn worker setup
	•	Health checks for K8s/LB
	•	Workspace API quota handling and caching guardrails

Success Criteria
	•	The service runs reliably under load, survives transient Workspace errors, and has predictable logging.

⸻

v0.7 — Configuration & Extensibility

Goal: Make the system flexible while avoiding scope creep.

Deliverables
	•	Configurable:
	•	Cache TTL
	•	Token lifetime
	•	Allowed audiences & issuers
	•	Mapping overrides for derived permissions (simple YAML or dict)
	•	Optional admin debug endpoints (internal only):
	•	/debug/auth-profile?email= (requires admin permission)

Success Criteria
	•	Environment/config files allow behavior adjustment without code changes.

⸻

v0.8 — Developer Experience

Goal: Ready for broader internal adoption.

Deliverables
	•	Developer documentation:
	•	How login works
	•	How authorization is derived from Workspace attributes
	•	How to use the standalone endpoint
	•	How to use the Python library
	•	OpenAPI docs for all endpoints
	•	Example “starter app” showing integration

Success Criteria
	•	A new internal dev can read docs and integrate google-authz in <30 minutes.

⸻

v0.9 — Security Review & Cleanup

Goal: Final polish before 1.0.

Deliverables
	•	Code review focused on:
	•	Token validation
	•	Input sanitization
	•	Permission enforcement
	•	Key rotation strategy
	•	Threat model summary (lightweight)
	•	Remove dead code, finalize types, simplify configuration

Success Criteria
	•	Security review yields no blocking issues.
	•	Codebase is stable, predictable, and fully aligned with scope.

⸻

v1.0 — Production Release

Goal: Stable, fully scoped, production-ready authorization layer.

Deliverables
	•	Fully validated production deployment in K3s
	•	Metrics endpoint (optional but beneficial)
	•	Finalized docs & architecture diagrams
	•	Versioned release of Python integration library

Success Criteria
	•	google-authz is the authoritative identity + authorization provider for the tools application
	•	Other internal services can reliably retrieve permissions from it
	•	Workspace attribute changes propagate correctly and predictably
	•	No missing features relative to scope

⸻

Summary Timeline

Version	Milestone
v0.1	Local prototype: fetch Workspace data
v0.2	Login + session + caching
v0.3	Authorization enforcement
v0.4	Standalone AuthZ endpoint
v0.5	Python integration library
v0.6	Hardening & operational maturity
v0.7	Configurability improvements
v0.8	Developer experience improvements
v0.9	Security + cleanup
v1.0	Production release


⸻

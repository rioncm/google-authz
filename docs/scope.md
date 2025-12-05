# google-authz – Scope Document

1. Overview

Working title: google-authz
Purpose: Provide a small, focused service that:
	1.	Uses Google Workspace for authentication (SSO).
	2.	Derives authorization decisions from Google Workspace data:
	•	Full user profile & custom attributes (e.g. the Authorization schema),
	•	Workspace group membership.

This service will act as the authentication and authorization layer for the primary “tools” web application and may also be consumed by other internal APIs and microservices via a standalone authorization endpoint or a lightweight Python integration library.

⸻

2. Objectives
	1.	Single source of truth
All identity and authorization data originates from Google Workspace (profiles, custom attributes, groups).
	2.	Simple, explicit authorization model
Transform Workspace data into a normalized EffectiveAuth object (roles, permissions, and attributes) that can be used consistently across applications.
	3.	No separate auth database or admin UI
All user and permission management occurs in the Workspace Admin Console through custom attributes and group membership.
	4.	Reusable across applications
Provide helpers, middleware, and a Python integration library so code in the tools application and other internal services can easily determine:
	•	Who is the current user?
	•	Does the current user have permission X?

⸻

3. In Scope

3.1 Authentication (AuthN)
	•	Implement OIDC login with Google Workspace:
	•	Redirect the user to Google for sign-in.
	•	Handle callback and token exchange.
	•	Verify ID token signature and claims.
	•	Identify the user using:
	•	sub (Google user ID),
	•	email.
	•	Establish an application session through:
	•	Internal JWT stored in an HTTP-only cookie, or
	•	Opaque session ID backed by a server-side session store.

⸻

3.2 Authorization Standalone (AuthZ)
	•	Accept and validate an existing Workspace token (ID token or internal token).
	•	Return normalized authorization information (EffectiveAuth) to the calling internal application.
	•	This endpoint serves internal APIs/microservices that need Workspace-derived authorization but do not perform login flows themselves.

⸻

3.3 Authorization Data Ingestion
	•	Using a Workspace service account with domain-wide delegation and the Admin SDK, retrieve:
	•	Full user profile (minimal required fields),
	•	Custom attributes within the Authorization schema (e.g., Home Department, User Functions, Department Manager),
	•	Group membership for the user.
	•	Fetch this data:
	•	At login time,
	•	Optionally when cache entries expire,
	•	Optionally upon explicit refresh.

⸻

3.4 Authorization Model

Define a clear, minimal data structure:

email
home_department
is_department_manager
functions          # list of "Module:Action" strings from User Functions
permissions        # normalized permission codes (e.g., "shipping:create")
groups             # raw Workspace group emails

Provide deterministic mapping rules to convert Workspace data into:
	•	functions (from multi-line User Functions),
	•	permissions (e.g., Shipping:Create → shipping:create),
	•	Derived permissions (e.g., based on Home Department or Department Manager flag, if configured).

⸻

3.5 Caching & Session Handling
	•	Cache EffectiveAuth per user in Redis or comparable in-memory store.
	•	Each cache entry must have a configurable TTL.
	•	On cache miss, the service will:
	•	Attempt to re-fetch Workspace authorization data once, or
	•	Force re-authentication if necessary.

⸻

3.6 API / Integration Surface

Provide a minimal interface for the tools app and internal services:

Backend Helpers
	•	get_current_user() → returns EffectiveAuth
	•	require_permission("module:action") → decorator/middleware for protecting routes

HTTP contract for internal apps
	•	The tools backend and other internal services may:
	•	Read internal JWTs and derive EffectiveAuth, or
	•	Request EffectiveAuth via the standalone AuthZ endpoint.

Health Endpoint
	•	/health confirms:
	•	Auth service is running,
	•	Cache/Redis connectivity is healthy.

⸻

3.7 Logging & Auditing (Minimal)
	•	Log:
	•	Login successes and failures,
	•	Workspace profile/attribute fetch attempts and failures.
	•	No audit UI; logging is for debugging and security reviews using existing logging infrastructure.

⸻

3.8 Standalone Python Library
	•	Provide a lightweight Python package that:
	•	Validates internal tokens,
	•	Fetches or receives EffectiveAuth,
	•	Exposes simple helper functions to check permissions inside internal APIs or microservices.
	•	No business logic or policy engine is included; it is strictly an integration helper.

⸻

4. Out of Scope (Guardrails Against Scope Creep)

The following are explicitly not part of google-authz:
	1.	User management UI
	•	No GUI for editing users, roles, or permissions.
	•	All such changes happen in the Workspace Admin Console.
	2.	Multi-tenant identity provider
	•	Only one Workspace domain is supported.
	3.	Fine-grained policy engine
	•	No generic ABAC/OPA-style rule engine.
	•	No record-level authorization language.
	•	Apps are responsible for applying business-specific authorization using EffectiveAuth.
	4.	Support for non-Google identity providers
	•	No SAML, LDAP, or external IdPs.
	5.	End-user profile editor
	•	Users cannot modify authorization attributes through this service.
	6.	Full audit/reporting console
	•	No interface for browsing or analyzing org-wide permissions.

⸻

5. Stakeholders & Users

Primary Stakeholders
	•	IT / Infrastructure
	•	Operates the service and manages Workspace integration.
	•	Application Developers
	•	Integrate google-authz into the tools app or internal services.

Indirect Users
	•	Business Users
	•	Authenticate via Google SSO; do not directly interact with google-authz.
	•	Workspace Admins / HR
	•	Maintain user profile attributes and group memberships that control authorization.

⸻

6. High-Level Architecture
	1.	User → Tools Web UI
	•	User initiates login; browser redirects to Google.
	2.	Tools Backend / google-authz Module
	•	Handles OIDC callback.
	•	Validates Google ID token.
	•	Fetches Workspace attributes, profile, groups using Admin SDK.
	•	Computes EffectiveAuth.
	•	Caches EffectiveAuth.
	•	Issues internal JWT/session.
	3.	Subsequent Requests
	•	Tools backend validates internal token.
	•	Retrieves EffectiveAuth from cache.
	•	Enforces permissions with helpers/middleware.
	4.	Standalone Authorization Endpoint
	•	Accepts a validated Workspace or internal token.
	•	Returns EffectiveAuth for use by internal APIs/microservices.
	5.	Python Integration Library
	•	Wraps token validation + AuthZ requests.
	•	Enables simple permission checks in other services.
	6.	No Persistence Layer
	•	No database for auth state.
	•	Only transient cache; truth is the Workspace directory.

⸻

7. Functional Requirements (MVP)
	1.	FR-1: Authenticate user via Google Workspace OIDC and establish a session.
	2.	FR-2: Given a user email, fetch:
	•	Profile,
	•	Authorization schema attributes,
	•	Group memberships.
	3.	FR-3: Normalize Workspace data into an EffectiveAuth object.
	4.	FR-4: Cache EffectiveAuth with TTL.
	5.	FR-5: Provide backend helpers for:
	•	Accessing EffectiveAuth,
	•	Protecting routes via permission checks.
	6.	FR-6: Provide /health endpoint.
	7.	FR-7: Log authentication and Workspace-fetch events.
	8.	FR-8: Provide a standalone AuthZ endpoint that returns EffectiveAuth for a validated Workspace token.
	9.	FR-9: Provide a standalone Python library for integration into internal APIs.

⸻

8. Non-Functional Requirements

Security
	•	All communication over HTTPS.
	•	Service account key stored securely (not in image).
	•	Internal JWTs signed/verified with strong keys.
	•	Minimized Workspace scopes.

Performance
	•	Login flow target <1–2 seconds (dominated by Google latency).
	•	Permission checks must be O(1) against cached authorization data.

Reliability
	•	If Workspace is unavailable:
	•	Cached authorization may continue to be used until TTL expires.
	•	System exhibits clear failure modes during login or attribute refresh.

Operability
	•	Configuration via environment variables.
	•	Logging compatible with existing centralized log ingestion.

⸻

9. Assumptions & Dependencies
	•	Google Workspace is the only identity provider.
	•	All users of the tools app have Workspace accounts.
	•	Authorization-related custom attributes and groups are maintained by admins.
	•	Service account and domain-wide delegation are configured.
	•	Redis (or equivalent) is available for caching.

⸻


# Changelog

All notable changes to this project are documented here. The format loosely follows [Keep a Changelog](https://keepachangelog.com/) and adheres to [SemVer](https://semver.org/).

## [Unreleased]
### Added
- OAuth access token validation for `/authz` and `/authz/check` via Google tokeninfo/userinfo.
- Support for multiple allowed OAuth audiences (`GOOGLE_OAUTH_ALLOWED_AUDIENCES`).

### Changed
- Network ACL parsing now tolerates comma-separated strings without pre-splitting.

## [0.6.0] - 2024-06-01
### Added
- MIT license, Code of Conduct, Security policy, and contributing guide.
- Public-friendly README with Docker quick start, deployment docs, architecture diagram, and FAQ.
- Example apps (React client, FastAPI backend, Vite starter) plus local docker-compose stack with Redis.
- GitHub Actions workflow for lint/tests, container builds, and Trivy/pip-audit scanning.
- CHANGELOG, GitHub issue/PR templates, and release template referencing `docs/kubernetes` manifests.

## [0.5.0] - 2024-05-01
### Added
- `google-authz-client` Python package with FastAPI, Flask, and Django helpers.
- Sync + async HTTP clients (`GoogleAuthzClient`, `AsyncGoogleAuthzClient`) built on `httpx`.
- Dependency helper functions (`current_user`, `require_permission`, `any_of`, `all_of`).
- Middleware/decorators for Flask and Django to expose `EffectiveAuth` to views.
- Sample FastAPI app and developer docs for framework integrations.

## [0.4.0] - 2024-04-01
### Added
- `/session` endpoint plus refresh helper to expose EffectiveAuth + session metadata to browser apps.
- Configurable `ALLOWED_ORIGINS` and improved CORS defaults for React/Vite front ends.
- OAuth token passthrough flow for add-ons that already carry Workspace ID tokens.
- Enhanced `/authz` logging/metrics (module/action, cache hit rate) and retry/backoff controls.
- Comprehensive onboarding guide covering OAuth setup, schema creation, and deployment walkthroughs.

## [0.3.0] - 2024-03-01
### Added
- Public `/authz` and `/authz/check` endpoints for stateless authorization.
- Permission evaluation responses with `permitted_actions`, `decision`, and detailed error codes.
- Token validation for both Google ID tokens and internal session tokens.
- Rate limiting, network ACL enforcement via `AUTHZ_ALLOWED_NETWORKS`, and improved observability.

## [0.2.0] - 2024-02-01
### Added
- Full OAuth login (`/login` + `/auth/callback`) with nonce/state validation.
- Redis-backed EffectiveAuth cache with in-memory fallback and TTL controls.
- Signed internal session cookie plus `/me` and `/logout` helpers for manual testing.
- Logging around login success/failure and cache status to aid debugging.

## [0.1.0] - 2024-01-15
### Added
- Initial FastAPI service skeleton, configuration loader, and Workspace integration scaffolding.
- Basic health endpoints and manual `/authz/test` path for exercising Workspace fetches.
- Local development docs (`docs/scopev0.1.md`) covering `.env` basics and uvicorn workflow.

[Unreleased]: https://github.com/example/google-authz/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/example/google-authz/releases/tag/v0.6.0
[0.5.0]: https://github.com/example/google-authz/releases/tag/v0.5.0
[0.4.0]: https://github.com/example/google-authz/releases/tag/v0.4.0
[0.3.0]: https://github.com/example/google-authz/releases/tag/v0.3.0
[0.2.0]: https://github.com/example/google-authz/releases/tag/v0.2.0
[0.1.0]: https://github.com/example/google-authz/releases/tag/v0.1.0

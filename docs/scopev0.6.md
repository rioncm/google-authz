# scope v0.6 – Public Repository Preparation

## Objective
Prepare google-authz for a public GitHub release so other teams (or the community) can deploy it with minimal friction. This phase focuses on licensing, documentation polish, security hygiene, and contributor enablement rather than new runtime features.

## Requirements
1. **Repository hygiene**
   - Add an OSS license MIT.
- Add `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and `SECURITY.md` describing how to report vulnerabilities.
   - Provide issue/PR templates plus labels for roadmap alignment.
   - Ensure `.dockerignore`, `.gitignore`, and `.editorconfig` cover generated artifacts.

2. **Documentation overhaul**
   - Rewrite `README.md` with:
     - Project overview + feature list.
     - Quick start (Docker + .env example).
     - Configuration reference linking to `docs/config.md`.
     - Architecture diagram highlighting login flow, `/authz`, `/authz/check`.
     - FAQ (e.g., “How do I define custom schemas?”, “How do I add scopes?”).
   - Publish a deployment guide (Kubernetes + Docker Compose) with secrets management instructions.
   - Include tutorial linking React/Vite front end to login flow.

3. **Samples & automation**
- Add `examples/` folder:
    - React client (login + `/session` usage).
    - FastAPI backend calling `/authz/check`.
    - Vite starter template (React/Vite project pre-wired to call `/login`, `/session`, `/authz/check`).
   - Provide ready-to-run docker-compose for local stack (app + redis).
   - GitHub Actions CI workflow:
     - Lint + tests.
     - Optional container build + vulnerability scan (trivy/grype).

4. **Security & compliance**
   - Audit repo to ensure no private keys or customer-specific JSON files are checked in.
   - Document how to supply service-account JSON via secrets (never embed values).
   - Add dependency scanning (pip-audit or safety) to CI.
   - Provide guidance on rotating OAuth credentials and service accounts.

5. **Release process**
   - Tagging/versioning strategy (SemVer).
   - CHANGELOG.md with entries for v0.1 → v0.6.
   - GitHub Releases template referencing artifacts (docker image, python package).

6. **Community support**
   - Define support expectations (best-effort, issues only).
   - Add discussion board or link to community Slack if available.

## Non-Goals
- Feature development beyond polish.
- Publishing the Python library to PyPI (handled earlier in v0.5).

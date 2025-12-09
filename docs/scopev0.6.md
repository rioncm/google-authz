# scope v0.6 – Public Repository Preparation

## Objective
Prepare google-authz for a public GitHub release so other teams (or the community) can deploy it with minimal friction. This phase focuses on licensing, documentation polish, security hygiene, and contributor enablement rather than new runtime features.

## Requirements
1. **Repository hygiene**
   - Add an MIT `LICENSE` file and reference it from `README.md`.
   - Author `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and `SECURITY.md` (include disclosure instructions and SLA for triage).
   - Land issue and PR templates plus a default label set documenting roadmap areas.
   - Audit ignore files (`.gitignore`, `.dockerignore`, `.editorconfig`) so build artifacts, IDE files, and credentials never land in commits.

2. **Documentation overhaul**
   - Rewrite `README.md` to include: concise overview + feature bullets, Docker-based quick start (env file example), configuration summary that links to `docs/config.md`, architecture diagram callout, and FAQ covering schema/scopes customization.
   - Produce `docs/deployment.md` that walks through Docker Compose and Kubernetes rollouts, including how to pass secrets via env vars or secret objects.
   - Capture a diagram of the login → `/session` → `/authz` → `/authz/check` flow and store it at `docs/img/architecture-v0.6.png` (checked in as SVG + PNG).
   - Publish a React/Vite tutorial that demonstrates wiring the login flow to `/session`.

3. **Samples & automation**
   - Expand `examples/` with:
     - `examples/react-client` showcasing login + `/session`.
     - `examples/fastapi-backend` exercising `/authz/check`.
     - `examples/vite-starter` pre-configured to call `/login`, `/session`, and `/authz/check`.
   - Provide a docker-compose stack (`docker-compose.local.yml`) that runs google-authz and redis with seeded configs.
   - Add a GitHub Actions workflow covering lint/tests, optional container build, and vulnerability scanning (trivy or grype).

4. **Security & compliance**
   - Verify no secrets or customer JSON files remain in the repo history; relocate anything sensitive to `private/` (gitignored) or external secret stores.
   - Document secret injection patterns (env vars, mounted files) inside `docs/security.md`, including how to provide service-account JSON securely.
   - Extend CI with dependency scanning (pip-audit or Safety) and treat failures as blocking.
   - Add rotation guidance for OAuth credentials + service accounts to `docs/security.md` (include cadence, alerting, and rollback steps).

5. **Release process**
   - Adopt SemVer tagging (`vMAJOR.MINOR.PATCH`) and document bump workflow in `CONTRIBUTING.md`.
   - Create `CHANGELOG.md` summarizing v0.1 through v0.6 with links to relevant PRs.
   - Define a GitHub Releases template that references the Docker image, the `docs/kubernetes` manifest suite for Kubernetes deployments, and python client artifacts.

6. **Community support**
   - Document support expectations in `README.md` (best-effort via GitHub Issues unless otherwise stated).
   - Enable GitHub Discussions or link to the community Slack channel once available.

## Non-Goals
- Feature development beyond polish.
- Publishing the Python library to PyPI (handled earlier in v0.5).

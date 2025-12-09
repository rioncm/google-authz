# Contributing to google-authz

We welcome pull requests, issue reports, and documentation fixes. This guide explains how to set up the repo, propose changes, and ship releases.

## Getting started
1. Fork the repo and clone it locally.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env`, fill in secrets, and place service-account JSON under `private/`.
4. Run the API locally:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Optional: start Redis + app via `docker compose -f docker-compose.local.yml up --build`.

## Development workflow
- Create a feature branch per change.
- Add tests (or sample updates) when touching runtime code.
- Run the following before pushing:
  ```bash
  ruff check app
  pytest
  ```
- Update docs in `README.md`, `docs/deployment.md`, or `docs/security.md` when behavior changes.

## Issue labels
We triage issues using the following default labels:
- `area:api`, `area:ui`, `area:infra`, `area:docs`
- `kind:bug`, `kind:enhancement`, `kind:question`
- `priority:p1`, `priority:p2`, `priority:p3`
Include at least one `area:*` and one `kind:*` label on every issue/PR to align with the roadmap.

## Pull request checklist
- Reference an issue in the PR description.
- Include screenshots for UI-visible changes.
- Add release notes (`CHANGELOG.md`) when user-facing behavior shifts.
- Ensure CI passes (lint, tests, container build, Trivy scan).

## Release process (SemVer)
1. Ensure `main` is green and documentation is up-to-date.
2. Update `APP_VERSION` (if necessary) and append a section to `CHANGELOG.md` with links to merged PRs.
3. Tag the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z" && git push origin vX.Y.Z`.
4. Draft a GitHub Release using the template under `.github/release_template.md` (or the default UI). Reference the Docker image digest and python artifacts.
5. CI will build/publish the container once the tag is pushed. Announce in Discussions/Slack.

## Community expectations
All participants must follow the [Code of Conduct](CODE_OF_CONDUCT.md). For security-sensitive reports, read [`SECURITY.md`](SECURITY.md) before filing an issue.

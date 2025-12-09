# Security & Secrets Management

This document explains how to handle credentials for `google-authz`, add dependency scanning, and rotate sensitive material safely.

## Secret handling principals
1. **Keep secrets out of Git.** The repo already gitignores `.env`, `private/`, and JSON credentials. Never commit live OAuth or service-account files.
2. **Mount secrets at runtime.** Whether you run via Docker Compose or Kubernetes, inject values through env vars or mounted files supplied by your orchestrator/secrets manager.
3. **Audit frequently.** Before tagging a release, run `git ls-files -z | xargs -0 file` or dedicated scanners to ensure no `.json` files slipped in.

## Injecting secrets
### Docker Compose
- Store secrets in `.env` and `private/` locally.
- Compose mounts `.env` automatically and binds `private/` read-only so the FastAPI app can read the service-account JSON path declared in `GOOGLE_SERVICE_ACCOUNT_FILE`.

### Kubernetes
- Use `kubectl create secret ... --from-env-file=.env` for env vars and `--from-file=service.json=...` for JSON payloads.
- Projects using an external secret operator should map their vault path → Kubernetes secret and keep manifest changes minimal.

### GitHub Actions / CI
- Store publishing tokens and Docker registry credentials in repository secrets (Settings → Secrets and variables → Actions).
- The CI workflow reads `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, etc., if you enable container pushes.

## Dependency & container scanning
- CI uses `pip-audit` to flag vulnerable dependencies defined in `requirements.txt`.
- Container images are scanned with `aquasecurity/trivy-action` after each build. Failures break the pipeline by default—acknowledge CVEs in the issue tracker if you must temporarily defer.

## Credential rotation
| Item | Recommendation |
| --- | --- |
| Google OAuth client ID/secret | Rotate quarterly or immediately after staff changes. Update `.env`, secret manager entries, and restart pods. |
| Service-account JSON | Use short-lived keys from Google Secret Manager. Track key IDs in `docs/security.md` and delete old keys via `gcloud iam service-accounts keys delete`. |
| Session signing secret | Rotate monthly; store multiple secrets in secret managers if you need overlapping validity (implement in code later). |

### Rotation workflow
1. Create a new secret in your manager (e.g., `gcloud secrets versions add google-authz-oauth --data-file=oauth.env`).
2. Update Kubernetes secrets (or `.env`) with the new value.
3. Redeploy google-authz (rolling update). Validate login + `/session` flows.
4. Remove the old secret or mark it inactive.

## Incident response & disclosure
- Follow [`SECURITY.md`](../SECURITY.md) for reporting vulnerabilities.
- When secrets leak, revoke OAuth credentials through Google Cloud Console and disable service-account keys immediately.

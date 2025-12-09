# Deployment Guide

This guide covers common deployment targets for `google-authz`: local Docker Compose stacks and Kubernetes clusters. Both approaches rely on the same configuration contract described in [`docs/config.md`](config.md).

## 1. Docker Compose (local dev & demos)
1. Copy `.env.example` to `.env` and fill in OAuth, delegated admin, and session secrets.
2. Ensure your service-account JSON lives under `private/` so it is mounted read-only by Docker.
3. Start the stack:
   ```bash
   docker compose -f docker-compose.local.yml up --build
   ```
4. The API listens on `localhost:8000`, Redis on `localhost:6379`, and the OpenAPI docs are available at `/docs`.

### Secrets management
- `.env` is mounted directly into the container via Compose – keep it out of source control (already gitignored).
- For multi-developer teams, copy `.env.example` and distribute secrets via 1Password/Keybase instead of pushing `.env`.
- Service-account JSON should stay in `private/` (gitignored) or reference a cloud secret manager volume.

## 2. Kubernetes (staging & production)
Reference manifests are published under [`docs/kubernetes/`](kubernetes/README.md). The suite includes namespace, secret, config map, deployment, and ingress examples. Recommended workflow:

1. Create a namespace:
   ```bash
   kubectl apply -f docs/kubernetes/namespace.yaml
   ```
2. Create secrets for OAuth + service accounts:
   ```bash
   kubectl -n google-authz create secret generic google-authz-env --from-env-file=.env
   kubectl -n google-authz create secret generic google-service-account --from-file=service.json=private/gworkspace-465416-361687040922.json
   ```
3. Apply configs + deployment + ingress:
   ```bash
   kubectl apply -f docs/kubernetes/env-config.yaml
   kubectl apply -f docs/kubernetes/env-secret.yaml
   kubectl apply -f docs/kubernetes/manifest.yaml
   kubectl apply -f docs/kubernetes/ingress.yaml
   ```
4. Point DNS or /etc/hosts at the ingress controller endpoint and run through the login flow.

### Secrets best practices
- Prefer external secret managers (GCP Secret Manager, AWS Secrets Manager, Vault) and sync them as Kubernetes secrets using controllers like [External Secrets Operator](https://external-secrets.io/).
- Store OAuth credentials as opaque secrets and mount them as env vars. Store service-account JSON as mounted files (volume + projected secret) to avoid long env vars.
- Rotate secrets using CI jobs that call the secret manager API and update Kubernetes secrets (documented in [`docs/security.md`](security.md)).

## 3. CI/CD hooks
- The GitHub Actions workflow under `.github/workflows/ci.yml` runs lint/tests, builds a container, and scans it with Trivy.
- Add an environment-protected deploy job (ArgoCD, GitOps) that watches the container registry tag mentioned in GitHub Releases.

## Troubleshooting
| Symptom | Fix |
| --- | --- |
| OAuth callback errors | Ensure `GOOGLE_OAUTH_REDIRECT_URI` matches the URI configured in Google Cloud Console. |
| Session cookie missing | Set `SESSION_COOKIE_SECURE=false` for local HTTP testing and check browser devtools. |
| `/authz` returning 500 | Verify the service-account JSON has the Admin SDK scopes granted. Use `docker compose logs app` for stack traces. |
| Redis connection issues | Update `REDIS_URL` to point to the in-cluster Redis or switch `redis_location` to `in-memory` for debugging. |

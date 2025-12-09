# google-authz Kubernetes Manifests

These manifests represent a single-namespace deployment that keeps the git repo in sync, injects secrets, and runs Redis as a sidecar. Everything is sanitized for public documentation—you must replace the placeholders with values from your environment.

## Files

- `namespace.yaml` – Creates the dedicated namespace (`google-authz` by default).
- `env-secret.yaml` – Holds non-sensitive configuration (delegated admin email, customer ID, etc.). Replace each placeholder with your real Workspace settings before applying.
- `google-service-secret.yaml` – Placeholder secret for the Workspace service account JSON. Paste the JSON from `private/…` or create the secret via `kubectl create secret generic google-service-secret --from-file=credentials.json=./private/<file>.json -n google-authz`.
- `manifest.yaml` – Deployment with:
  - application container (`ghcr.io/your-org/google-authz:0.2.0` placeholder),
  - Redis sidecar.
- `ingress.yaml` – Exposes the service via Traefik (`auth.example.com` placeholder host names). Adjust annotations for your ingress controller/TLS issuer.

## Secrets to Provide

1. `authz-env-secret` – already defined, but replace every placeholder before `kubectl apply`.
2. `google-service-secret` – populate the `credentials.json` block with your service account or create it from a file:
   ```sh
   kubectl create secret generic google-service-secret \
     --from-file=credentials.json=./private/gworkspace.json \
     -n google-authz
   ```
3. `git-sync-credentials` – if your repository is private, create a secret with the environment variables expected by git-sync (e.g., `GITSYNC_USERNAME`, `GITSYNC_PASSWORD`, or SSH keys).

## Deployment Order

```sh
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/env-secret.yaml
kubectl apply -f kubernetes/google-service-secret.yaml   # after populating credentials
kubectl apply -f kubernetes/manifest.yaml
kubectl apply -f kubernetes/ingress.yaml
```

## Customization Checklist

- Swap `YOUR-ORG` repo/image placeholders in `manifest.yaml`.
- Update hostnames (`auth.example.com`) and TLS secret names in `ingress.yaml`.
- Provide a Redis connection string if you want to use an external cache instead of the sidecar.
- Tune readiness/liveness probe paths if the FastAPI endpoints change.
- Consider using ConfigMaps for non-secret configuration if you prefer not to store it in Secrets.

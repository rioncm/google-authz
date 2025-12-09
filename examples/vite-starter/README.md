# Vite starter (React)

Starter template that wires React hooks to `/login`, `/session`, and `/authz/check`. Copy this folder to kick off a front-end that consumes google-authz.

## Commands
```bash
cd examples/vite-starter
npm install
npm run dev -- --host
```

Environment variables:
- `VITE_AUTHZ_BASE_URL` – defaults to `http://localhost:8000`
- `VITE_REQUIRED_PERMISSION` – e.g., `inventory:read`

Paste either a `session_token` (for trusted backends) or a Google `id_token` from the `/login` flow into the text area before hitting **Evaluate**. The template posts directly to `/authz/check`.

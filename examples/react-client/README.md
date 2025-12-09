# React client example

Minimal React/Vite client that exercises `/login` and `/session` from `google-authz`.

## Setup
```bash
cd examples/react-client
npm install
npm run dev -- --host
```

Set `VITE_AUTHZ_BASE_URL` in `.env` (defaults to `http://localhost:8000`). The app will:
- Render a "Sign in with Google" button that redirects to `${BASE_URL}/login`.
- Call `${BASE_URL}/session` to show the cached `EffectiveAuth` payload.

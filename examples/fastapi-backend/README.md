# FastAPI backend example

A minimal API that calls google-authz `/authz/check` before handling protected routes.

## Setup
```bash
cd examples/fastapi-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Set environment variables:
- `AUTHZ_BASE_URL` – default `http://localhost:8000`
- `REQUIRED_PERMISSION` – default `inventory:read`

This sample assumes a browser client hits `/login` and forwards the `ga_session` cookie to this backend.

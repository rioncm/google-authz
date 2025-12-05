# google-authz – v0.1 Local Notes

## Environment

Create a `.env` file in the project root:

```
GOOGLE_WORKSPACE_DELEGATED_USER=admin@pleasantmattress.com
GOOGLE_WORKSPACE_CUSTOMER_ID=C0123456
GOOGLE_WORKSPACE_AUTH_SCHEMA=Authorization
GOOGLE_SERVICE_ACCOUNT_FILE=private/gworkspace-465416-361687040922.json
SAMPLE_USER_EMAIL=rion@pleasantmattress.com
```

The `private/` JSON is git-ignored and should contain the Workspace service account key that already has domain-wide delegation enabled for the Admin SDK scopes.

## Running the FastAPI app

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Endpoints:
- `GET /health` – confirms the service is up.
- `POST /authz/test` – body `{ "email": "user@example.com" }` (defaults to `SAMPLE_USER_EMAIL` when omitted) and returns the raw Workspace payloads plus the normalized `EffectiveAuth`.

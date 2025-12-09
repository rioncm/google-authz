import os
from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class Settings(BaseModel):
    authz_base_url: str = os.getenv("AUTHZ_BASE_URL", "http://localhost:8000")
    required_permission: str = os.getenv("REQUIRED_PERMISSION", "inventory:read")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


app = FastAPI(title="google-authz FastAPI sample")


async def require_session(request: Request) -> str:
    token = request.cookies.get("ga_session")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session cookie")
    return token


class AuthzCheckResponse(BaseModel):
    authorized: bool
    decision: str
    permitted_actions: list[str]


async def require_permission(
    session_token: Annotated[str, Depends(require_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthzCheckResponse:
    module, action = settings.required_permission.split(":", maxsplit=1)
    async with httpx.AsyncClient(base_url=settings.authz_base_url, timeout=10) as client:
        resp = await client.post(
            "/authz/check",
            json={
                "module": module,
                "action": action,
                "session_token": session_token,
            },
            headers={"Content-Type": "application/json"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    payload = AuthzCheckResponse(**resp.json())
    if not payload.authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return payload


@app.get("/inventory")
async def inventory(_: Annotated[AuthzCheckResponse, Depends(require_permission)]):
    return JSONResponse({"items": ["widget", "gear"]})

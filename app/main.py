from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel

from app.lib.config import Settings, get_settings
from app.lib.logging_config import configure_logging
from app.lib.models import WorkspaceAuthResponse
from app.lib.workspace import (
    WorkspaceAuthorizationService,
    WorkspaceDirectoryClient,
    WorkspaceError,
)

configure_logging()
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup items
    directory_client = WorkspaceDirectoryClient(settings)
    auth_service = WorkspaceAuthorizationService(directory_client, settings)
    app.state.settings = settings
    app.state.workspace_service = auth_service
    yield
    # Shutdown items (if any)


app = FastAPI(lifespan=lifespan,title=settings.app_name, version=settings.app_version)


class TestAuthRequest(BaseModel):
    email: str | None = None


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_workspace_service(request: Request) -> WorkspaceAuthorizationService:
    return request.app.state.workspace_service


@app.get("/health")
def health(settings: Settings = Depends(get_app_settings)) -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env, "version": settings.app_version}


@app.post("/authz/test", response_model=WorkspaceAuthResponse)
def get_authorization_profile(
    payload: TestAuthRequest,
    settings: Settings = Depends(get_app_settings),
    workspace_service: WorkspaceAuthorizationService = Depends(get_workspace_service),
) -> WorkspaceAuthResponse:
    email = (payload.email or settings.sample_user_email).strip().lower()
    try:
        effective_auth, raw_user, raw_groups = workspace_service.fetch_effective_auth(email)
    except WorkspaceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return WorkspaceAuthResponse(
        requested_email=email,
        effective_auth=effective_auth,
        raw_user=raw_user,
        raw_groups=raw_groups,
    )

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import Settings
from .models import EffectiveAuth

SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
]


class WorkspaceError(Exception):
    """Raised when Workspace data cannot be fetched."""


class WorkspaceDirectoryClient:
    """Thin wrapper around the Admin SDK Directory API."""

    def __init__(self, settings: Settings):
        if not settings.google_service_account_file.exists():
            raise WorkspaceError(
                f"Service account file {settings.google_service_account_file} is missing. "
                "Provide GOOGLE_SERVICE_ACCOUNT_FILE or drop the JSON in private/."
            )
        if not settings.google_delegated_user:
            raise WorkspaceError("GOOGLE_WORKSPACE_DELEGATED_USER is required to perform domain-wide delegation.")

        credentials = service_account.Credentials.from_service_account_file(
            str(settings.google_service_account_file)
        )
        delegated_credentials = credentials.with_scopes(SCOPES).with_subject(settings.google_delegated_user)

        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)
        self._service = build("admin", "directory_v1", credentials=delegated_credentials, cache_discovery=False)

    def get_user(self, email: str) -> Dict[str, Any]:
        """Fetch a Workspace user with the configured custom schema."""
        try:
            return (
                self._service.users()
                .get(
                    userKey=email,
                    projection="full",
                    customFieldMask=self._settings.google_auth_schema,
                )
                .execute()
            )
        except HttpError as exc:
            self._logger.exception("Failed to fetch Workspace user %s", email)
            raise WorkspaceError(f"Failed to fetch Workspace user {email}") from exc

    def list_groups(self, email: str) -> Dict[str, Any]:
        """List group memberships for the user."""
        groups: List[Dict[str, Any]] = []
        request = self._service.groups().list(userKey=email)
        try:
            while request is not None:
                response = request.execute()
                if "groups" in response and response["groups"]:
                    groups.extend(response["groups"])
                request = self._service.groups().list_next(request, response)
        except HttpError as exc:
            self._logger.exception("Failed to fetch Workspace groups for %s", email)
            raise WorkspaceError(f"Failed to fetch Workspace groups for {email}") from exc
        return {"groups": groups}


class WorkspaceAuthorizationService:
    """Fetch Workspace data and normalize it into EffectiveAuth."""

    HOME_DEPARTMENT_KEY = "HomeDepartment"
    USER_FUNCTIONS_KEY = "UserFunctions"
    MANAGER_KEY = "DepartmentManager"

    def __init__(self, client: WorkspaceDirectoryClient, settings: Settings):
        self._client = client
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)

    def fetch_effective_auth(self, email: str) -> Tuple[EffectiveAuth, Dict[str, Any], Dict[str, Any]]:
        user = self._client.get_user(email)
        groups_response = self._client.list_groups(email)
        groups = [group["email"] for group in groups_response.get("groups", []) if "email" in group]

        custom_schema = self._extract_custom_schema(user)
        functions = self._coerce_list(custom_schema.get(self.USER_FUNCTIONS_KEY))

        effective_auth = EffectiveAuth(
            email=user.get("primaryEmail", email).lower(),
            home_department=self._coerce_scalar(custom_schema.get(self.HOME_DEPARTMENT_KEY)),
            is_department_manager=self._coerce_bool(custom_schema.get(self.MANAGER_KEY)),
            functions=functions,
            permissions=self._derive_permissions(functions),
            groups=groups,
        )
        return effective_auth, user, groups_response

    def _extract_custom_schema(self, user: Dict[str, Any]) -> Dict[str, Any]:
        schemas = user.get("customSchemas") or {}
        return schemas.get(self._settings.google_auth_schema, {})

    @staticmethod
    def _coerce_scalar(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, list):
            flattened = WorkspaceAuthorizationService._flatten_list(value)
            return flattened[0] if flattened else None
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return str(value)

    @staticmethod
    def _coerce_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return WorkspaceAuthorizationService._flatten_list(value)
        if isinstance(value, dict):
            if "values" in value and isinstance(value["values"], list):
                return WorkspaceAuthorizationService._flatten_list(value["values"])
            if "value" in value:
                return [str(value["value"]).strip()]
        return [str(value).strip()]

    @staticmethod
    def _flatten_list(value: Sequence[Any]) -> List[str]:
        flattened: List[str] = []
        for entry in value:
            if isinstance(entry, dict) and "value" in entry:
                flattened.append(str(entry["value"]).strip())
            else:
                flattened.append(str(entry).strip())
        return [item for item in flattened if item]

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        scalar = WorkspaceAuthorizationService._coerce_scalar(value)
        if scalar is None:
            return False
        return str(scalar).lower() in {"1", "true", "yes", "y"}

    @staticmethod
    def _derive_permissions(functions: Sequence[str]) -> List[str]:
        permissions = {WorkspaceAuthorizationService._normalize_permission(func) for func in functions if func}
        return sorted(permissions)

    @staticmethod
    def _normalize_permission(function_name: str) -> str:
        normalized = function_name.strip()
        if ":" in normalized:
            module, action = normalized.split(":", 1)
            return f"{WorkspaceAuthorizationService._slugify(module)}:{WorkspaceAuthorizationService._slugify(action)}"
        return WorkspaceAuthorizationService._slugify(normalized)

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = value.strip().lower().replace(" ", "_")
        return cleaned.replace("__", "_")

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import Settings
from .models import EffectiveAuth

BASE_SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
]
DEFAULT_CUSTOM_SCHEMAS: Tuple[str, ...] = ("EmployeeInfo",)


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
        scopes = self._build_scopes(settings.additional_scopes)
        delegated_credentials = credentials.with_scopes(scopes).with_subject(settings.google_delegated_user)

        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)
        self._service = build("admin", "directory_v1", credentials=delegated_credentials, cache_discovery=False)
        self._extra_schemas = self._normalize_extra_schemas(settings)
        self._custom_field_mask = self._build_custom_field_mask()
        self._schema_field_types = self._load_schema_field_types()

    def _build_scopes(self, additional_scopes: Sequence[str]) -> List[str]:
        ordered_scopes: List[str] = []
        seen = set()
        for scope in [*BASE_SCOPES, *additional_scopes]:
            if not scope or scope in seen:
                continue
            ordered_scopes.append(scope)
            seen.add(scope)
        return ordered_scopes

    def _build_custom_field_mask(self) -> str:
        schemas = set(DEFAULT_CUSTOM_SCHEMAS)
        if self._settings.google_auth_schema:
            schemas.add(self._settings.google_auth_schema)
        schemas.update(self._extra_schemas)
        return ",".join(sorted(schemas))

    def _normalize_extra_schemas(self, settings: Settings) -> List[str]:
        extra = [name.strip() for name in settings.google_workspace_extra_schemas if name and name.strip()]
        auth_schema = settings.google_auth_schema
        return [name for name in extra if name != auth_schema]

    def _load_schema_field_types(self) -> Dict[str, Dict[str, Dict[str, object]]]:
        if not self._extra_schemas:
            return {}
        customer_id = self._settings.google_customer_id or "my_customer"
        try:
            response = self._service.schemas().list(customerId=customer_id).execute()
        except HttpError as exc:
            self._logger.warning("Failed to fetch schema definitions: %s", exc)
            return {}
        schemas = response.get("schemas") or []
        schema_map: Dict[str, Dict[str, Dict[str, object]]] = {}
        for schema in schemas:
            schema_name = schema.get("schemaName")
            if schema_name not in self._extra_schemas:
                continue
            fields = schema.get("fields") or []
            field_map: Dict[str, Dict[str, object]] = {}
            for field in fields:
                field_name = field.get("fieldName")
                if not field_name:
                    continue
                field_map[field_name] = {
                    "type": field.get("fieldType") or "unknown",
                    "multi": bool(field.get("multiValued")),
                }
            schema_map[schema_name] = field_map
        return schema_map

    def get_user(self, email: str) -> Dict[str, Any]:
        """Fetch a Workspace user with the configured custom schema."""
        try:
            return (
                self._service.users()
                .get(
                    userKey=email,
                    projection="full",
                    customFieldMask=self._custom_field_mask,
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

    @property
    def extra_schemas(self) -> List[str]:
        return list(self._extra_schemas)

    @property
    def schema_field_types(self) -> Dict[str, Dict[str, Dict[str, object]]]:
        return self._schema_field_types


class WorkspaceAuthorizationService:
    """Fetch Workspace data and normalize it into EffectiveAuth."""

    RBAC_KEY = "RBAC"

    def __init__(self, client: WorkspaceDirectoryClient, settings: Settings):
        self._client = client
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)

    def fetch_effective_auth(self, email: str) -> Tuple[EffectiveAuth, Dict[str, Any], Dict[str, Any]]:
        user = self._client.get_user(email)
        groups_response = self._client.list_groups(email)
        groups = [group["email"] for group in groups_response.get("groups", []) if "email" in group]
        self._logger.debug(
            "Workspace user customSchemas for %s: %s",
            email,
            user.get("customSchemas") or {},
        )

        custom_schema = self._extract_custom_schema(user)
        functions = self._coerce_list(custom_schema.get(self.RBAC_KEY))
        custom_schemas = self._extract_extra_schemas(user)
        self._logger.debug(
            "Auth schema '%s' RBAC raw=%s parsed=%s",
            self._settings.google_auth_schema,
            custom_schema.get(self.RBAC_KEY),
            functions,
        )
        self._logger.debug("Extra schemas parsed for %s: %s", email, custom_schemas)

        effective_auth = EffectiveAuth(
            email=user.get("primaryEmail", email).lower(),
            functions=functions,
            permissions=self._derive_permissions(functions),
            groups=groups,
            custom_schemas=custom_schemas,
        )
        return effective_auth, user, groups_response

    def _extract_custom_schema(self, user: Dict[str, Any]) -> Dict[str, Any]:
        schemas = user.get("customSchemas") or {}
        return schemas.get(self._settings.google_auth_schema, {})

    def _extract_extra_schemas(self, user: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, object]]]:
        schemas = user.get("customSchemas") or {}
        output: Dict[str, Dict[str, Dict[str, object]]] = {}
        for schema_name in self._client.extra_schemas:
            schema_payload = schemas.get(schema_name) or {}
            output[schema_name] = self._normalize_schema_fields(schema_name, schema_payload)
        return output

    def _normalize_schema_fields(
        self,
        schema_name: str,
        schema_payload: Dict[str, Any],
    ) -> Dict[str, Dict[str, object]]:
        field_type_map = self._client.schema_field_types.get(schema_name, {})
        normalized: Dict[str, Dict[str, object]] = {}
        for field_name, raw_value in schema_payload.items():
            values, multi = self._normalize_field_values(raw_value)
            type_info = field_type_map.get(field_name, {})
            normalized[field_name] = {
                "type": type_info.get("type", "unknown"),
                "multi": type_info.get("multi", multi),
                "values": values,
            }
        return normalized

    def _normalize_field_values(self, value: Any) -> Tuple[List[str], bool]:
        if value is None:
            return [], False
        if isinstance(value, dict) and "values" in value:
            return self._coerce_list(value.get("values")), True
        if isinstance(value, list):
            return self._coerce_list(value), True
        if isinstance(value, dict) and "value" in value:
            return self._coerce_list(value.get("value")), False
        return self._coerce_list(value), False

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

# Sprint v0.2a – Dynamic ADDITIONAL_SCOPES Support

## Objective
Allow deployments to specify additional Google Directory API scopes through a comma-separated `ADDITIONAL_SCOPES` environment variable so custom schema data can be requested without code changes. All scopes defined in `ADDITIONAL_SCOPES` must be appended to the existing set used by `WorkspaceDirectoryClient`. The configured Authorization schema and the Google-managed EmployeeInfo schema are always requested by default.

## Deliverables
- Parse `ADDITIONAL_SCOPES` once in `Settings` (or a helper) into a normalized list of scope strings.
- Extend `WorkspaceDirectoryClient` to merge the existing default scopes with the parsed list and use the resulting set for delegated credentials.
- Update documentation / sample `.env` to illustrate how to configure the new variable.
- Add unit / integration coverage that confirms user fetches include the custom scopes when `ADDITIONAL_SCOPES` is set.

## Implementation Notes
- Sanitize the comma-separated value by trimming whitespace and ignoring empty entries.
- Deduplicate scopes to avoid unnecessary OAuth tokens.
- Fail fast (or log) if an invalid URL is supplied to avoid confusing Google errors.
- Ensure the combined scopes remain compatible with the existing service account delegation configuration.

## Data Requirements
- **Authorization Schema:** _Add required fields here._
    - RBAC -- string multi value



***Noted Changes***
    HOME_DEPARTMENT_KEY = "HomeDepartment"
    USER_FUNCTIONS_KEY = "UserFunctions"
    MANAGER_KEY = "DepartmentManager"

    -- Becomes --

    CORE_TEAM_KEY = "CoreTeam"
    PERMISSION_KEY = "Permission"
    MANAGER_KEY = "Manager"

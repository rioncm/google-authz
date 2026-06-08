# /authz and /authz/check Responses

This document describes the response payloads returned by the authorization endpoints.

## POST /authz

Returns the caller’s `EffectiveAuth` document plus a cache source label.

Response shape:

```
{
  "effective_auth": {
    "email": "user@example.com",
    "functions": ["bankrec:read", "key:all"],
    "permissions": ["bankrec:read", "key:all"],
    "groups": ["group@example.com"],
    "custom_schemas": {
      "Teams": {
        "team": {
          "type": "STRING",
          "multi": true,
          "values": ["Operations", "Sales"]
        }
      }
    },
    "fetched_at": "2025-12-29T19:48:03.660095"
  },
  "source": "cache"
}
```

Field notes:
- `email`: The Workspace primary email for the user.
- `functions`: Raw RBAC values pulled from the `Authorization` schema `RBAC` field.
- `permissions`: Normalized permissions derived from `functions`.
- `groups`: Google Groups email addresses for the user.
- `custom_schemas`: Optional passthrough of extra schemas listed in `GOOGLE_WORKSPACE_EXTRA_SCHEMAS`.
- `fetched_at`: When the EffectiveAuth payload was generated.
- `source`: One of `cache` or `refreshed`.

## POST /authz/check

Evaluates a single `module:action` permission for the caller.

Success (authorized):

```
{
  "authorized": true,
  "decision": "granted",
  "evaluated_permission": "bankrec:read",
  "permitted_actions": ["read"],
  "source": "cache",
  "reason": null
}
```

Failure (not authorized):

```
{
  "authorized": false,
  "decision": "denied",
  "evaluated_permission": "bankrec:read",
  "permitted_actions": [],
  "source": "cache",
  "reason": "permission_missing"
}
```

Field notes:
- `authorized`: Boolean decision for the requested permission.
- `decision`: `granted` or `denied`.
- `evaluated_permission`: Normalized `module:action` string used in the check.
- `permitted_actions`: List of actions allowed within the requested module.
- `source`: One of `cache` or `refreshed`.
- `reason`: Optional reason when denied.

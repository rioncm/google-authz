# AuthZ Endpoint Responses

This document describes the response payloads returned by the browser login and authorization endpoints.

## GET /login/app

Starts a browser login flow for a configured first-party application.

Request:

```http
GET /login/app?app=helpers&redirect_uri=https%3A%2F%2Fhelpers.k8.pminc.me%2F
```

Behavior:

- Validates `app` against the server-side login app registry.
- Validates `redirect_uri` against the app's approved redirects.
- Stores approved app metadata in the signed OAuth state cookie.
- Redirects to Google OAuth with HTTP 303.
- On `/auth/callback`, sets the AuthZ session cookie and redirects to the approved app URL.

Invalid app names or redirect URLs return HTTP 400 before Google OAuth begins.

See [`docs/browser-app-login.md`](browser-app-login.md) for registry configuration and consuming app examples.

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

When called with `session_token`, `/authz` decodes the signed session token from the browser cookie, resolves the cached or refreshed `EffectiveAuth`, and returns the RBAC data. The session cookie itself does not contain the full RBAC document.

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

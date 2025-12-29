# scope v0.3 – Standalone Authorization Endpoint

## Objective
Expose stateless APIs for internal callers to (a) exchange a valid Workspace token for EffectiveAuth and (b) ask the service to enforce RBAC-style permissions (“module:verb”) against that user’s Authorization schema data. Access is limited to trusted networks while user identity still comes from existing OAuth/session validation.

## Requirements
1. **Endpoint contracts**
   1. `/authz` (existing behavior)
      - `POST /authz`.
      - Accepts a JSON payload with exactly one token field:
        - `{"id_token": "<Google ID token>"}`
        - or `{"session_token": "<internal JWT>"}`.
      - Response:
        ```json
        {
          "effective_auth": { ... },
          "source": "cache" | "refreshed"
        }
        ```
      - Errors:
        - `400` malformed payload.
        - `401` invalid/expired token.
        - `404` cache + refresh failure.
        - `429` rate limit triggered.

   2. `/authz/check`
      - `POST /authz/check`.
      - Payload includes the token plus the target permission:
        ```json
        {
          "id_token": "<...>",
          "module": "inventory",
          "action": "read"
        }
        ```
        - `module`: arbitrary string defined by admins. Normalized to lowercase slug to match stored permissions.
        - `action`: must be one of the RBAC style verbs `["create", "read", "update", "delete", "list", "approve", "manage"]`. Requests with invalid verbs return `400`.
        - Either `id_token` or `session_token` must be supplied (mutually exclusive) exactly as `/authz`.
      - Server looks up EffectiveAuth (cache first). It then checks if `f"{module}:{action}"` exists in `EffectiveAuth.permissions`.
      - Response:
        ```json
        {
          "authorized": true,
          "decision": "granted",
          "evaluated_permission": "inventory:read",
          "permitted_actions": ["inventory:read", "inventory:list"],
          "source": "cache" | "refreshed"
        }
        ```
        - `permitted_actions` contains every `module:verb` pair for the module evaluated so callers can cache future decisions locally. When the caller needs complete EffectiveAuth data they should call `/authz`.
        - When unauthorized: return `403` with `{"authorized": false, "decision": "denied", "reason": "permission_missing", "permitted_actions": []}`.
      - Errors:
        - `400` malformed payload or invalid verb.
        - `401` invalid token.
        - `404` cache + refresh failure (cannot evaluate).
        - `429` rate limit triggered.

2. **Token validation**
   - Reuse existing ID token verification logic (audience, issuer, hosted domain, nonce/state checks as applicable).
   - When `session_token` is provided, verify the internal JWT/session cookie using current session helpers.
   - On successful validation derive the user’s email (lowercased) that serves as the cache key.

3. **EffectiveAuth retrieval**
   - Attempt cache lookup via existing `fetch_and_cache_effective_auth`.
   - If cache miss, trigger Workspace fetch flow once (with the same guardrails as login).
   - Return the EffectiveAuth plus metadata indicating whether the data came from cache or fresh fetch.
   - `/authz/check` reuses the same path; the permission evaluation only runs after EffectiveAuth is available.

4. **Rate limiting & observability**
   - Add lightweight rate limiting per caller IP (e.g., N requests/min) to protect Workspace quota. Implementation can reuse FastAPI dependencies or a Redis counter.
   - Log every request outcome with:
     - Caller IP (from headers/load balancer if available).
     - Token type (`id_token` vs `session_token`).
     - Cache hit/miss.
     - Workspace fetch duration when applicable.
      - For `/authz/check`, log the evaluated permission and allow/deny decision.

5. **Access control**
   - No per-client secrets/state. Restrict reachability via network ACLs or ingress rules so only trusted services can hit `/authz`.
   - Document expected deployment network boundaries (e.g., only published on the internal cluster service network).
   - Introduce `AUTHZ_ALLOWED_NETWORKS` env var (IPv4 only) with support for:
        - `0.0.0.0/0` or `*` (allow all – only for dev)
        - CIDR blocks (`10.0.0.0/16`)
        - Comma-separated single hosts (`10.1.1.5,10.1.1.6`)
        - Explicit ranges using `start|end` (`10.42.0.10|10.42.0.25`)

6. **Documentation**
   - Update README/scope docs describing:
     - Payload schema and example request/response.
     - Allowed RBAC verbs (`create, read, update, delete, list, approve, manage`) and module naming expectations.
     - Required network restrictions.
     - Error codes and retry guidance.
   - Add runbook notes for operations (monitoring cache miss rate, handling rate-limit tuning).

## Non-Goals
- Implementing broad client-side permission helper libraries (still slated for v0.4); v0.3 only exposes the enforcement endpoint.
- Introducing new stateful caller authentication mechanisms (shared secrets, mTLS). All caller identity is enforced via network policy.

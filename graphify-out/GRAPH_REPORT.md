# Graph Report - /Users/rion/VSCode/pminc/google-authz  (2026-06-09)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 409 nodes · 1192 edges · 72 communities (27 shown, 45 thin omitted)
- Extraction: 67% EXTRACTED · 33% INFERRED · 0% AMBIGUOUS · INFERRED: 389 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Authorization and Session Management|Authorization and Session Management]]
- [[_COMMUNITY_Authorization Request Handling|Authorization Request Handling]]
- [[_COMMUNITY_API Parameter Definitions|API Parameter Definitions]]
- [[_COMMUNITY_API Endpoint Metadata|API Endpoint Metadata]]
- [[_COMMUNITY_OAuth Service Implementation|OAuth Service Implementation]]
- [[_COMMUNITY_Workspace Authorization Logic|Workspace Authorization Logic]]
- [[_COMMUNITY_API Documentation Metadata|API Documentation Metadata]]
- [[_COMMUNITY_Caching Implementations|Caching Implementations]]
- [[_COMMUNITY_React Frontend Dependencies|React Frontend Dependencies]]
- [[_COMMUNITY_React Frontend Dependencies|React Frontend Dependencies]]
- [[_COMMUNITY_Permission and Session Checks|Permission and Session Checks]]
- [[_COMMUNITY_Frontend Authz and Session Hooks|Frontend Authz and Session Hooks]]
- [[_COMMUNITY_Login App Tests|Login App Tests]]
- [[_COMMUNITY_Path Utilities|Path Utilities]]
- [[_COMMUNITY_Configuration Settings Management|Configuration Settings Management]]
- [[_COMMUNITY_FastAPI Application Package|FastAPI Application Package]]
- [[_COMMUNITY_Authorization Endpoint Responses|Authorization Endpoint Responses]]
- [[_COMMUNITY_Browser Login Flow|Browser Login Flow]]
- [[_COMMUNITY_Environment Variables|Environment Variables]]
- [[_COMMUNITY_Deployment Guide|Deployment Guide]]
- [[_COMMUNITY_Developer Documentation|Developer Documentation]]
- [[_COMMUNITY_Project Roadmap|Project Roadmap]]
- [[_COMMUNITY_Scope Document|Scope Document]]
- [[_COMMUNITY_Local Development Notes|Local Development Notes]]
- [[_COMMUNITY_Google Login and Caching|Google Login and Caching]]
- [[_COMMUNITY_Dynamic Scope Support Sprint|Dynamic Scope Support Sprint]]
- [[_COMMUNITY_Standalone Authorization Endpoint|Standalone Authorization Endpoint]]
- [[_COMMUNITY_Application Completion and Multi-Client|Application Completion and Multi-Client]]
- [[_COMMUNITY_Python Integration Library|Python Integration Library]]
- [[_COMMUNITY_Public Repository Preparation|Public Repository Preparation]]
- [[_COMMUNITY_Custom Schema Passthrough Sprint|Custom Schema Passthrough Sprint]]
- [[_COMMUNITY_Security and Secrets Management|Security and Secrets Management]]
- [[_COMMUNITY_Login Integration Helpers Review|Login Integration Helpers Review]]
- [[_COMMUNITY_Architecture Diagram|Architecture Diagram]]
- [[_COMMUNITY_Kubernetes Environment ConfigMap|Kubernetes Environment ConfigMap]]
- [[_COMMUNITY_Kubernetes Ingress and Service|Kubernetes Ingress and Service]]
- [[_COMMUNITY_Kubernetes Login Apps ConfigMap|Kubernetes Login Apps ConfigMap]]
- [[_COMMUNITY_Kubernetes Deployment Manifest|Kubernetes Deployment Manifest]]
- [[_COMMUNITY_Kubernetes Namespace Manifest|Kubernetes Namespace Manifest]]
- [[_COMMUNITY_Google-Authz Kubernetes Manifests|Google-Authz Kubernetes Manifests]]
- [[_COMMUNITY_FastAPI Backend README|FastAPI Backend README]]
- [[_COMMUNITY_FastAPI Backend Requirements|FastAPI Backend Requirements]]
- [[_COMMUNITY_React Client Index HTML|React Client Index HTML]]
- [[_COMMUNITY_React Client README|React Client README]]
- [[_COMMUNITY_Vite Starter Index HTML|Vite Starter Index HTML]]
- [[_COMMUNITY_Vite Starter README|Vite Starter README]]
- [[_COMMUNITY_Bug Report Template|Bug Report Template]]
- [[_COMMUNITY_Issue Template Configuration|Issue Template Configuration]]
- [[_COMMUNITY_Feature Request Template|Feature Request Template]]
- [[_COMMUNITY_Pull Request Template|Pull Request Template]]
- [[_COMMUNITY_Release Template|Release Template]]
- [[_COMMUNITY_GitHub Actions CI Workflow|GitHub Actions CI Workflow]]
- [[_COMMUNITY_Kubernetes Environment ConfigMap|Kubernetes Environment ConfigMap]]
- [[_COMMUNITY_Kubernetes Ingress and Service|Kubernetes Ingress and Service]]
- [[_COMMUNITY_Kubernetes Login Apps ConfigMap|Kubernetes Login Apps ConfigMap]]
- [[_COMMUNITY_Kubernetes Deployment Manifest|Kubernetes Deployment Manifest]]
- [[_COMMUNITY_Kubernetes Namespace Manifest|Kubernetes Namespace Manifest]]
- [[_COMMUNITY_Google-Authz Kubernetes Manifests|Google-Authz Kubernetes Manifests]]

## God Nodes (most connected - your core abstractions)
1. `Settings` - 66 edges
2. `EffectiveAuth` - 42 edges
3. `WorkspaceAuthorizationService` - 41 edges
4. `OAuthService` - 39 edges
5. `SessionManager` - 39 edges
6. `parameters` - 39 edges
7. `WorkspaceDirectoryClient` - 38 edges
8. `OAuthStateManager` - 37 edges
9. `EffectiveAuthCache` - 35 edges
10. `Request` - 33 edges

## Surprising Connections (you probably didn't know these)
- `Path` --uses--> `LoginAppRegistry`  [INFERRED]
  tests/test_login_apps.py → app/lib/login_apps.py
- `Request` --uses--> `Settings`  [INFERRED]
  app/lib/oauth.py → app/lib/config.py
- `Settings` --uses--> `Settings`  [INFERRED]
  app/lib/oauth.py → app/lib/config.py
- `Flow` --uses--> `Settings`  [INFERRED]
  app/lib/oauth.py → app/lib/config.py
- `Request` --uses--> `Settings`  [INFERRED]
  tests/test_login_app_session.py → app/lib/config.py

## Import Cycles
- 1-file cycle: `app/main.py -> app/main.py`

## Communities (72 total, 45 thin omitted)

### Community 0 - "Authorization and Session Management"
Cohesion: 0.09
Nodes (57): Path, Response, Settings, Settings, AuthzCheckRequest, AuthzCheckResponse, AuthzRequest, AuthzResponse (+49 more)

### Community 1 - "Authorization Request Handling"
Cohesion: 0.13
Nodes (40): Request, auth_callback(), authz(), authz_check(), build_session_response(), cache_key_for_email(), enforce_authz_request_guards(), ensure_origin_allowed() (+32 more)

### Community 2 - "API Parameter Definitions"
Cohesion: 0.19
Nodes (39): default, enum, enumDescriptions, location, type, required, description, format (+31 more)

### Community 3 - "API Endpoint Metadata"
Cohesion: 0.18
Nodes (32): deprecated, flatPath, httpMethod, parameterOrder, path, response, scopes, id (+24 more)

### Community 4 - "OAuth Service Implementation"
Cohesion: 0.13
Nodes (7): Request, Response, Settings, Flow, OAuthService, OAuthState, Handles Google OAuth flow + ID token validation.

### Community 5 - "Workspace Authorization Logic"
Cohesion: 0.22
Nodes (6): Any, EffectiveAuth, List group memberships for the user., Fetch Workspace data and normalize it into EffectiveAuth., Fetch a Workspace user with the configured custom schema., WorkspaceAuthorizationService

### Community 6 - "API Documentation Metadata"
Cohesion: 0.10
Nodes (19): auth, oauth2, basePath, baseUrl, batchPath, canonicalName, documentationLink, fullyEncodeReservedExpansion (+11 more)

### Community 7 - "Caching Implementations"
Cohesion: 0.22
Nodes (9): EffectiveAuth, Settings, build_cache(), InMemoryCache, Create the appropriate cache backend., Simple in-memory cache for development/test usage., Redis-based cache implementation., RedisCache (+1 more)

### Community 8 - "React Frontend Dependencies"
Cohesion: 0.13
Nodes (14): dependencies, react, react-dom, devDependencies, vite, @vitejs/plugin-react, name, private (+6 more)

### Community 9 - "React Frontend Dependencies"
Cohesion: 0.13
Nodes (14): dependencies, react, react-dom, devDependencies, vite, @vitejs/plugin-react, name, private (+6 more)

### Community 10 - "Permission and Session Checks"
Cohesion: 0.44
Nodes (8): Depends, Request, AuthzCheckResponse, get_settings(), inventory(), require_permission(), require_session(), Settings

### Community 12 - "Frontend Authz and Session Hooks"
Cohesion: 0.53
Nodes (3): App(), checkPermission(), useSession()

### Community 13 - "Login App Tests"
Cohesion: 0.60
Nodes (4): Path, test_login_app_registry_rejects_unapproved_redirect(), test_login_app_registry_rejects_unknown_app(), test_login_app_registry_validates_approved_redirect()

## Knowledge Gaps
- **89 isolated node(s):** `Path`, `Path`, `Any`, `baseUrl`, `documentationLink` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **45 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Authorization and Session Management` to `Authorization Request Handling`, `OAuth Service Implementation`, `Workspace Authorization Logic`, `Caching Implementations`, `Configuration Settings Management`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `LoginAppRegistry` connect `Authorization and Session Management` to `Authorization Request Handling`, `Login App Normalization`, `Login App Tests`, `Path Utilities`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `WorkspaceAuthorizationService` connect `Workspace Authorization Logic` to `Authorization and Session Management`, `Authorization Request Handling`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `Settings` (e.g. with `EffectiveAuth` and `Settings`) actually correct?**
  _`Settings` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `EffectiveAuth` (e.g. with `EffectiveAuth` and `Settings`) actually correct?**
  _`EffectiveAuth` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `WorkspaceAuthorizationService` (e.g. with `AuthzCheckRequest` and `AuthzCheckResponse`) actually correct?**
  _`WorkspaceAuthorizationService` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `OAuthService` (e.g. with `AuthzCheckRequest` and `AuthzCheckResponse`) actually correct?**
  _`OAuthService` has 24 INFERRED edges - model-reasoned connections that need verification._
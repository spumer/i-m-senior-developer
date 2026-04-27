# api-design — protocol and contract design

> API contract design, stack-agnostic. This file covers the **design angle**: which protocol, how to model resources, spec-first vs code-first, versioning strategy, error contract shape, pagination, idempotency. Loaded whenever the feature exposes or consumes an API, regardless of stack (Python, Node, or anything else).

## When to load

Load when the feature has any API surface: REST endpoint, GraphQL schema, gRPC service definition, WebSocket channel, or when the feature consumes an external API that must be contracted. Load regardless of backend stack.

## Protocol decision matrix

Protocol choice is a design decision that affects every client team. Make it explicit and justify it.

| Protocol | When to pick | When to avoid |
|---|---|---|
| **REST** | CRUD-ish resources; public or external API; broad client compatibility; team already knows HTTP semantics | Real-time bidirectional streams; highly client-specific data shapes with deep fan-out |
| **GraphQL** | Client-driven data shapes (client specifies exactly what fields it needs); federated data from multiple sources; multiple client types with different data needs (mobile vs web) | Simple CRUD where query flexibility is not needed — GraphQL's schema, resolvers, and N+1 problem add overhead without benefit |
| **gRPC** | Internal service-to-service high-throughput; strict binary contracts; polyglot microservices needing code generation; streaming required | Public APIs (Protobuf not browser-native without transcoding); small teams where schema overhead is high cost |
| **WebSocket** | Real-time bidirectional communication; live updates; collaborative features; push notifications | Request-response patterns that don't need persistence — SSE or polling is simpler and more cache-friendly |

**Decision rule (FPF A.11):** REST is the default. Escalate to GraphQL, gRPC, or WebSocket only with concrete evidence that REST cannot serve the stated requirements (e.g. client teams requiring different field shapes, latency requirements under 1ms, bidirectional streams). "GraphQL is more modern" is not evidence.

## REST resource modeling

Resources are the nouns of the API. Modeling them correctly at design time prevents URL debt.

**Resource = bounded context noun.** A resource maps to a domain concept the API exposes, not to a database table. One DB table does not imply one resource endpoint.

**HTTP verbs and idempotency:**

| Verb | Semantics | Idempotent? |
|---|---|---|
| GET | Read resource or collection | Yes |
| POST | Create resource; trigger action | No (by default) |
| PUT | Replace resource entirely | Yes |
| PATCH | Partial update | No (by default; design explicitly) |
| DELETE | Remove resource | Yes |

**URL hierarchy rules:**
- URL path reflects **ownership**: `/users/{id}/orders` means an order is owned by a user
- Do not reflect DB joins in URLs: `/orders?user_id=X` is better than `/users/{id}/orders` when the relationship is not ownership
- No verbs in URLs: `/getUserById` is RPC-over-HTTP, not REST

**Query parameters, headers, body:**
- Query params: filtering, sorting, pagination, projection (what fields to return)
- Headers: cross-cutting concerns (auth `Authorization`, content negotiation `Content-Type`/`Accept`, idempotency `Idempotency-Key`, tracing `X-Request-Id`)
- Body: resource representation on POST/PUT/PATCH

**Design output:** For each endpoint, document: method + path + auth requirement + query params + request body shape + response shape + possible error codes. The Hand-off Contracts table in the architecture document is the right home for this.

## OpenAPI / spec-first vs code-first

**Spec-first (write OpenAPI YAML → codegen server stubs and clients):**
- Backend writes the OpenAPI spec first; both server stubs and client SDKs are generated
- Best when: ≥2 client teams depend on the API; contract must be agreed before implementation starts; clients are in different languages
- Tools: openapi-generator, @openapitools/openapi-generator-cli

**Code-first (framework generates spec from code):**
- Backend writes code (FastAPI + Pydantic, NestJS decorators) and the framework generates the OpenAPI spec
- Best when: single-team, internal API; TypeScript monorepo where tRPC or Zod codegen handles types
- Risk: spec is a reflection of the code, not a contract — it is easy to accidentally break clients

**Decision rule:** Spec-first when ≥2 client teams. Code-first for single-team or internal-only. Document the choice and the toolchain in the architecture's Integration Points section.

**Mixed approach (common):** Backend uses code-first (FastAPI generates spec), but the generated spec is committed to the repo and treated as a contract (CI fails if the spec diff is not committed). This gives spec-first guarantees with code-first convenience.

## Versioning strategy

Versioning must be decided before the first API client ships. It cannot be retrofitted cleanly.

| Strategy | When to use | Trade-offs |
|---|---|---|
| **URL prefix (`/v1/`, `/v2/`)** | Breaking changes; broad client base; clear transition period | URL proliferation; old versions must be maintained |
| **Header-based (`Accept: application/vnd.api+json; version=2`)** | Clients control version; cleaner URLs | Less discoverable; harder to test in browser |
| **Media type versioning** | Content-type negotiation; fits hypermedia APIs | Complex tooling; rarely implemented correctly |

**Recommendation:** URL prefix for breaking changes. Backward-compatible additions (new optional fields, new endpoints) never require a version bump. Document the deprecation policy at design time:
- How long does v1 live after v2 ships? (e.g. "6 months minimum")
- How are clients notified of deprecation? (`Deprecation` header, changelog, email)
- What is the sunset date format? (`Sunset: Sat, 01 Jan 2026 00:00:00 GMT`)

**Semver for APIs:** A breaking change is: removing a field, changing a field type, changing HTTP status codes for existing conditions, changing auth scheme. Adding optional fields, adding new endpoints, adding new optional query params — these are not breaking.

## Error contract

Inconsistent error shapes are one of the most common API design failures. Clients write 5 different parsers and give up.

**Recommendation: Problem Details (RFC 7807).** Standard envelope with fields `type`, `title`, `status`, `detail`, `traceId`, optional `errors[]`. Specify the envelope shape in the architecture document; do not re-design per endpoint.

| Field | Required | Purpose |
|---|---|---|
| `type` | Yes | Machine-readable URI identifying the error class |
| `title` | Yes | Short human-readable summary |
| `status` | Yes | HTTP status code (repeat for client convenience) |
| `detail` | No | Human-readable explanation for this specific occurrence |
| `traceId` | Recommended | Correlates with server logs |
| `errors` | No | Array of field-level validation errors for 422 |

**Design rule:** Pick one error shape and use it everywhere. State it in the architecture document. Clients will rely on it.

**HTTP status codes — design-time mapping:**
- 400: client sent invalid data (validation, malformed JSON)
- 401: not authenticated
- 403: authenticated but not authorized
- 404: resource not found
- 409: conflict (e.g. duplicate create)
- 422: validation failed (semantically valid JSON but business rule violated)
- 429: rate limited
- 500: server fault (never leak stack traces to clients)

## Pagination, filtering, sorting

Decide the pagination strategy before any list endpoint ships. Changing it later breaks clients.

**Cursor vs offset:**

| Strategy | When to use | Limitation |
|---|---|---|
| **Cursor pagination** | Large or frequently-updated datasets; infinite scroll; real-time feeds | Cannot jump to arbitrary page |
| **Offset pagination (`?page=2&limit=20`)** | Small stable datasets; admin UIs where "go to page 5" is needed | Performance degrades on large offsets; results shift if dataset changes |

**Filter syntax options:**
- Simple query-string: `?status=active&created_after=2024-01-01` (sufficient for most cases)
- RSQL: `?filter=status==active;created>2024-01-01` (complex but standardized)
- JSON body filter (POST-based search): useful when filter criteria exceed URL length limits

**Sort syntax:** `?sort=created_at&order=desc` or `?sort=-created_at` (minus prefix = descending). Pick one convention and document it.

**Design rule:** Define the pagination strategy, filter syntax, and sort convention for the project once, in the architecture document. Every list endpoint follows it. Do not let each endpoint reinvent filtering syntax.

## Idempotency and retries

Document which endpoints are safe to retry at design time. Clients need this to build robust retry logic.

**HTTP semantics:**
- GET, PUT, DELETE are idempotent by HTTP definition (repeating the request produces the same result)
- POST is not idempotent by default
- PATCH is not idempotent by default (though can be designed to be)

**Making POST idempotent: design POST endpoints with irreversible side effects to require an `Idempotency-Key` header (client-generated UUID).** The server stores the key and result; repeated requests with the same key return the cached response. Required for: payment operations, order placement, email sending, any mutation with money or communication side effects. Specify required idempotency in the Hand-off Contracts table per endpoint.

**Design output for each endpoint:**
- Safe (read-only, no side effects): GET, HEAD, OPTIONS
- Idempotent (same result on repeat): GET, PUT, DELETE, POST with Idempotency-Key
- Non-idempotent (do not retry blindly): POST without Idempotency-Key, PATCH

Document retry-safe vs non-retry-safe classification in the Hand-off Contracts table. The implementer and the client team both need this.

## Common design pitfalls

- **Verbs in URLs (`/getUserById`, `/createOrder`).** This is RPC-over-HTTP, not REST. It breaks HTTP semantics, makes caching impossible (GET `/getUserById` is not cacheable), and confuses clients. Resources are nouns; verbs are HTTP methods.

- **Inconsistent error shapes.** If `/users` returns `{"error": "not found"}` and `/orders` returns `{"message": "Order does not exist", "code": 404}`, clients must write two error handlers. Pick one shape at design time and enforce it in the architecture.

- **Breaking changes without version bump.** Removing a field, changing a field type, or changing an HTTP status code for an existing condition is a breaking change. Without a version bump, existing clients break silently. Version strategy must be decided at design time.

- **GraphQL by default for simple CRUD.** GraphQL adds a schema definition, a resolver layer, a type system, and an N+1 problem that requires DataLoader. For straightforward CRUD with one or two client teams, this overhead is not justified. Start with REST; escalate to GraphQL with evidence.

- **No contract test plan.** Backend and frontend evolve independently. Without contract tests (consumer-driven contract tests via Pact, or snapshot tests of the OpenAPI spec), they drift. The architecture document should name the contract test strategy — even if "spec committed to repo and diff-checked in CI" is the answer. Leaving it undefined means it will not happen.

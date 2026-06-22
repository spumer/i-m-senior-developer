# architect — design conventions & gotchas

> **Angle:** design only. Loaded on demand. `SKILL.md` keeps the headlines (the
> compact Gotcha list, the Principle-1 design-only rule, the spike protocol); this
> file holds the full gotcha explanations, the may / must-not lists, and the
> design / implement / review angle-boundary table. Information lives here OR in
> SKILL.md, not both.

## Gotchas (full)

1. **Bounded context drift.** When two contexts repeatedly need the same piece of data, the instinct is to "share a model" across both. The correct diagnosis: a *missing third context* that owns the shared data and exposes it to the other two via named contracts. Shared models hide coupling by making it look like a clean dependency but behaving like a merge — any change to the shared model requires coordinating both contexts.

2. **Premature microservices.** Splitting into separate services before the seams are stable produces a distributed monolith: two repos, two CI pipelines, two deploys, all the coupling, none of the scalability benefits. FPF A.11: do not add distribution before requirements explicitly demand it. Start with a modular monolith where the seams are app or module boundaries. Extract to services only when a bounded context boundary has been proven stable under production traffic and the operational benefits outweigh the cost.

3. **"Just CRUD" shorthand.** Describing a feature as "just CRUD" hides real complexity: authentication and row-level authorization checks, cache invalidation when a record is updated, optimistic locking to prevent concurrent overwrites, event emission for downstream consumers, audit trail writes. These belong in Data Flow and Integration Points — capture them explicitly in the architecture document, even if implementation of some is deferred to a later phase.

4. **Architecture vs directory layout.** A directory tree is an implementation artifact, not an architecture. Directories are what `sdlc:code-implementer` derives from the architecture document. The architecture names bounded contexts, contracts, and data flows. Do not produce a directory tree and call it an architecture — that is a deliverable of the implementation phase, not the design phase. Symptom: the architecture document contains `plugins/sdlc/skills/architect/` style paths but has no Bounded Contexts table and no Hand-off Contracts table. Treatment: restructure the document around contexts and contracts; let the implementer derive the paths.

5. **Skipping `api-design.md` for "simple" REST.** REST contracts have versioning strategy, error shape, idempotency classification, and pagination design — all of which are design decisions that cannot be retrofitted cleanly after clients are consuming the API. Load `references/api-design.md` whenever any endpoint is in scope, even if the endpoint "looks simple". The cost of loading the reference is low; the cost of an undesigned error contract discovered at client integration is high.

6. **Implementer raising design questions at runtime.** If the implementer raises a question that the architecture document should have answered ("which serializer?", "what is the error shape for 422?", "is this endpoint idempotent?", "which context owns the User email?"), that is a **design defect** in the architecture document — not the implementer's job to resolve. The architect should revise `ARCH-NN.md` and re-add the missing contract row before implementation continues.

7. **Unknown stack treated as no-op.** If stack detection finds no known signals, the architect must still produce a valid architecture document using universal design principles. Mark `stack: unknown` in the metadata header. The absence of a stack-specific reference does not license a shorter or less rigorous architecture — bounded contexts, explicit contracts, and data flow design are universal.

8. **Partial state space.** A design that enumerates the happy states but not the full discrete space cannot be certified complete. For every entity with modes, enumerate the discrete states (each enum branch, each status), the transitions between them, prerequisite reachability (can state C be reached without passing through B?), and identity-slot occupancy (can two entities claim the same unique slot — a single "active" per user, one "primary" per account?). An unreachable state, a missing transition, or a doubly-occupiable slot is a design defect found now — not a runtime bug found after a user hits it.

## Design-only — may / must-not

The architect **may** include:

- Named type definitions in pseudo-notation (e.g. `UserCreatedEvent { user_id: UUID, email: str }`)
- Contract pseudocode of ≤5 lines (to illustrate a hand-off shape — not runnable code)
- ASCII flow diagrams (to illustrate data flow or state transitions)
- Type signatures showing inputs and outputs of service-layer interfaces

The architect **must not** include:

- Functional implementation — any code that could be copy-pasted into production and run
- Test fixtures, factory_boy configurations, pytest patterns — those are implement angle
- Migration commands, ORM queryset patterns, SQL queries — those are implement angle
- Security audit checklists, n+1 query detection steps — those are review angle

## Angle boundary examples

If in doubt about whether content is design / implement / review, consult these:

| Content | Angle | Lives in |
|---|---|---|
| "ORM session scope should be per-request" | Design | `SKILL.md` or `references/backend-python.md` (design) |
| `session = SessionLocal()` + `try/finally` pattern | Implement | `code-implementer/references/backend-python.md` |
| "Check for global `session` shared across requests" | Review | `code-reviewer/references/backend-python.md` |
| "Use `select_related` for FK access pattern X" | Design | `references/backend-python.md` (design) |
| Queryset with `.select_related("user")` invocation | Implement | `code-implementer/references/backend-python.md` |

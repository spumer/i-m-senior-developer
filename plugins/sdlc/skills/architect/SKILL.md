---
name: architect
description: >
  This skill should be used when designing system architecture: bounded
  contexts, module boundaries, data flow, integration contracts, API
  shape, hand-offs between components. Activates when the user asks to
  "design", "architect", "split into modules", "where are the boundaries",
  "design the data flow", or in russian «спроектируй», «архитектура»,
  «разбей на модули», «как разделить», when a feature README is presented
  before implementation, or when an existing system needs a new
  component. Loads stack-specific references (backend-python,
  frontend-react, api-design) on demand based on detected project
  signals. Produces an architecture document; never writes
  implementation code.
---

# Architect — system design

Designs **how** the system fits together: bounded contexts, contracts, data flow, and integration points across components. The single artifact of an architect activation is an architecture document in Markdown — design decisions and explicit hand-offs. Not code, not tests, not migrations.

The architect skill is activated before implementation. It is the first phase of the `sdlc` pipeline (`sdlc:architect` → `sdlc:code-implementer` → `sdlc:code-reviewer`). The architecture document it produces is the required input for `sdlc:code-implementer`. Starting implementation without an architecture document is a process violation that produces implementations the reviewer cannot validate against any stated design.

Outputs produced by the architect skill:

- One `ARCH-NN.md` file (primary output — always produced)
- Optionally, a conversation comment noting open questions that require human input before implementation (in session, not as a file)

Outputs the architect skill does **not** produce: source code, test files, migrations, configuration files, or any file that changes the running system.

## Principles

1. **Design only — no implementation hints beyond contract.**

   The architecture document may include type signatures and contract pseudocode (≤5 lines) to clarify a hand-off, but never functional implementation code. If a design decision requires a code spike to validate, say so explicitly: «needs a spike — `sdlc:code-implementer` to validate, then revisit». Do not write the spike. The seam between design and implementation is the architecture document itself — do not blur it.

2. **Bounded contexts (FPF A.1.1).**

   Name each context. Draw the seams. State what each context owns and what it does not. A context boundary is defined by what changes together — not by what is convenient to import. A seam is not a directory; directories are an output artifact, not the design. When two contexts repeatedly need the same data, the instinct is "share a model" — the correct diagnosis is a missing third context that owns the shared data.

3. **Evidence-based decisions (FPF A.10).**

   Claim "X is the bottleneck" or "Y will not scale" only when citing a file, a measurement, a prior incident, or a referenced document. Prediction without evidence is a design opinion, not a design decision. If evidence is missing, mark the decision as «assumption — needs validation» in Open Questions, and name who decides (architect, tech lead, measurement).

4. **Parsimony (FPF A.11).**

   Use the minimum number of components that solve the stated requirements. "We might need it later" is not sufficient justification for adding a component now. Every additional service, layer, or abstraction is complexity that the implementer must manage and the reviewer must audit. Escalate complexity only when requirements explicitly demand it.

5. **Explicit hand-offs.**

   Every cross-context call must have a named contract: input shape, output shape, and error mode. An implicit hand-off ("the implementer will figure it out") is a design defect. If the contract is unclear at design time, it will be invented independently by the backend and the frontend — producing two incompatible inventions that collide at integration time.

6. **Apply Functional Clarity.**

   If plugin `functional-clarity` is installed, activate `functional-clarity:functional-clarity` skill for the full 22-principle methodology. These principles apply at design time: Functional Visibility (is every contract visible from the outside?), Fail-Fast (does the design surface invalid states at boundaries?), Contract Explicitness (is every hand-off row complete?), Error Hiding prevention (does the design create conditions where errors will be silently swallowed?).

**Priority order when principles conflict:** (1) Fail-fast on missing input beats parsimony — do not produce a partial architecture. (2) Explicit hand-offs beat scope reduction — do not omit a contract row to keep the document short. (3) Parsimony beats completeness for implementation detail — do not add implementation-angle content to stay "thorough".

## Workflow

Five steps run on every architect activation. Steps 1 and 5 are always required; steps 2-4 branch on detected stack.

**Step 1 — Read input.**

Read the feature README or task description. If neither is present → fail-fast: «нужен README или PLAN-документ. Нельзя спроектировать то, что не описано.» Do not invent requirements to unblock the architecture session. If the README is ambiguous on a key decision point, surface it in Open Questions — do not resolve it silently.

Minimum readable input: a description of what the feature does, who uses it, and what the acceptance criteria are. If any of these three are missing, surface the gap in Open Questions before producing the architecture document.

**Step 2 — Detect stack.**

Scan the project root for signals:

- `pyproject.toml`, `requirements.txt`, or top-level `*.py` files → backend-python candidate
- `package.json` containing `"react"`, `"next"`, `"vue"`, or `"svelte"` → frontend candidate
- Both sets present → mixed stack

The detection-order rule: check Python markers first, then Node/frontend markers. The full 9-stack heuristic table (including Go, Java, mobile, and other stacks) lives in `plugins/planner/skills/planner/references/bootstrap.md` §4 — do not duplicate it here; reference it for edge-case or unknown stacks.

**Step 3 — Load matching references.**

Based on step 2:

- Python detected → load `references/backend-python.md`
- Frontend detected → load `references/frontend-react.md`
- API surface in scope (feature exposes or consumes HTTP/GraphQL/gRPC) → load `references/api-design.md`
- Mixed stack → load both stack references; produce one document with separate backend and frontend sections

**Step 4 — Produce the architecture document.**

Use the output format template below. Write to `<feature-dir>/ARCH-NN.md` (or `DESIGN-NN.md` — naming convention comes from `planner-context.md` §5 if present). Every section in the template is required; use `— none identified yet` rather than omitting a section entirely.

Work through the template in order:
- Start with Bounded Contexts — name all contexts before filling hand-off contracts.
- Fill Hand-off Contracts after contexts are named — each row requires both contexts to exist.
- Write Data Flow after contracts — the flow connects the contexts via their contracts.
- Fill Integration Points last — external dependencies usually emerge from the data flow.
- Always end with Open Questions — capture every unresolved decision, even minor ones.

**Step 5 — Hand-off.**

The final section of the architecture document names the next agent (`sdlc:code-implementer`) and the artifact path, so the orchestrator can dispatch without ambiguity. Do not stop before writing the Hand-off section. If the orchestrator is `/plan-do`, it reads this section to determine the next dispatch target.

If the architecture reveals that implementation should be split into parallel phases (e.g. backend and frontend are independent), note the parallelism in the Hand-off section. The orchestrator (`planner:planner`) uses this signal to parallelize the implementation phase.

## Stack detection (summary)

Scan project root for the file-based signals described above. Detection order: Python markers first (`pyproject.toml`, `requirements.txt`, top-level `*.py` files), then Node/frontend markers (`package.json`, `node_modules/`). Treat the first positive match as the primary stack candidate, but do not stop — scan for secondary stack markers too before concluding.

If both sets are present → mixed stack. Load both `references/backend-python.md` and `references/frontend-react.md`. Produce one architecture document with two clearly separated stack sections (Backend and Frontend). The Hand-off Contracts table explicitly covers cross-stack calls (e.g. "React component calls Python API endpoint").

If no signals match any known pattern → apply universal design principles. Set `stack: unknown` in the document metadata header. Do not fail. The full 9-stack heuristic table (9 stacks including Go, Java Spring, mobile, and others) lives in `plugins/planner/skills/planner/references/bootstrap.md` §4 — consult it before concluding "unknown".

## Output format — architecture document

Write the following template to `<feature-dir>/ARCH-NN.md`. Every section is required. Use `— none identified yet` if a section is empty at time of writing, but the architect must not silently skip Open Questions — if there are genuinely no open questions, write `— architecture is complete as stated`.

```markdown
# <FEAT-XXXX> Architecture (ARCH-NN)

> **Source feature:** <path/to/README.md>
> **Stack:** backend-python | frontend-react | mixed | unknown
> **References loaded:** <list>
> **Generated:** <ISO date>

## Bounded contexts
- <context-name>: <one-sentence purpose> — <module/path it lives in>
  - <sub-boundary if needed>: <one-sentence purpose>

## Hand-off contracts
| Caller | Callee | Input shape | Output shape | Error mode |
|---|---|---|---|---|
| <context-A> | <context-B> | <type or pseudocode> | <type or pseudocode> | <exception / HTTP status / empty> |

## Data flow
<diagram in ASCII or prose; one paragraph per major flow>

Flow 1 — <name>:
  <source> → <step> → <step> → <destination>
  Cache invalidation: <trigger> invalidates <key>
  Async: <event name> emitted when <condition>

## Integration points
- <external system>: <protocol> — <auth model> — <failure handling>
  - Retry: <yes/no, policy>
  - Failure degrade: <fallback behavior>

## Open questions
- <question> → <who decides> — <deadline or trigger for decision>

## Out of scope
- <thing that is NOT this feature> — <one-line reason it is excluded>

## Hand-off
Next agent: `sdlc:code-implementer`
Input: this document + project codebase
Artifact path: <feature-dir>/ARCH-NN.md
TDD: activate `tdd-master:tdd-master` before any production code
Stack references loaded: <list from metadata header>
```

**Section guidance:**

**Bounded contexts** — One bullet per context. Name it. State its single responsibility in one sentence. Name the module, app, or path where it lives. A context may have named sub-boundaries (e.g. a service layer within a Django app, a repository layer within a FastAPI service); add a nested bullet for each sub-boundary worth naming. Rule: if you cannot state the context's responsibility in one sentence, the context is not yet bounded — it is two contexts fused together.

**Hand-off contracts** — One row per cross-context call. Input and output shapes must be named types or brief inline pseudocode — not prose like "sends the user data". Error mode: what concretely happens on failure (exception class, HTTP status code, empty result, dead-letter queue). If the error mode is "unknown at design time", that belongs in Open Questions, not in this table.

**Data flow** — ASCII diagram or prose. One paragraph per major flow. Separate async flows from sync flows — they have different failure modes and different monitoring requirements. This section is where "just CRUD" hides its real complexity: cache invalidation on update, event emission to downstream consumers, optimistic locking to prevent concurrent overwrites, audit trail writes, webhook fan-out. Capture all of these explicitly, even if implementation of some is deferred to a later phase.

**Integration points** — Every external system the feature depends on (third-party API, message broker, S3, payment gateway) or exposes to (webhook consumer, client SDK). For each: the protocol, the auth model, the failure handling strategy (retry policy, circuit breaker, graceful degrade behavior).

**Open questions** — Every design decision that is unresolved at time of writing. Never genuinely empty on a non-trivial feature. If a decision is blocked on a stakeholder, name the stakeholder. If a decision requires a spike, name who runs the spike and when the answer is needed.

**Out of scope** — Explicitly names things the architecture consciously excludes with a one-line reason. Prevents scope creep during implementation. When in doubt, add a line — an explicit "out of scope" is better than silence that the implementer interprets as "in scope".

**Hand-off** — Always present as the last section. Names the next agent, the artifact path, and reminds the next agent to activate `tdd-master:tdd-master` before writing production code.

## Design-only rule

The architect does **not** write code, tests, or migrations. The architecture document is the only permitted output artifact.

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

**Spike protocol:** If a design decision requires running code to validate — benchmarking two ORM strategies, verifying that a framework supports a specific feature, measuring cache hit rates under realistic load — the architect writes this in Open Questions: «needs a spike — `sdlc:code-implementer` to validate, then revisit ARCH-NN §Hand-off contracts». The architect does not write the spike.

**Angle boundary examples** (if in doubt, consult these):

| Content | Angle | Lives in |
|---|---|---|
| "ORM session scope should be per-request" | Design | `SKILL.md` or `references/backend-python.md` (design) |
| `session = SessionLocal()` + `try/finally` pattern | Implement | `code-implementer/references/backend-python.md` |
| "Check for global `session` shared across requests" | Review | `code-reviewer/references/backend-python.md` |
| "Use `select_related` for FK access pattern X" | Design | `references/backend-python.md` (design) |
| Queryset with `.select_related("user")` invocation | Implement | `code-implementer/references/backend-python.md` |

## Gotchas

1. **Bounded context drift.**

   When two contexts repeatedly need the same piece of data, the instinct is to "share a model" across both. The correct diagnosis: a *missing third context* that owns the shared data and exposes it to the other two via named contracts. Shared models hide coupling by making it look like a clean dependency but behaving like a merge — any change to the shared model requires coordinating both contexts.

2. **Premature microservices.**

   Splitting into separate services before the seams are stable produces a distributed monolith: two repos, two CI pipelines, two deploys, all the coupling, none of the scalability benefits. FPF A.11: do not add distribution before requirements explicitly demand it. Start with a modular monolith where the seams are app or module boundaries. Extract to services only when a bounded context boundary has been proven stable under production traffic and the operational benefits outweigh the cost.

3. **"Just CRUD" shorthand.**

   Describing a feature as "just CRUD" hides real complexity: authentication and row-level authorization checks, cache invalidation when a record is updated, optimistic locking to prevent concurrent overwrites, event emission for downstream consumers, audit trail writes. These belong in Data Flow and Integration Points — capture them explicitly in the architecture document, even if implementation of some is deferred to a later phase.

4. **Architecture vs directory layout.**

   A directory tree is an implementation artifact, not an architecture. Directories are what `sdlc:code-implementer` derives from the architecture document. The architecture names bounded contexts, contracts, and data flows. Do not produce a directory tree and call it an architecture — that is a deliverable of the implementation phase, not the design phase.

   Symptom: the architecture document contains `plugins/sdlc/skills/architect/` style paths but has no Bounded Contexts table and no Hand-off Contracts table. Treatment: restructure the document around contexts and contracts; let the implementer derive the paths.

5. **Skipping `api-design.md` for "simple" REST.**

   REST contracts have versioning strategy, error shape, idempotency classification, and pagination design — all of which are design decisions that cannot be retrofitted cleanly after clients are consuming the API. Load `references/api-design.md` whenever any endpoint is in scope, even if the endpoint "looks simple". The cost of loading the reference is low; the cost of an undesigned error contract discovered at client integration is high.

6. **Implementer raising design questions at runtime.**

   If the implementer raises a question that the architecture document should have answered ("which serializer?", "what is the error shape for 422?", "is this endpoint idempotent?", "which context owns the User email?"), that is a **design defect** in the architecture document — not the implementer's job to resolve. The architect should revise `ARCH-NN.md` and re-add the missing contract row before implementation continues.

7. **Unknown stack treated as no-op.**

   If stack detection finds no known signals, the architect must still produce a valid architecture document using universal design principles. Mark `stack: unknown` in the metadata header. The absence of a stack-specific reference does not license a shorter or less rigorous architecture — bounded contexts, explicit contracts, and data flow design are universal.

## Integration with other plugins

**`tdd-master:tdd-master`** — The architect does not invoke this skill. However, test strategy decisions live in the design: which context boundaries need unit tests, which need integration tests, which need contract tests, which need end-to-end validation. These decisions appear in the architecture document (in Bounded Contexts and Hand-off Contracts) so that `sdlc:code-implementer` knows what test coverage is expected before writing any production code. The architect names the test boundary; the implementer names the test fixture.

**`functional-clarity:functional-clarity`** — Apply Functional Clarity principles. If plugin `functional-clarity` is installed, activate `functional-clarity:functional-clarity` skill for the full 22-principle methodology. During architecture: Functional Visibility (is every contract visible from the outside, or are there implicit side effects?), Fail-Fast (does the design surface invalid states at boundaries, or does it let invalid states propagate?), Contract Explicitness (is every hand-off table row complete, or are error modes left as "TBD"?), Error Hiding prevention (does the design create conditions where errors will be swallowed — e.g. event-driven flows with no dead-letter queue). If not installed, apply these principles from memory.

**`planner:planner`** — The orchestrator dispatches this skill via `/plan-do`. The architect never invokes the planner back. If the architecture session reveals that the task scope is materially larger than planned (e.g. "simple CRUD" requires a new bounded context and a data migration), the architect notes this in Open Questions and returns the architecture document; the orchestrator or the user decides whether to re-plan before calling `sdlc:code-implementer`. The planner reads `planner-context.md` to know this agent exists and to know its output is `ARCH-NN.md`.

**`document-skills:frontend-design`** — For UI-fidelity (visual quality, design polish, typography, spacing, component composition, taste), `references/frontend-react.md` mentions activating `document-skills:frontend-design`. If installed, it adds visual design discipline at design time: which design system, what the visual primitives are, how components compose visually, what the taste constraints are. If not installed, graceful degrade to universal principles (consistent spacing scale, readable typography, accessible color contrast). The architecture document always names the design system (e.g. shadcn/ui, MUI, Radix UI, custom Tailwind) and the CSS strategy — regardless of whether this skill is installed.

**Integration precedence:** These plugins collaborate, not compete. The architect activates `functional-clarity:functional-clarity` for design-time FPF analysis. The planner dispatches and reads the output. The implementer activates `tdd-master:tdd-master` downstream. The architect does not activate `tdd-master` or the implementer — that is the orchestrator's responsibility.

## When references are missing

If the detected stack has no matching reference (e.g. Go backend, Java Spring, iOS/Android mobile, Ruby on Rails, PHP):

1. Apply universal design principles: bounded contexts, explicit contracts, evidence-based decisions, parsimony, explicit hand-offs.
2. Set `stack: <detected-technology> — no specific reference, universal principles applied` in the architecture document's metadata header.
3. Do not fail the architecture session. Do not invent a reference inline (do not write an ad-hoc Go design guide embedded in the architecture document itself). Do not silently omit the metadata annotation.
4. Surface the gap in Open Questions: «No stack-specific reference exists for <technology>. Review `plugins/planner/skills/planner/references/bootstrap.md` §4 for full coverage map.» This allows a future plugin author or the repo owner to act on the gap.

Universal design principles that apply regardless of stack:
- Every context has a name, a single responsibility, and a named module or service boundary.
- Every cross-context call has a contract row (input, output, error mode).
- Data flow is documented before implementation begins.
- Integration points name protocol, auth model, and failure handling.
- Open questions are surfaced, not silently resolved.

## Reference index

Load references on demand — do not load all three on every activation. Load only what the detected stack and feature scope require.

A reference adds stack-specific design guidance; it does not replace the SKILL.md workflow. After loading a reference, return here and continue from step 4 (produce the architecture document). If the project has multiple stacks, load the relevant references before starting the template — do not fill the template in one stack's terms and then patch the other stack in.


- `references/backend-python.md` — **load when:** project is Python (Django / FastAPI / Flask / SQLAlchemy) and the design touches data, ORM, services, or background tasks.
  Contents (design angle): framework decision matrix, bounded contexts in Python backends, data layer design (aggregate roots vs anemic models, repository abstraction decision), async/sync boundary decision tree, background task infrastructure (Celery vs RQ vs APScheduler), API surface abstraction choice (DRF vs FastAPI Pydantic), common design pitfalls.

- `references/frontend-react.md` — **load when:** project is React / Vue / Svelte and the design touches components, state management, routing, or rendering boundaries.
  Contents (design angle): framework decision matrix (React+Vite vs Next.js vs SvelteKit), component boundary rules (stateful vs presentational, atomic vs feature-folder), state management decision tree (local / context / Zustand / Redux), data fetching architecture (TanStack Query / SWR / RSC), routing design (route list, auth guards, layout boundaries), type system at API boundaries, integration with `document-skills:frontend-design`.

- `references/api-design.md` — **load when:** the feature exposes or consumes an API (REST, GraphQL, gRPC, WebSocket), regardless of backend stack.
  Contents: protocol decision matrix, REST resource modeling (URL structure, verb-to-action mapping, idempotency table), spec-first vs code-first decision, versioning strategy (URL prefix vs header), error contract (RFC 7807 Problem Details), pagination and filtering design (cursor vs offset, filter syntax), idempotency and retry classification per endpoint.

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

   Every cross-context call must have a named contract: input shape, output shape, and error mode. An implicit hand-off ("the implementer will figure it out") is a design defect. If the contract is unclear at design time, it will be invented independently by the backend and the frontend — producing two incompatible inventions that collide at integration time. The contract's vocabulary belongs to the context that declares it — see §Boundary vocabulary.

6. **Apply Functional Clarity.**

   If plugin `functional-clarity` is installed, activate `functional-clarity:functional-clarity` skill for the full 22-principle methodology. These principles apply at design time: Functional Visibility (is every contract visible from the outside?), Fail-Fast (does the design surface invalid states at boundaries?), Contract Explicitness (is every hand-off row complete?), Error Hiding prevention (does the design create conditions where errors will be silently swallowed?).

**Priority order when principles conflict:** (1) Fail-fast on missing input beats parsimony — do not produce a partial architecture. (2) Explicit hand-offs beat scope reduction — do not omit a contract row to keep the document short. (3) Parsimony beats completeness for implementation detail — do not add implementation-angle content to stay "thorough".

## Workflow

Five steps run on every architect activation. Steps 1 and 5 are always required; steps 2-4 branch on detected stack.

**Step 1 — Read input.**

Read the feature README or task description. If neither is present → fail-fast: «нужен README или PLAN-документ. Нельзя спроектировать то, что не описано.» Do not invent requirements to unblock the architecture session. If the README is ambiguous on a key decision point, surface it in Open Questions — do not resolve it silently.

Minimum readable input: a description of what the feature does, who uses it, and what the acceptance criteria are. If any of these three are missing, surface the gap in Open Questions before producing the architecture document.

**Rank source authority.** When the README cites another artifact as authoritative — a canonical spec, an OpenAPI contract, a domain protocol — that primary source outranks the README's paraphrase of it. Before encoding a "X is forbidden" / "Y is required" constraint into the design, verify it against the cited primary source (`Read`/`grep` the actual line). A constraint that paraphrases without a findable source is an Open Question, not a design rule (FPF A.10) — the orchestrator's framing is not evidence.

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

Use the output format template below. Resolve the target path in this order: the document named by the orchestrator (under `/plan-do` this is the `ARCHITECTURE.md` referenced in the execution plan header) → the project's convention from `planner-context.md` §5 → `<feature-dir>/ARCH-NN.md`. Update that document in place; never add a second architecture file beside it, because the execution plan's freshness gate tracks one path only. Every section in the template is required; use `— none identified yet` rather than omitting a section entirely.

Work through the template in order:
- Start with Bounded Contexts — name all contexts before filling hand-off contracts.
- Fill Hand-off Contracts after contexts are named — each row requires both contexts to exist.
- Write Data Flow after contracts — the flow connects the contexts via their contracts.
- Fill Integration Points last — external dependencies usually emerge from the data flow.
- Fill Decisions & owners after Integration Points — every behavioral predicate is either committed here or surfaced as an Open Question.
- Always end with Open Questions — capture every unresolved decision, even minor ones.

**Step 5 — Hand-off.**

The final section of the architecture document names the next agent (`sdlc:code-implementer`) and the artifact path, so the orchestrator can dispatch without ambiguity. Do not stop before writing the Hand-off section. If the orchestrator is `/plan-do`, it reads this section to determine the next dispatch target.

If the architecture reveals that implementation should be split into parallel phases (e.g. backend and frontend are independent), note the parallelism in the Hand-off section. The orchestrator (`planner:planner`) uses this signal to parallelize the implementation phase.

## Stack detection (summary)

Stack detection is Step 2 above — Python markers first (`pyproject.toml`, `requirements.txt`, top-level `*.py`), then Node/frontend (`package.json` with `react`/`next`/`vue`/`svelte`); scan for secondary markers before concluding. Both → mixed: load both references, produce one document with separate Backend/Frontend sections, and cover cross-stack calls in the Hand-off Contracts table. No match → `stack: unknown`, universal principles, do not fail. The full 9-stack heuristic table lives in `plugins/planner/skills/planner/references/bootstrap.md` §4.

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
| Caller | Callee | Input shape | Output shape | Error mode | Vocabulary |
|---|---|---|---|---|---|
| <context-A> | <context-B> | <type or pseudocode> | <type or pseudocode> | <exception / HTTP status / empty> | <declaring context — whose language names this contract> |

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

## Decisions & owners
| Decision (behavioral predicate) | Verdict | Owner | Traces to requirement |
|---|---|---|---|
| <e.g. "duplicate email on signup"> | committed: <chosen behavior> — OR — implementer's-choice: <constraint to satisfy> | <single owner> | <README / AC line> |

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

The feature-id (`FEAT-XXXX`) appears in the document title and in
artifact filenames only. Do not embed it in contract pseudocode, code
snippets, or identifier names anywhere in the document — the
implementer copies these fragments verbatim, and the ID leaks into
code comments and identifiers.

**Section guidance:**

**Bounded contexts** — One bullet per context. Name it. State its single responsibility in one sentence. Name the module, app, or path where it lives. A context may have named sub-boundaries (e.g. a service layer within a Django app, a repository layer within a FastAPI service); add a nested bullet for each sub-boundary worth naming. Rule: if you cannot state the context's responsibility in one sentence, the context is not yet bounded — it is two contexts fused together.

**Hand-off contracts** — One row per cross-context call. Input and output shapes must be named types or brief inline pseudocode — not prose like "sends the user data". Error mode: what concretely happens on failure (exception class, HTTP status code, empty result, dead-letter queue). If the error mode is "unknown at design time", that belongs in Open Questions, not in this table. Vocabulary: name the context whose language the contract speaks — the answer must be the declaring context. Fill it for every row; on rows created by dependency inversion (the port is declared in one context, implemented in another) run the substitution test before accepting the names — see §Boundary vocabulary.

**Data flow** — ASCII diagram or prose. One paragraph per major flow. Separate async flows from sync flows — they have different failure modes and different monitoring requirements. This section is where "just CRUD" hides its real complexity: cache invalidation on update, event emission to downstream consumers, optimistic locking to prevent concurrent overwrites, audit trail writes, webhook fan-out. Capture all of these explicitly, even if implementation of some is deferred to a later phase.

**Integration points** — Every external system the feature depends on (third-party API, message broker, S3, payment gateway) or exposes to (webhook consumer, client SDK). For each: the protocol, the auth model, the failure handling strategy (retry policy, circuit breaker, graceful degrade behavior).

**Decisions & owners** — One row per behavioral predicate the feature decides (how it behaves at a fork: duplicate email, empty-cart checkout, concurrent edit, missing optional field). Each predicate is either **committed** (name the single chosen behavior — never "A or B"; the implementer does not re-decide) or **implementer's-choice** (the implementer may pick; name the constraint the choice must satisfy). Exactly one owner per predicate. Trace each to the requirement that motivates it: a decision with no requirement is scope creep; a requirement with no decision is an Open question. This is the seam that stops the implementer from raising design questions at runtime (Gotcha 6).

**Open questions** — Every design decision that is unresolved at time of writing. Never genuinely empty on a non-trivial feature. If a decision is blocked on a stakeholder, name the stakeholder. If a decision requires a spike, name who runs the spike and when the answer is needed.

**Out of scope** — Explicitly names things the architecture consciously excludes with a one-line reason. Prevents scope creep during implementation. When in doubt, add a line — an explicit "out of scope" is better than silence that the implementer interprets as "in scope".

**Hand-off** — Always present as the last section. Names the next agent, the artifact path, and reminds the next agent to activate `tdd-master:tdd-master` before writing production code.

## Boundary vocabulary

A context boundary has two layers: structure (imports, cycles, dependency direction — covered by the sections above) and vocabulary. **What a context declares on its boundary it names in its own language.** The rule is scale-free — it holds for a layer inside an app, a module in a monolith, a service, a schema published to another team. Everything declared in context A — port names, method names, parameter names and types, event names, schema fields, docstrings — is phrased in A's own facts and needs. The counterpart's actions, mechanisms, and domain terms must not enter A's vocabulary through any channel: not as a name, not as a signature/type, not as prose. Translating between vocabularies is the dependent side's duty, on its own territory (adapter, anticorruption layer) — the owner never pre-names things "conveniently" for a consumer.

This matters most under dependency inversion: when B depends on A, the contract is declared in A and implemented in B — precisely then nothing structural stops B's vocabulary from leaking into A's names (imports stay clean, the type checker stays happy), so the check must be explicit at design time, where the boundary names are born.

**Substitution test** (objective criterion): mentally replace the implementation/subscriber with a different one — another channel, another mechanism, a second consumer alongside the first. Do the name, the signature, and the docstring stay accurate? If anything would need editing, the element carries foreign vocabulary — a boundary defect, not taste.

Applying it in the architecture document: fill the Vocabulary column of the Hand-off contracts table for every row; the answer must be the declaring context. Signatures pass only the owner's facts (ids, transactional context) — never the subscriber's tuning knobs (queue names, retry counts, channel selectors). Event names state the owner's fact (`user_registered`), not the expected reaction (`trigger_welcome_email`).

Scope guard: the rule applies to elements declared on a boundary between contexts — not to names internal to one context, and not to presentation-layer copy (button labels, operator-facing texts). The normative text — leak channels, per-scale examples, leak classes with ❌/✅, false-positive cases — lives in one place: `functional-clarity:functional-clarity` → `references/06-boundary-vocabulary.md`. This section is a reminder, not a copy; when in doubt, read the reference. If the plugin is not installed, apply the rule as stated here.

## Design-only rule

The architect does **not** write code, tests, or migrations — the architecture document is the only output artifact (Principle 1). It **may** include named type definitions, ≤5-line contract pseudocode, ASCII flow diagrams, and service-interface type signatures; it **must not** include functional implementation, test fixtures, ORM/SQL queries, or review/security checklists. The full may / must-not lists and the design / implement / review angle-boundary table are in `references/design-conventions.md`.

**Spike protocol:** if a design decision requires running code to validate (benchmark two ORM strategies, verify a framework feature, measure cache hit rates), write it in Open Questions: «needs a spike — `sdlc:code-implementer` to validate, then revisit ARCH-NN §Hand-off contracts». The architect does not write the spike.

## Gotchas

Headlines below; full explanations in `references/design-conventions.md`.

1. **Bounded context drift** — two contexts needing the same data → a *missing third context* that owns it, not a shared model.
2. **Premature microservices** — splitting before seams are stable = a distributed monolith (FPF A.11). Start modular-monolith; extract only when a boundary is proven stable under load.
3. **"Just CRUD" shorthand** — hides auth, cache invalidation, optimistic locking, event emission, audit writes. Capture them in Data Flow / Integration Points.
4. **Architecture vs directory layout** — a directory tree is an implementation artifact; the architecture names contexts, contracts, and flows (let the implementer derive paths).
5. **Skipping `api-design.md` for "simple" REST** — versioning, error shape, idempotency, pagination can't be retrofitted. Load it whenever any endpoint is in scope.
6. **Implementer raising design questions at runtime** — "which serializer? error shape for 422? idempotent?" is a design defect; revise `ARCH-NN.md` and add the missing contract row.
7. **Unknown stack treated as no-op** — still produce a full architecture with universal principles; mark `stack: unknown`. No stack reference ≠ a shorter architecture.
8. **Partial state space** — enumerate every discrete state, transition, prerequisite reachability, and identity-slot occupancy; an unreachable / missing-transition / doubly-occupiable state is a design defect found now, not a runtime bug later.
9. **Vocabulary leak across the boundary** — a port/event declared in context A named with the subscriber's action or mechanism (`InvoiceEmailQueuePort.enqueue_email`); imports are clean, so structural checks stay silent. Run the substitution test on every inverted-dependency contract row (§Boundary vocabulary).

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

- `references/design-conventions.md` — loaded on demand (stack-agnostic, always available). Full Gotcha explanations, the design-only may / must-not lists, and the design / implement / review angle-boundary table. SKILL.md keeps the headlines; this holds the detail.

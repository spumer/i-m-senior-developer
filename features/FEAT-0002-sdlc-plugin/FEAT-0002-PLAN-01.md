# FEAT-0002 — SDLC Plugin: Architecture (PLAN-01)

> **Source feature spec:** `features/FEAT-0002-sdlc-plugin/README.md`
> **Planner output (parallelization scheme):** `features/FEAT-0002-sdlc-plugin/PLANNER_OUTPUT.md`
> **Structural prior-art:** `features/FEAT-0001-planner-plugin/FEAT-0001-PLAN-01.md`
> **Marketplace target:** `i-m-senior-developer`
> **Initial version:** `0.1.0`
> **Sibling plugins referenced:** `tdd-master`, `functional-clarity`, `planner`, `document-skills` (built-in)

This document is the implementation contract. Every artifact, frontmatter field, section name, length budget, content origin, and cross-plugin reference is specified here. Implementers (3 parallel sonnet agents per Phase 2a + 1 each for 2b and 2c) fill in content per the spec; they do not make architectural choices. Where this contract is silent, implementers must surface a question instead of guessing.

The plugin's central design tension is the **same-name-different-angle reference files** (`backend-python.md` and `frontend-react.md` exist in all 3 skills). §12 Decision 2 resolves this with explicit angle assignment per file. Implementers must follow the angle exactly — duplication of content across angles is a defect.

---

## §1. Plugin Directory Layout (target)

```
plugins/sdlc/
├── .claude-plugin/
│   └── plugin.json                                       # manifest (§2)
├── agents/
│   ├── architect.md                                      # ~30 lines — thin wrapper, model=opus (§4.1)
│   ├── code-implementer.md                               # ~30 lines — thin wrapper, model=sonnet (§4.2)
│   └── code-reviewer.md                                  # ~30 lines — thin wrapper, model=sonnet (§4.3)
├── skills/
│   ├── architect/
│   │   ├── SKILL.md                                      # design-only core, ≤500 (target 280-340) lines (§5)
│   │   └── references/
│   │       ├── backend-python.md                         # ~140-170 lines — design angle (§6.1)
│   │       ├── frontend-react.md                         # ~140-170 lines — design angle (§6.2)
│   │       └── api-design.md                             # ~140-170 lines — REST/GraphQL/OpenAPI (§6.3)
│   ├── code-implementer/
│   │   ├── SKILL.md                                      # implement core, ≤500 (target 280-340) lines (§7)
│   │   └── references/
│   │       ├── backend-python.md                         # ~140-170 lines — implement angle (§8.1)
│   │       └── frontend-react.md                         # ~140-170 lines — implement angle (§8.2)
│   └── code-reviewer/
│       ├── SKILL.md                                      # review core, ≤500 (target 280-340) lines (§9)
│       └── references/
│           ├── security.md                               # ~160-190 lines — OWASP, always-active (§10.1)
│           ├── backend-python.md                         # ~140-170 lines — review angle (§10.2)
│           └── frontend-react.md                         # ~140-170 lines — review angle (§10.3)
└── README.md                                             # plugin-level + migration guide (§11)
```

Plus one **edit** to `.claude-plugin/marketplace.json` (root of repo) — §3.

Anything not listed above must NOT be created. No `hooks/` directory ships in v0.1.0 (per §12 Decision 3). No `commands/` — the orchestrator (`/plan-do` from the `planner` plugin) drives sdlc agents; sdlc itself ships none.

**Total deliverables: 15 files** (1 manifest + 3 agents + 3 SKILL.md + 8 references + 1 plugin README) + 1 marketplace edit.

---

## §2. Plugin Manifest (`plugins/sdlc/.claude-plugin/plugin.json`)

Single JSON object. No comments. Fields exactly as below. Match the existing `planner/plugin.json` and `tdd-master/plugin.json` style (no `category` field — that lives only in marketplace.json).

| Field | Value | Rationale |
|---|---|---|
| `name` | `sdlc` | kebab-case, matches directory; plugin namespace will be `sdlc:` |
| `version` | `0.1.0` | per CLAUDE.md semver mandate, initial release |
| `description` | `Software Development Life Cycle plugin: 3 agents (architect, code-implementer, code-reviewer) covering design, implementation, and review across backend (Python) and frontend (React) stacks. Replaces legacy ~/.claude/agents/python-implementer.md, django-architect.md, code-reviewer.md. References tdd-master and functional-clarity plugins instead of duplicating their content.` | matches `planner` description style: first sentence states value, second states migration scope, third states cross-plugin integration. ≤450 chars. |
| `author.name` | `Svyatoslav Posokhin` | matches all sibling manifests |
| `keywords` | `["sdlc", "architect", "code-implementer", "code-reviewer", "backend-python", "frontend-react", "multi-agent", "development-pipeline"]` | discoverability: 3 roles + 2 stacks + concept tags |

Do **not** add a `category` field (project convention — see §3 for marketplace `category`).

Do **not** add a `repository` field — none of the sibling plugins have one; this is a monorepo and the marketplace entry's `source: ./plugins/sdlc` already locates the code.

---

## §3. Marketplace Entry (edit `.claude-plugin/marketplace.json`)

Append the following object to the `plugins` array, **after** the `planner` entry (chronological order). Do not change other entries. Field order follows the existing `planner` entry style.

```json
{
  "name": "sdlc",
  "description": "SDLC pipeline plugin: 3 agents (architect, code-implementer, code-reviewer) covering design → implement → review across Python backend and React frontend. Stack-aware via on-demand references. References tdd-master and functional-clarity instead of duplicating.",
  "author": {
    "name": "Svyatoslav Posokhin"
  },
  "source": "./plugins/sdlc",
  "category": "development"
}
```

The marketplace `description` (≤300 chars) is what users see in plugin pickers — keep it informative but concise. The `description` here may differ slightly from `plugin.json` `description` (marketplace has tighter character budget); prioritize the value-prop sentence.

---

## §4. Agent Wrapper Specs (3 files, ~30 lines each)

All three wrappers follow the canonical pattern from `plugins/planner/agents/planner.md`:

1. YAML frontmatter (name / model / color / tools / description with russian triggers + 2 `<example>` blocks).
2. Body: H1 role line, `## Activation` (one paragraph delegating to the skill), `## Boundaries` / `## Границы` (5 bullets), `## What this agent is NOT` (1 paragraph).

Body length budget per wrapper: **25-35 lines** (excluding frontmatter). Total file with frontmatter: **45-65 lines**. Wrapper does **not** repeat skill workflow — it points to the skill and stops.

### §4.1 `agents/architect.md`

| Frontmatter field | Value | Justification |
|---|---|---|
| `name` | `architect` | matches skill folder; namespace yields `sdlc:architect` |
| `model` | `opus` | architecture is high-leverage, low-frequency; design errors propagate downstream into implementation and review (FPF A.10 — evidence: FEAT-0001-PLAN-01.md was authored on opus for the same reason). README §58 explicitly mandates `model=opus`. |
| `color` | `blue` | sibling colors taken: `cyan` (planner), `green` (tdd-master), `magenta` (llms-keeper). Pick `blue` for architect, `purple` for code-implementer, `red` for code-reviewer (collision-free across the marketplace). |
| `tools` | `["Read", "Grep", "Glob", "Write"]` | least-privilege. Read/Grep/Glob = scan project for stack signals, read existing architecture docs. Write = output architecture document only. **No `Edit`** (architect designs new artifacts; implementer modifies code). **No `Bash`** (architect does not execute anything). |
| `description` | multi-line YAML literal block (`description: \|`) — see content below | russian + english triggers + 2 `<example>` blocks |

**Description content (third-person, gerund where natural — Anthropic best-practice; russian + english triggers per project convention):**

```
description: |
  Designs system architecture: bounded contexts, hand-offs, contracts,
  data flow, integration points. Activates the `sdlc:architect` skill
  which loads stack-specific design references (backend-python /
  frontend-react / api-design) on demand. Produces an architecture
  document for the implementer; never writes implementation code.

  Вызывай этого агента для проектирования: «спроектируй», «архитектура»,
  «design this feature», «как разбить модули», «где границы», получен
  README фичи и нужен ARCH-документ перед /plan-do.

  <example>
  user: Готов README фичи FEAT-0042. Нужна архитектура.
  assistant: Запускаю sdlc:architect — он спроектирует bounded contexts
  и контракты, прочитает references по стеку проекта (backend-python),
  и положит архитектурный документ рядом с README.
  </example>

  <example>
  user: Design the data flow for the new payment integration.
  assistant: Calling sdlc:architect — it will load backend-python and
  api-design references, sketch the bounded contexts, and emit an
  architecture document with explicit hand-off contracts.
  </example>
```

**Body (25-35 lines):**

1. **H1:** `# Architect — system design dispatcher`
2. **Role paragraph (3-4 lines):** "You are an architect. You design systems, you do not implement them. Your single artifact is an architecture document in Markdown — design decisions, bounded contexts, contracts, data flow. No code, no tests, no migrations."
3. **`## Activation` (3-4 lines):** "On invocation, read the `sdlc:architect` skill and follow it. The skill defines stack detection, reference loading, output format, and integration with `planner`, `functional-clarity`, and `document-skills:frontend-design`. Do not inline that workflow here."
4. **`## Границы` (5 bullets, mirrors `planner` agent boundaries pattern):**
   - Ты НЕ пишешь код / тесты / миграции — только design.
   - Ты НЕ редактируешь существующий код проекта.
   - Write-разрешён ТОЛЬКО на: `<feature-dir>/ARCH-NN.md` (или `DESIGN-NN.md`, имя по соглашению проекта из `planner-context.md` §5).
   - Ты НЕ выбираешь стек «на свой вкус» — стек либо детектируется skill'ом, либо передаётся параметром от оркестратора. Если стек неизвестен → applies universal principles + помечает в output `stack: unknown`.
   - При конфликте простоты и «модности» побеждает простота (FPF A.11 — parsimony).
5. **`## What this agent is NOT`:** "Not an implementer; not a reviewer. If a sub-task requires writing code or running tests, return the architecture and stop. The orchestrator dispatches the `code-implementer` next."

### §4.2 `agents/code-implementer.md`

| Frontmatter field | Value | Justification |
|---|---|---|
| `name` | `code-implementer` | matches skill folder; namespace `sdlc:code-implementer` |
| `model` | `sonnet` | implementation is volume work — many files, many calls; sonnet cost/quality is the right point. README §59 mandates `model=sonnet`. |
| `color` | `purple` | collision-free per §4.1 color rationale |
| `tools` | `["Read", "Edit", "Write", "Grep", "Glob", "Bash"]` | implementer modifies code (Edit), creates new files (Write), runs tests (Bash). README/legacy `python-implementer.md` used same set. |
| `description` | YAML literal block, see below | russian + english triggers + 2 `<example>` blocks |

**Description content:**

```
description: |
  Implements code per an architecture document: TDD cycle, minimal
  changes, fail-fast. Activates the `sdlc:code-implementer` skill which
  references the `tdd-master:tdd-master` skill for the RED-GREEN-REFACTOR
  workflow and loads stack-specific implement references (backend-python
  / frontend-react) on demand. Never designs systems; never reviews
  others' code.

  Вызывай для имплементации: «реализуй», «закодь», «implement this»,
  «add the endpoint», получен ARCH/PLAN-документ и нужно писать код.

  <example>
  user: Архитектура готова, реализуй фичу FEAT-0042.
  assistant: Запускаю sdlc:code-implementer — он начнёт с RED-фазы по
  tdd-master, прочитает references по backend-python для ORM/migrations
  и сделает минимальные изменения.
  </example>

  <example>
  user: Implement the React component per the design doc.
  assistant: Calling sdlc:code-implementer — it activates tdd-master and
  loads frontend-react reference (vitest + RTL + hooks).
  </example>
```

**Body (25-35 lines):**

1. **H1:** `# Code-Implementer — TDD-first implementation dispatcher`
2. **Role paragraph (3-4 lines):** "You are an implementer. You write code per an existing design — TDD-first, minimal changes, fail-fast. Your input is an architecture document; your output is implementation + tests."
3. **`## Activation`:** "On invocation, read the `sdlc:code-implementer` skill and follow it. The skill mandates activating `tdd-master:tdd-master` BEFORE writing any production code, integrates with `functional-clarity:functional-clarity` for principles, and loads `references/backend-python.md` or `references/frontend-react.md` per detected stack."
4. **`## Границы`:**
   - Ты НЕ проектируешь архитектуру — если ARCH-документа нет, fail-fast: «нужен ARCH/PLAN-документ; вызови sdlc:architect».
   - Ты НЕ ревьюишь чужой код — это работа `sdlc:code-reviewer`.
   - Ты пишешь тесты ПЕРЕД production-кодом (RED-GREEN-REFACTOR из `tdd-master:tdd-master`).
   - Ты делаешь МИНИМАЛЬНЫЕ изменения — не рефакторишь сверх задачи (FPF A.11; project rule `code-change-discipline.md`).
   - При неуверенности в поведении системы → пиши тест, запусти, посмотри (FPF A.10) — не утверждай «работает так» без evidence.
5. **`## What this agent is NOT`:** "Not an architect; not a reviewer. If the design is missing or contradictory, stop and ask. Do not invent design decisions to unblock implementation."

### §4.3 `agents/code-reviewer.md`

| Frontmatter field | Value | Justification |
|---|---|---|
| `name` | `code-reviewer` | matches skill folder; namespace `sdlc:code-reviewer` resolves the legacy collision automatically (see §11 migration) |
| `model` | `sonnet` | review = pattern-matching against checklists; sonnet sufficient. README §60 mandates. |
| `color` | `red` | collision-free; semantically appropriate for review/defects |
| `tools` | `["Read", "Grep", "Glob", "Bash"]` | reviewer reads code (Read/Grep/Glob), runs `git diff` and tests (`Bash` restricted). **No `Write` / `Edit`** — reviewer never modifies code; outputs review-request-changes file via Bash heredoc or chat. README/legacy `code-reviewer.md` had similar restriction. |
| `description` | YAML literal block, see below | russian + english triggers + 2 `<example>` blocks |

**Description content:**

```
description: |
  Reviews code changes for security, system issues, FPF/Functional
  Clarity violations, and stack-specific pitfalls. Activates the
  `sdlc:code-reviewer` skill which always loads `references/security.md`
  (OWASP Top 10), and stack-specific `references/backend-python.md` or
  `references/frontend-react.md` on demand. Operates on git-diff; never
  modifies code itself.

  Вызывай для ревью: «отревью», «проверь код», «review this PR»,
  «есть ли security-проблемы», после implementer-фазы перед merge.

  <example>
  user: Закончил имплементацию FEAT-0042, отревью.
  assistant: Запускаю sdlc:code-reviewer — он возьмёт git-diff, прогонит
  security checklist (всегда), и стэк-специфичный reference (backend-python
  для n+1, ORM pitfalls, atomic ops).
  </example>

  <example>
  user: Review the React PR, focus on accessibility and XSS.
  assistant: Calling sdlc:code-reviewer — security.md auto-loads (XSS, CSP),
  frontend-react.md adds accessibility/perf/hooks pitfalls.
  </example>
```

**Body (25-35 lines):**

1. **H1:** `# Code-Reviewer — system-issues + security dispatcher`
2. **Role paragraph (3-4 lines):** "You are a reviewer. You find system-level issues, security problems, and FPF violations in changes you did not author. You operate on git-diff. You produce a review report; you never modify code."
3. **`## Activation`:** "On invocation, read the `sdlc:code-reviewer` skill and follow it. The skill always activates `references/security.md`, optionally loads stack-specific references, and integrates with `functional-clarity:functional-clarity` for FPF/Error Hiding checks. Output goes to `<feature-dir>/review-request-changes/REVIEW-NN.md` or chat if no feature dir exists."
4. **`## Границы`:**
   - Ты НЕ правишь код. Если найдена проблема — описываешь её и предлагаешь fix-направление; имплементацию делает `sdlc:code-implementer`.
   - Ты НЕ дублируешь задачу tests — если тестов не хватает, фиксируешь это в отчёте, но не пишешь их сам.
   - Ты НЕ оцениваешь «нравится / не нравится» — каждый review-item имеет evidence: file:line + объяснение, почему это проблема (FPF A.10).
   - Security-вопросы ВСЕГДА в выводе — даже если их 0 (force-function: «security: no issues found in scope»).
   - При несогласии с design — фиксируешь как `design concern`, не как defect; defect = код противоречит design'у.
5. **`## What this agent is NOT`:** "Not an implementer; not an architect. Findings include `file:line` references; the implementer applies the fix. If a finding implies an architecture change, escalate to architect via the orchestrator."

---

## §5. Skill `architect` — `plugins/sdlc/skills/architect/SKILL.md`

Hard length budget: **≤500 lines** (Anthropic best-practice). Target: **280-340 lines**. If exceeded → push content into a new reference (max 1 level deep, per README §79).

### §5.1 Frontmatter spec

| Field | Value |
|---|---|
| `name` | `architect` |
| `description` | Third-person; russian+english triggers; ≤900 chars (Anthropic best-practice — keep skill descriptions tight). Exact template below. |

**Description template (verbatim — translate freely if too long, but keep all triggers):**

```
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
```

### §5.2 Section outline (full skeleton — fill, do not add new sections)

| § | Section | Content origin / what to include | Lines |
|---|---|---|---|
| 1 | `# Architect — system design` (H1) + 2-sentence purpose | Designs **how** the system fits together: contexts, contracts, data flow. Output is an architecture document, not code. | 5 |
| 2 | `## Principles` | 6 numbered design-only principles. **No FC duplication** — point to `functional-clarity:functional-clarity`. List: (1) Design only — no implementation hints beyond contract; (2) Bounded contexts (FPF A.1.1) — name them, draw the seams; (3) Evidence-based decisions (FPF A.10) — cite files / docs / measurements when claiming "X is bottleneck"; (4) Parsimony (FPF A.11) — minimum components that solve the problem; (5) Explicit hand-offs — every cross-context call has a contract (input / output / error mode); (6) Apply Functional Clarity — if `functional-clarity:functional-clarity` is installed, activate it for the full 22-principle set. | 30 |
| 3 | `## Workflow` | 5 numbered steps: (1) Read input README / task description; if missing → fail-fast «нужен README или PLAN»; (2) Detect stack from project signals (`pyproject.toml` → backend-python; `package.json` + `react` → frontend-react; both → mixed) — same heuristics as `planner/references/bootstrap.md` §4 (do not duplicate the table; reference it); (3) Load matching reference(s) — `references/backend-python.md`, `references/frontend-react.md`, or both; load `references/api-design.md` when API surface is in scope; (4) Produce architecture document per §5 below; (5) Hand-off — name the next agent (`sdlc:code-implementer`) and the artifact path. | 25 |
| 4 | `## Stack detection (summary)` | 5-line summary of the stack-detection heuristic; pointer to `plugins/planner/skills/planner/references/bootstrap.md` §4 as the master table. **Do not duplicate the 9-row table** — reference it. State the detection-order rule (Python before Node before Frontend) inline. Mixed-stack rule: if both detected, load both references and produce a single architecture document with two stack sections. | 10 |
| 5 | `## Output format — architecture document` | The full markdown template for `<feature-dir>/ARCH-NN.md` (or `DESIGN-NN.md`, name per `planner-context.md` §5). Sections: (a) Bounded Contexts; (b) Hand-off Contracts; (c) Data Flow; (d) Integration Points; (e) Open Questions; (f) Out of Scope. **This template stays in SKILL.md** — orchestrator and implementer need it on every activation. See template content in §5.4 below. | 80 |
| 6 | `## Design-only rule` | Hard rule, mirrors `planner` boundary style: architect does NOT write code, tests, or migrations. The architecture document may include type signatures and contract pseudocode, but never functional implementation. If a "design decision" requires running code to validate, the architect says so explicitly («needs a spike — implementer to validate, then revisit») rather than writing the spike itself. | 15 |
| 7 | `## Gotchas` | Anthropic best-practice — the «most valuable section». 5-7 real items: (a) Bounded context drift — when 2 contexts repeatedly need the same data, that is a *missing third context*, not "let's share a model"; (b) Premature microservices — splitting into services before the seams are stable produces distributed monoliths, FPF A.11 says don't; (c) Stack-mixed shorthand — describing a feature as "just CRUD" hides the real complexity (auth, cache invalidation, events) — surface it in §c (Data Flow); (d) "Architecture" mistaken for "directory layout" — directories are an output, not the design; (e) Skipping `api-design.md` for "simple" REST — REST contracts have versioning, error shape, idempotency — design them up front; (f) Implementer asking design questions back at runtime → that is a **design defect**, not implementer's job; revise the architecture document. | 30 |
| 8 | `## Integration with other plugins` | **Mandatory section per README §77.** Explicit references with exact namespaces (verified — see §12 Decision 5): (a) `tdd-master:tdd-master` — architect does not invoke this; mention only as: "test strategy decisions live in the design (which boundaries get unit tests, which need integration), but the actual TDD cycle is for code-implementer"; (b) `functional-clarity:functional-clarity` — "Apply Functional Clarity principles. If plugin `functional-clarity` is installed, activate `functional-clarity:functional-clarity` skill for full 22-principle methodology" (verbatim from README §120); (c) `planner:planner` — "the orchestrator dispatches this skill; the architect never invokes the planner back; planner reads `planner-context.md` to know this agent exists"; (d) `document-skills:frontend-design` — "for UI-fidelity (visual quality, design polish), `references/frontend-react.md` mentions activating `document-skills:frontend-design`. If installed, it adds visual design discipline; if not, graceful degrade to universal principles." | 25 |
| 9 | `## When references are missing` | If detected stack has no matching reference (e.g. Go backend, mobile) → SKILL.md falls back to universal design principles + explicit `stack: <detected> — no specific reference, universal principles applied` line in the architecture document's metadata header. **Do not fail.** Do not invent a reference inline. | 10 |
| 10 | `## Reference index` | Bullet list of 3 references with one-line load triggers each. (a) `backend-python.md` — load when project is Python (Django/FastAPI/Flask) and design touches data, ORM, services, or background tasks; (b) `frontend-react.md` — load when project is React/Vue/Svelte and design touches components, state, routing, or rendering boundaries; (c) `api-design.md` — load when the feature exposes or consumes an API (REST, GraphQL, gRPC), regardless of stack. | 15 |

**Total core: ≈245 lines + headers/blank ≈ 280-320 lines. Within budget.**

### §5.3 What does NOT belong in architect/SKILL.md (route to references)

If implementer is tempted to inline these, they go to references instead:

- Django ORM relationship patterns, FastAPI dependency injection, SQLAlchemy session strategy → `references/backend-python.md`.
- React state management decision tree (local / context / Zustand / Redux), component boundary heuristics, SSR vs CSR vs SSG → `references/frontend-react.md`.
- REST resource modeling, OpenAPI spec structure, GraphQL schema design, versioning strategies → `references/api-design.md`.
- Stack-detection table (9 stacks) → already lives in `plugins/planner/skills/planner/references/bootstrap.md` §4 — do not duplicate; reference it.
- Functional Clarity principle bodies → live in `functional-clarity:functional-clarity` skill — do not duplicate; cite the plugin namespace.

### §5.4 Architecture document template (full content for §5.2 row 5)

The template is the body of the fenced ` ```markdown ` block in §5.2 row 5. Verbatim content (implementer copies into SKILL.md):

```markdown
# <FEAT-XXXX> Architecture (ARCH-NN)

> **Source feature:** <path/to/README.md>
> **Stack:** backend-python | frontend-react | mixed | unknown
> **References loaded:** <list>
> **Generated:** <ISO date>

## Bounded contexts
- <context-name>: <one-sentence purpose> — <module/path it lives in>

## Hand-off contracts
| Caller | Callee | Input shape | Output shape | Error mode |
|---|---|---|---|---|

## Data flow
<diagram in ASCII or prose; one paragraph per major flow>

## Integration points
- <external system>: <protocol> — <auth model> — <failure handling>

## Open questions
- <question> → <who decides>

## Out of scope
- <thing that is NOT this feature> (with one-line reason)

## Hand-off
Next agent: `sdlc:code-implementer`
Input: this document + project codebase
TDD: activate `tdd-master:tdd-master` before any production code
```

---

## §6. Skill `architect/references/` — 3 files, design-angle only

Each reference is **design angle only**. No implementation code, no test patterns, no review checklists. If a topic has both design and implement angles, this file covers the design angle only; the matching `code-implementer/references/<same-name>.md` covers the implement angle.

All references live in `plugins/sdlc/skills/architect/references/`. No frontmatter (references load on demand from SKILL.md pointers).

### §6.1 `architect/references/backend-python.md` — design angle

**Purpose:** Python backend design decisions. Loaded by SKILL.md when stack-detection finds Python (Django / FastAPI / Flask / SQLAlchemy / etc.).

**Length budget:** 140-170 lines.

**Section outline:**

| § | Section | Content (design angle only) | Lines |
|---|---|---|---|
| 1 | `## When to load` | One sentence: load when SKILL.md stack-detection finds Python markers. | 3 |
| 2 | `## Framework decision matrix` | Table: framework → when to pick → when to avoid. Rows: Django (full-stack, admin, ORM, batteries), FastAPI (API-first, async, type-driven), Flask (minimal, niche utilities, legacy compat), SQLAlchemy stand-alone (data layer without HTTP framework). Decision rule per FPF A.11: pick the smallest framework that covers the requirements; do not pick FastAPI "because it's modern" if Django answers the same question. | 25 |
| 3 | `## Bounded contexts in Python backends` | Pattern: app boundaries in Django (one app = one bounded context, share via signals/services not direct ORM imports); FastAPI: routers + service layer + repository layer; SQLAlchemy: session-per-request scope. Anti-pattern: cross-app FK chains that hide context coupling. | 25 |
| 4 | `## Data layer design` | ORM design choices: aggregate roots vs anemic models; when to use Django's `prefetch_related` vs `select_related` (design-time decision based on access patterns); FastAPI + SQLAlchemy: repository abstraction or not? Decision: only abstract the repository if you have ≥2 storage backends; otherwise YAGNI (FPF A.11). Migration strategy at design time: forward-only vs reversible — pick before first migration ships. | 30 |
| 5 | `## Async vs sync` | Design-time decision tree: do you have IO-bound concurrency requirements? If yes → FastAPI (async-native); if no → Django (sync-native, `sync_to_async` only at boundaries). Mixed: explicitly note the boundary in the architecture document. | 15 |
| 6 | `## Background tasks design` | Celery vs RQ vs APScheduler vs cloud queues — pick at design time based on (a) durability needs (Celery = durable; APScheduler = in-process), (b) infra constraints. **Design output:** name the queue, name the worker process, name the persistence backend; do NOT design the worker code (that is implement angle). | 20 |
| 7 | `## API surface in Python` | Cross-reference: load `api-design.md` for protocol/contract details. This section covers Python-specific shape: Django REST Framework serializers vs FastAPI Pydantic models vs raw views; the design decision is which abstraction the project commits to (one only — do not mix DRF and FastAPI). | 12 |
| 8 | `## Common design pitfalls` | 5 bullets: (a) putting business logic in views (Django) or routers (FastAPI) instead of services; (b) cross-app raw SQL (Django) — bypasses bounded contexts; (c) global session in SQLAlchemy — race conditions; (d) coupling to ORM model in business logic — locks you to ORM forever; (e) "we'll add caching later" — at minimum, identify cache-bearing endpoints in the design, even if implementation is deferred. | 15 |

**Hard rule:** No code blocks longer than 5 lines (just enough to show shape). No pytest, no factory_boy, no mypy config — those are implement-angle. No N+1 hunt, no n+1 detection — those are review-angle.

### §6.2 `architect/references/frontend-react.md` — design angle

**Purpose:** React (and Vue/Svelte by extension — the principles transfer) frontend design. Loaded when stack-detection finds React/Vue/Svelte.

**Length budget:** 140-170 lines.

**Section outline:**

| § | Section | Content (design angle only) | Lines |
|---|---|---|---|
| 1 | `## When to load` | One sentence trigger. | 3 |
| 2 | `## Framework decision matrix` | React + Vite (SPA), Next.js (SSR/SSG/App-Router), Vue 3 + Vite, SvelteKit, Solid. Decision rule: SSR/SEO requirements → Next.js or SvelteKit; pure dashboard/admin → SPA. | 20 |
| 3 | `## Component boundaries` | Atomic-design vs feature-folder; the design choice is which boundary (component boundary = bounded context boundary); rule: a component owns its state OR receives it via props — never both. | 25 |
| 4 | `## State management decision` | Local state → `useState`; cross-component → React Context (≤3 levels); cross-feature → Zustand / Jotai (lightweight) or Redux Toolkit (large team, strict patterns). Decision rule: pick the simplest tier that solves the problem. Anti-pattern: Redux for 5-component apps. | 25 |
| 5 | `## Data fetching architecture` | TanStack Query (React Query) vs SWR vs hand-rolled fetch hooks vs RSC (Next.js App Router). Design decision: where does the cache live? Where do mutations invalidate? Document this in the architecture, not in components. | 20 |
| 6 | `## Routing architecture` | React Router vs Next.js file-routing vs TanStack Router. Design output: list of routes, auth guards per route, layout boundaries. | 15 |
| 7 | `## Type system at boundaries` | TypeScript at API boundary (codegen from OpenAPI / GraphQL / Zod) vs hand-written; design decision: where types are generated, where hand-written, where they meet. | 12 |
| 8 | `## Integration with `document-skills:frontend-design`` | One-paragraph link: "For UI-fidelity (visual quality, design polish), activate `document-skills:frontend-design`. If installed, it adds visual design discipline (typography, spacing, component composition, taste); if not, graceful degrade to universal principles. The architecture document still names the design system (e.g. shadcn/ui, MUI, custom) and the visual primitives at design time." | 10 |
| 9 | `## Common design pitfalls` | 5 bullets: (a) Redux by default — overkill for most apps; (b) prop-drilling beyond 3 levels — refactor to context or composition; (c) putting fetch in components instead of a data-layer hook — locks rendering to network; (d) ignoring SSR/CSR boundary — hydration mismatches; (e) designing without naming the design system. | 15 |

**Hard rule:** No vitest, no RTL, no hooks implementation patterns — those are implement-angle. No XSS / CSP / accessibility audit — that is review-angle.

### §6.3 `architect/references/api-design.md` — protocol/contract design

**Purpose:** API contract design (stack-agnostic — Python or Node or anything). Loaded when feature exposes or consumes an API.

**Length budget:** 140-170 lines.

**Section outline:**

| § | Section | Content | Lines |
|---|---|---|---|
| 1 | `## When to load` | Load when feature has API surface (REST, GraphQL, gRPC, WebSocket). | 3 |
| 2 | `## Protocol decision matrix` | REST (CRUD-ish, public APIs, simple), GraphQL (client-driven shapes, federated data), gRPC (internal high-throughput, strict contracts), WebSocket (real-time, bidirectional). Decision rule: REST is the default; escalate only with evidence. | 20 |
| 3 | `## REST resource modeling` | Resource = bounded context noun; HTTP verbs map to actions; idempotency rules per verb; URL hierarchy reflects ownership; query params for filtering, headers for cross-cutting (auth, content-type). | 25 |
| 4 | `## OpenAPI / spec-first vs code-first` | Decision: spec-first (write OpenAPI YAML, codegen server stubs and clients) vs code-first (Pydantic / FastAPI generates spec). Rule: spec-first when ≥2 client teams; code-first for internal-only. | 15 |
| 5 | `## Versioning strategy` | URL-prefix (`/v1/`) vs header-based vs media-type. Recommendation: URL-prefix for breaking changes; backward-compatible additions never bump version. Document the deprecation policy at design time. | 18 |
| 6 | `## Error contract` | Problem Details (RFC 7807) vs custom envelope. Decision: pick one and use everywhere. Error shape includes: machine-readable code, human-readable message, optional details, optional `traceId`. | 18 |
| 7 | `## Pagination, filtering, sorting` | Cursor vs offset pagination; filter syntax (RSQL, query-string, JSON body); sort syntax. Pick at design time and document; do not let each endpoint reinvent. | 15 |
| 8 | `## Idempotency and retries` | Which endpoints are idempotent (GET, PUT, DELETE — by HTTP semantics; POST — explicit `Idempotency-Key` header if needed). Document retry-safe vs not in the architecture. | 15 |
| 9 | `## Common design pitfalls` | 5 bullets: (a) verbs in URLs (`/getUserById`) — break REST; (b) inconsistent error shapes — clients write 5 parsers; (c) breaking changes without version bump — silent client breakage; (d) GraphQL by default for tiny CRUD — over-engineering; (e) no contract test plan — backend and frontend drift. | 15 |

---

## §7. Skill `code-implementer` — `plugins/sdlc/skills/code-implementer/SKILL.md`

Hard length budget: **≤500 lines**. Target: **280-340 lines**.

### §7.1 Frontmatter spec

| Field | Value |
|---|---|
| `name` | `code-implementer` |
| `description` | Third-person; ≤900 chars. Template below. |

```
description: >
  This skill should be used when implementing code per an existing
  architecture or PLAN document. Activates when the user asks to
  "implement", "code this up", "build the feature", "add the endpoint",
  "write the component", or in russian «реализуй», «закодь», «добавь
  endpoint», «сделай компонент». Mandates TDD via the
  `tdd-master:tdd-master` skill (RED-GREEN-REFACTOR before any
  production code), enforces minimal changes (FPF A.11), fail-fast
  error handling, and Functional Clarity principles. Loads
  stack-specific references (backend-python or frontend-react) on
  demand. Never designs systems; never reviews others' code.
```

### §7.2 Section outline (full skeleton)

| § | Section | Content / origin | Lines |
|---|---|---|---|
| 1 | `# Code-Implementer — TDD-first implementation` (H1) + 2-sentence purpose | Implements code per a design document. Output: production code + tests + minimal supporting changes. | 5 |
| 2 | `## Principles` | 6 numbered: (1) **TDD-first** — activate `tdd-master:tdd-master` BEFORE writing production code; RED → GREEN → REFACTOR is non-negotiable; (2) **Minimal changes** (FPF A.11) — modify the smallest set of lines that satisfies the test; do not refactor in passing; (3) **Fail-fast** — surface invalid input/state at the boundary, not 5 layers deep; (4) **Evidence over assumption** (FPF A.10) — before claiming "this works the same way" → write a test, run it, look at the result; (5) **Don't change contract without discussion** (`code-change-discipline.md`) — signature/return-type/behavior for callers = breaking change; (6) **Apply Functional Clarity** — if `functional-clarity:functional-clarity` is installed, activate it for the full 22-principle set. | 30 |
| 3 | `## Workflow` | 7-step pipeline: (1) Read input — ARCH/PLAN/README; if missing → fail-fast; (2) Detect stack — same heuristic as architect (reference `bootstrap.md` §4); (3) Activate `tdd-master:tdd-master`; (4) Load stack reference — `references/backend-python.md` or `references/frontend-react.md`; (5) Per task: RED (write failing test) → GREEN (minimum code to pass) → REFACTOR (cleanup, still green); (6) Run full test suite per change set; (7) Hand off — name `sdlc:code-reviewer` and the diff scope. | 30 |
| 4 | `## TDD pointer` | Mandatory reference to `tdd-master:tdd-master`. One paragraph: "For TDD workflow, activate `tdd-master:tdd-master` skill. Use it BEFORE implementing — RED-GREEN-REFACTOR. Do not write production code before a failing test exists. If `tdd-master` is not installed → degrade to universal TDD principles (Kent Beck): write a test that fails for the right reason, write the minimum code to pass, refactor without changing tests." Verbatim wording from README §122. | 12 |
| 5 | `## Minimal-changes rule` | Hard rule: implement the contract from ARCH; do not refactor adjacent code; if adjacent code blocks the implementation, surface that as a `## Open question` in the next architecture iteration — do not silently rewrite. Anti-pattern: "while I was here I also fixed X" — produces unreviewable diffs. Cite `code-change-discipline.md` rule 6 (don't change contract). | 18 |
| 6 | `## Fail-fast rule` | Concrete: validate inputs at function boundary, raise typed exceptions (Python) / throw early (TS), do not return `None`/`null` to signal error if a typed exception is the better tool. Reference Functional Clarity for the full taxonomy. | 15 |
| 7 | `## Stack detection (summary)` | 5-line summary; pointer to `bootstrap.md` §4 master table. Mixed-stack rule: implement backend changes first (so contract is real), then frontend. | 8 |
| 8 | `## Output format — implementation report` | When implementer finishes, emit a chat report with: (a) files changed (path + lines added/removed), (b) tests added (path + test names), (c) commands run (`pytest`, `npm test`), (d) assumptions made (so reviewer can validate), (e) hand-off to `sdlc:code-reviewer`. **Do not write a separate report file** — the chat output is the artifact. | 18 |
| 9 | `## Gotchas` | 6-7 items: (a) writing the test AFTER the code — classic anti-TDD; the test then mirrors the bug; (b) one giant test → no signal on which line failed; tests should be fine-grained; (c) green by mocking everything → tests pass but production breaks; mock at boundaries only; (d) running only the new test and skipping the suite → regression invisible; (e) "I'll write the migration after merging" → migration is part of the change, not after; (f) refactoring during GREEN → only refactor in REFACTOR phase, with the suite green; (g) silently swallowing exceptions to "make it work" → Error Hiding (see `functional-clarity:functional-clarity`). | 30 |
| 10 | `## Integration with other plugins` | (a) `tdd-master:tdd-master` — mandatory, see §4 above; (b) `functional-clarity:functional-clarity` — apply principles, especially Error Hiding prevention and fail-fast; (c) `planner:planner` — orchestrator dispatches this skill; implementer never invokes planner back; if architecture is missing or incoherent, return to planner via the orchestrator (do not invent design); (d) `document-skills:frontend-design` — for React UI-fidelity tasks, see `references/frontend-react.md`. | 25 |
| 11 | `## When references are missing` | Same fallback as architect: universal principles, explicit `stack: <detected> — no specific reference, universal principles applied`. Do not fail. | 8 |
| 12 | `## Reference index` | Bullet list: (a) `backend-python.md` — Python implementation specifics (Django ORM patterns, pytest fixtures, mypy, migrations); (b) `frontend-react.md` — React implementation (vitest + RTL, hooks, async, types). | 10 |

**Total core: ≈209 lines + headers/blank ≈ 280-320 lines.**

### §7.3 What does NOT belong in code-implementer/SKILL.md

- TDD methodology body (RED-GREEN-REFACTOR cycle details, test-first patterns) — lives in `tdd-master:tdd-master`. Cite, do not duplicate.
- Functional Clarity principle bodies — live in `functional-clarity:functional-clarity`. Cite, do not duplicate.
- Django ORM patterns, pytest fixtures, mypy configuration → `references/backend-python.md`.
- vitest, RTL patterns, hooks testing → `references/frontend-react.md`.
- OWASP / security checks → that is review-angle, lives in `code-reviewer/references/security.md` — do not duplicate here.
- Stack-detection table → reference `bootstrap.md` §4.

---

## §8. Skill `code-implementer/references/` — 2 files, implement-angle only

Each file covers the **implement angle** of the same stack name as architect/reviewer references. Same file name, different content.

### §8.1 `code-implementer/references/backend-python.md` — implement angle

**Purpose:** Python implementation patterns. Loaded when stack-detection finds Python.

**Length budget:** 140-170 lines.

**Section outline:**

| § | Section | Content (implement angle only) | Lines |
|---|---|---|---|
| 1 | `## When to load` | Trigger sentence. | 3 |
| 2 | `## Project structure conventions` | Where to put new code per framework: Django (`<app>/models.py`, `<app>/views.py`, `<app>/services.py` if used, `<app>/tests/`); FastAPI (routers/, services/, repositories/, schemas/, tests/); Flask (blueprints/). Rule: follow the project's existing convention; if none → ask, do not impose. | 18 |
| 3 | `## ORM patterns (Django)` | Implement-angle: `select_related` / `prefetch_related` invocation in querysets, `bulk_create`/`bulk_update`, `update_or_create`, `transaction.atomic` blocks at service-layer boundary. Show ≤10-line code shape per pattern. **No design rationale** (that lives in architect reference). | 25 |
| 4 | `## SQLAlchemy patterns` | Session scope (per-request via FastAPI dependency), eager-loading (`selectinload`/`joinedload`), unit-of-work boundary at service layer. ≤10-line code samples. | 20 |
| 5 | `## pytest fixtures` | Implementation patterns: `@pytest.fixture` scope (function/module/session), `pytest-django` `db` fixture, `factory_boy` factories, `pytest-asyncio` for FastAPI. Anti-pattern: shared mutable fixtures across tests. | 25 |
| 6 | `## mypy configuration and patterns` | `pyproject.toml` `[tool.mypy]` recommended config (strict mode at module level, plugin for Django/SQLAlchemy if used). Common patterns: `cast`, `TypedDict`, `Protocol` for duck-typing, `Annotated` for FastAPI. | 18 |
| 7 | `## Migrations` | Django: `makemigrations` → review the SQL → `migrate`; reversible operations only unless documented otherwise; data migrations in separate files (`RunPython` blocks); never edit a migration after it ships. Alembic (SQLAlchemy): autogenerate → review → apply. | 18 |
| 8 | `## Async/sync boundary patterns` | `sync_to_async` and `async_to_sync` use cases; FastAPI: never call sync DB code from an async route without `run_in_executor` or `asyncio.to_thread`. Concrete failure mode: blocking the event loop. | 12 |
| 9 | `## Common implementation pitfalls` | 5 bullets: (a) forgetting `transaction.atomic` for multi-step writes; (b) running tests against shared DB → flaky; use transactional rollback fixture; (c) Django signals as primary control flow → invisible coupling; (d) catching `Exception` to "be safe" → Error Hiding; (e) skipping `mypy` because "tests cover it" — types catch a different class of bugs. | 15 |

**Hard rule:** No design rationale (that is architect-angle). No security audit (that is review-angle). Code samples ≤10 lines, illustrative only.

### §8.2 `code-implementer/references/frontend-react.md` — implement angle

**Purpose:** React implementation patterns. Loaded when stack is React.

**Length budget:** 140-170 lines.

**Section outline:**

| § | Section | Content | Lines |
|---|---|---|---|
| 1 | `## When to load` | Trigger sentence. | 3 |
| 2 | `## Project structure conventions` | feature-folder vs atomic; follow project; if absent, recommend feature-folder. | 12 |
| 3 | `## Component implementation patterns` | Function components only (no class), hooks at top-level, naming (`PascalCase` for components, `useFoo` for hooks). Pure component rule. ≤10-line samples. | 18 |
| 4 | `## Hooks patterns` | `useState` / `useReducer` boundary; `useEffect` cleanup; `useMemo` / `useCallback` only when measured (avoid premature optimization, FPF A.11); custom hooks for cross-component logic (one responsibility per hook). | 25 |
| 5 | `## Data fetching with TanStack Query` | `useQuery` / `useMutation` patterns; key conventions; cache invalidation on mutation; ≤10-line code shape. | 20 |
| 6 | `## TypeScript at component level` | Props typed via interface or type alias; `ReactNode` vs `JSX.Element`; generic components; `as const` for literal unions. | 15 |
| 7 | `## Testing with vitest + React Testing Library` | `describe`/`it` shape; `render` + `screen.getByRole` (accessibility-first queries); `userEvent` over `fireEvent`; mock at network boundary (`msw`), not at component boundary. ≤10-line samples. | 22 |
| 8 | `## Async patterns` | `await waitFor`, `findBy*` queries (auto-await), avoid `act` warnings via proper async/await. | 12 |
| 9 | `## Integration with `document-skills:frontend-design`` | One paragraph: "For UI-fidelity (visual quality, design polish), activate `document-skills:frontend-design`. If installed, it adds visual design discipline; if not, graceful degrade." Verbatim from README §124. | 8 |
| 10 | `## Common implementation pitfalls` | 5 bullets: (a) state in `useEffect` body (re-render loops); (b) missing dependency arrays; (c) testing implementation, not behavior — test what user sees; (d) mocking the component itself (test becomes tautology); (e) `any` type — defeats TypeScript. | 15 |

---

## §9. Skill `code-reviewer` — `plugins/sdlc/skills/code-reviewer/SKILL.md`

Hard length budget: **≤500 lines**. Target: **280-340 lines**.

### §9.1 Frontmatter spec

```
description: >
  This skill should be used when reviewing code changes — security
  issues, system-level defects, FPF/Functional Clarity violations,
  stack-specific pitfalls. Activates when the user asks to "review",
  "check this PR", "is this safe", "find bugs", "code review", or in
  russian «отревью», «проверь код», «есть ли проблемы», «code review».
  Operates on git-diff. Always loads `references/security.md`
  (OWASP Top 10 — non-negotiable). Loads stack-specific references
  (backend-python or frontend-react) on demand. Integrates with
  `functional-clarity:functional-clarity` for Error Hiding and FPF
  checks. Outputs a review report with file:line references; never
  modifies code itself.
```

### §9.2 Section outline (full skeleton)

| § | Section | Content / origin | Lines |
|---|---|---|---|
| 1 | `# Code-Reviewer — system-level + security` (H1) + 2-sentence purpose | Reviews code changes for system-level issues, security, FPF violations. Output: review report; never modifies code. | 5 |
| 2 | `## Principles` | 6 numbered: (1) **System issues over taste** — "I would name this differently" is not a review item; "this name says what it does, but the function does something else" is; (2) **Evidence per finding** (FPF A.10) — every item has `file:line` + reproduction or proof (test that fails, query that 500s); (3) **Security always** — load `references/security.md` even if the diff "looks innocent"; (4) **FPF lens** — apply Functional Clarity (Error Hiding, fail-fast violations, contract changes); (5) **Don't propose implementation** — describe the issue, suggest the direction, let `sdlc:code-implementer` choose the fix; (6) **Operate on git-diff** — review the change set, not the whole codebase; cross-reference for context as needed. | 30 |
| 3 | `## Workflow` | 6-step pipeline: (1) Read input — diff range or PR ref; if missing → fail-fast; (2) Run `git diff <base>..HEAD` (Bash) to get the change set; (3) **Always load** `references/security.md`; (4) Detect stack from changed files (`*.py` → backend-python; `*.tsx`/`*.jsx` → frontend-react); load matching reference(s); (5) Walk the diff with the loaded checklists; (6) Emit review report per output format. | 25 |
| 4 | `## Git-diff approach` | Concrete commands: `git diff <base>..HEAD --stat` (file overview), `git diff <base>..HEAD -- <path>` (file-level), `git log <base>..HEAD --oneline` (commit context). Use `Read` to load full file when context is needed. **Never run `git checkout` or `git reset`** — review-only mode. | 15 |
| 5 | `## OWASP / security framing` | One paragraph: `references/security.md` is the always-active checklist (OWASP Top 10, secrets in code, auth/authz, injection, XSS, CSRF). Even for non-web changes, scan for secrets and credentials. Output: a `Security` section in the report — present even if empty (force-function: "security: no issues found in scope"). | 18 |
| 6 | `## FPF check (Functional Clarity)` | One paragraph: "If `functional-clarity:functional-clarity` is installed, activate it for the full 22-principle methodology. Key checks: Error Hiding (silently swallowed exceptions, default values masking failures), fail-fast violations (validation deep in call stack), contract changes without explicit migration, leaked invariants. If not installed → use the principles cited in this section." Verbatim wording from README §120. | 15 |
| 7 | `## System-issues focus` | List of categories the reviewer prioritizes (over style): n+1 queries, race conditions, transaction boundaries, error swallowing, contract changes, leaked secrets, missing migrations, untested edge cases. Style and naming go to "minor" section of report (or are skipped if a linter handles them). | 20 |
| 8 | `## Output format — review report` | Template for `<feature-dir>/review-request-changes/REVIEW-NN.md` (or chat if no feature dir). Sections: (a) Summary — N major / N minor / N security; (b) Security (always); (c) System issues; (d) FPF / Functional Clarity violations; (e) Stack-specific (per loaded reference); (f) Minor (taste, style — only if not covered by linter); (g) Hand-off to `sdlc:code-implementer` for fixes. Each item: `file:path:line — <issue> — <evidence/repro> — <direction for fix>`. | 35 |
| 9 | `## Gotchas` | 6-7 items: (a) Reviewer rewrites code in their head — describe the issue, not the fix; (b) Style issues drown the report — let the linter own them; (c) "Looks fine" — security still gets a section; (d) Reviewing without the test suite running locally → can't verify reproduction; ask the implementer to confirm; (e) Same finding in 5 places → consolidate into one item with all locations; (f) "I would have designed it differently" → that is a `design concern`, not a defect — fixing requires architect, not implementer; (g) Skipping `references/security.md` because the diff "is just a refactor" → secrets and creds slip in via refactors too. | 30 |
| 10 | `## Integration with other plugins` | (a) `functional-clarity:functional-clarity` — primary co-skill, see §6 above; (b) `tdd-master:tdd-master` — reviewer checks "is there a test for this?"; missing test = review item; reviewer does NOT write the test (that is implementer); (c) `planner:planner` — orchestrator dispatches; reviewer does not invoke planner; (d) `document-skills:frontend-design` — for visual / UX review of frontend changes, mention but do not require — graceful degrade. | 25 |
| 11 | `## When references are missing` | If no stack reference exists → universal principles + explicit "stack: unknown" in the report header. Security reference is **required** — if security.md is missing the implementation is broken; do not silently skip. | 10 |
| 12 | `## Reference index` | (a) `security.md` — **always loaded** (OWASP Top 10, secrets, auth, injection — core security checklist); (b) `backend-python.md` — Django security, n+1, ORM pitfalls, atomic ops (review angle); (c) `frontend-react.md` — XSS, CSP, accessibility, perf, hooks pitfalls (review angle). | 12 |

**Total core: ≈240 lines + headers/blank ≈ 280-320 lines.**

### §9.3 What does NOT belong in code-reviewer/SKILL.md

- OWASP Top 10 details, secret-detection patterns, auth/authz checklist → `references/security.md`.
- Django-specific n+1 detection, ORM pitfalls, atomic ops audit → `references/backend-python.md`.
- React XSS, CSP, accessibility audit, hooks pitfalls → `references/frontend-react.md`.
- Functional Clarity principle bodies → live in `functional-clarity:functional-clarity`.
- Implementation patterns / fixes — reviewer describes the issue; the implementer fixes.

---

## §10. Skill `code-reviewer/references/` — 3 files, review-angle only

### §10.1 `code-reviewer/references/security.md` — always-active

**Purpose:** OWASP Top 10 + secrets + auth + injection checklist. **Always loaded** — per README §69. Reviewer never skips this.

**Length budget:** 160-190 lines (slightly larger than other references — security is non-negotiable, so the checklist is exhaustive within its budget).

**Section outline:**

| § | Section | Content | Lines |
|---|---|---|---|
| 1 | `## When to load` | "Always loaded by the code-reviewer skill, regardless of stack or diff size. This file is non-optional." | 5 |
| 2 | `## OWASP Top 10 (current edition) — review checklist` | 10 categories with one-paragraph review angle each: A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A04 Insecure Design, A05 Security Misconfiguration, A06 Vulnerable Components, A07 Auth Failures, A08 Software/Data Integrity, A09 Logging Failures, A10 SSRF. Per category: what to grep for in diff, common code smells, suggested fix direction. | 60 |
| 3 | `## Secrets and credentials in code` | Patterns to grep: `password\s*=\s*["']`, `api_key`, `Bearer `, hardcoded URLs with creds, AWS keys (`AKIA[0-9A-Z]{16}`), private keys (`-----BEGIN`). Rule: any matching pattern → security item, regardless of "it's just a test fixture". | 20 |
| 4 | `## Authentication & authorization` | Authn: where login lives, password hashing (bcrypt/argon2 — never MD5/SHA1 raw), session handling, JWT pitfalls (algo confusion, no expiry, secret in code). Authz: row-level checks, IDOR (test: change ID in URL, can other user access?), missing decorators (Django `@login_required`, FastAPI `Depends(get_current_user)`). | 30 |
| 5 | `## Injection vectors` | SQL injection (raw SQL with f-strings, `extra()` in Django ORM); template injection (Jinja2 `{% raw %}` from user input); shell injection (`subprocess` with `shell=True` and user input); LDAP / XPath / etc. Each: what to grep, severity, fix direction. | 20 |
| 6 | `## CSRF / CORS / CSP` | CSRF: framework token middleware enabled? exemptions justified? CORS: not `*` for credentialed requests; allowed-origin allowlist explicit. CSP: present? `script-src 'unsafe-inline'`? | 18 |
| 7 | `## Output integration` | One paragraph: every review report has a `## Security` section, even if empty ("no security issues in scope"). Items use `file:line` + OWASP category + evidence + fix direction. | 10 |
| 8 | `## When in doubt — escalate` | Rule: if a finding is plausibly exploitable but the reviewer is uncertain → flag as `security/maybe` with reproduction request. Do not silently skip. | 8 |

### §10.2 `code-reviewer/references/backend-python.md` — review angle

**Purpose:** Python-specific review pitfalls. Loaded when changed files include `*.py`.

**Length budget:** 140-170 lines.

**Section outline:**

| § | Section | Content (review angle only) | Lines |
|---|---|---|---|
| 1 | `## When to load` | Trigger. | 3 |
| 2 | `## Django security specifics` | Beyond OWASP: `mark_safe`, `safe` filter usage in templates (XSS); `raw()` querysets and `extra()` (SQL injection); `DEBUG=True` in prod; `SECRET_KEY` in repo; `ALLOWED_HOSTS = ['*']`; missing `SECURE_*` settings. | 25 |
| 3 | `## n+1 queries` | Detection: loops over `queryset` accessing related FKs without `select_related`/`prefetch_related`; serializer N+1 in DRF nested. Tooling cue: `django-debug-toolbar`, `nplusone` package. Item severity: high if request-scoped, critical for list endpoints. | 20 |
| 4 | `## ORM pitfalls` | `get_or_create` race conditions (no `transaction.atomic`); `update()` skipping `save()` signals when intended; `bulk_create` skipping signals/validators; querying inside templates; `iterator()` exhausted then re-used. | 25 |
| 5 | `## Transaction & atomicity` | Multi-step writes outside `transaction.atomic` → partial state on failure; nested `atomic` with savepoint semantics; `select_for_update` requires atomic. Async: `transaction.atomic` is sync-only; FastAPI/SQLAlchemy uses session unit-of-work. | 20 |
| 6 | `## Error handling and Error Hiding` | `except Exception:` catch-all hiding bugs; `pass` in except blocks; logging an error and returning success; default values that mask missing data. Cross-link: `functional-clarity:functional-clarity` Error Hiding principle. | 15 |
| 7 | `## Type-safety review` | Missing type hints on public APIs; `Any` smuggled in; `# type: ignore` without comment; runtime type assumptions not validated (Pydantic / dataclasses). | 12 |
| 8 | `## Test quality review` | Tests testing the mock, not the system; `assert mock.called` without arg validation; no negative-path tests; flaky tests skipped instead of fixed. | 12 |
| 9 | `## Common review items` | 5 bullets: (a) raw f-string SQL → injection; (b) signals as primary control flow → invisible; (c) global mutable state → race; (d) `print()` left in code; (e) `TODO` without ticket. | 12 |

### §10.3 `code-reviewer/references/frontend-react.md` — review angle

**Purpose:** React-specific review pitfalls. Loaded when changed files include `*.tsx`/`*.jsx`/`*.vue`/`*.svelte`.

**Length budget:** 140-170 lines.

**Section outline:**

| § | Section | Content (review angle only) | Lines |
|---|---|---|---|
| 1 | `## When to load` | Trigger. | 3 |
| 2 | `## XSS in React` | `dangerouslySetInnerHTML` (any usage = review item; require justification); `href={userInput}` (javascript: scheme); `eval`/`Function()` constructed at runtime; user-controlled URLs in `<img>`/`<iframe src>`. | 22 |
| 3 | `## CSP` | If app sets CSP headers, `script-src 'unsafe-inline'` / `'unsafe-eval'` are review items; inline event handlers (`onClick="..."` as string) violate strict CSP. | 12 |
| 4 | `## Accessibility (a11y)` | `<button>` vs `<div onClick>` (use button); `alt` on `<img>`; form labels; focus management on route change; ARIA roles correct (or absent — wrong ARIA worse than no ARIA); color contrast (link to a tool). | 25 |
| 5 | `## Performance pitfalls` | Re-renders: missing `React.memo` for heavy components in lists; new object/function in JSX (`<Foo style={{...}}>`); `useMemo` / `useCallback` overuse (still costs); large bundles from `import *`. | 20 |
| 6 | `## Hooks pitfalls` | `useEffect` with stale closures (missing deps); cleanup missing → memory leak / double-fire; `useState` initial value computed each render (use lazy initializer); custom hook conditionally called → rules-of-hooks violation. | 22 |
| 7 | `## State management review` | Local state mistakenly in Redux (over-engineering); cross-component state in props beyond 3 levels (prop-drilling); state derived from props duplicated as state (sync bugs). | 15 |
| 8 | `## Type-safety review` | `any`/`unknown` without narrowing; `as` casts (audit); missing prop types; `// @ts-ignore`. | 10 |
| 9 | `## Test quality review` | Snapshot tests as the only test (low signal); querying by class/id instead of role/label; missing user-event tests for interaction; mocked the component under test. | 10 |
| 10 | `## Common review items` | 5 bullets: (a) console.log left in; (b) commented-out code; (c) magic numbers (extract to const); (d) missing error boundary; (e) `useEffect` doing data-fetching directly (use TanStack Query). | 12 |

---

## §11. Plugin README — `plugins/sdlc/README.md`

User-facing plugin documentation. Mirrors `plugins/planner/README.md` and `plugins/llms-keeper/README.md` style.

**Length budget:** 130-180 lines (slightly larger than planner README — migration guide is more detailed because 3 legacy agents must be removed and a name collision must be resolved).

**Section outline:**

| § | Heading | Content directive | Lines |
|---|---|---|---|
| 1 | `# sdlc` | H1, plugin name. | 1 |
| 2 | One-paragraph intro | What the plugin replaces (legacy `~/.claude/agents/python-implementer.md`, `django-architect.md`, `code-reviewer.md`) and what it adds (3 stack-aware agents, namespaced, distributable, integrates with `tdd-master` + `functional-clarity` + `planner` instead of duplicating). | 8 |
| 3 | `## What it does` | Bullet list, 6-8 items: 3 agents (architect / code-implementer / code-reviewer); stack-aware via on-demand references (backend-python, frontend-react, api-design, security); TDD enforced via `tdd-master:tdd-master`; FPF enforced via `functional-clarity:functional-clarity`; visual design via `document-skills:frontend-design` graceful integration; works under `/plan-do` (planner orchestrates the pipeline). | 12 |
| 4 | `## Structure` | Code-fenced directory tree (mirroring §1 of this plan). | 25 |
| 5 | `## Installation` | Per-marketplace install instructions citing `i-m-senior-developer`. Two-line version: add marketplace, install plugin. Match `planner/README.md` style. | 8 |
| 6 | `## Migration from legacy agents` | **Detailed migration block.** Includes: (1) backup-before-delete step ("check for local modifications"); (2) the 3 `rm -f` commands; (3) name-collision resolution for `code-reviewer`; (4) `planner-context.md` update (manual or via `/plan-reflect`); (5) verification with `/help` showing `(plugin:sdlc)` next to agents. **Exact content in §11.1 below.** | 45 |
| 7 | `## Agents` | Bullet list of the 3 agents with one-line role + namespaced name: `sdlc:architect`, `sdlc:code-implementer`, `sdlc:code-reviewer`. | 8 |
| 8 | `## Skills` | Bullet list of the 3 skills with what they activate on. Mirror agent names. | 8 |
| 9 | `## Integration with other plugins` | Bulleted: `tdd-master`, `functional-clarity`, `planner`, `document-skills:frontend-design`. One sentence each, copied from cross-plugin section of feature README §117-125. | 15 |
| 10 | `## Examples` | 3 short usage examples: (a) architect from feature README; (b) code-implementer for backend-python; (c) code-reviewer with security focus. ~3 lines each. | 12 |
| 11 | `## Requirements` | Claude Code with marketplaces; recommended companions: `tdd-master`, `functional-clarity`, `planner` (sdlc works without them but with reduced features). | 8 |
| 12 | `## Versioning` | One paragraph: this plugin starts at `0.1.0`. Any change to any file in `plugins/sdlc/` requires a semver bump in `plugin.json` per CLAUDE.md repo rule. | 6 |

### §11.1 Migration content (exact — implementer copies verbatim into §6 of plugin README)

```bash
# 1. BACKUP first — check for local modifications you want to preserve
#    (custom triggers, project-specific tweaks, lessons-learned notes)
diff -q ~/.claude/agents/python-implementer.md /dev/null 2>&1 && \
  cp ~/.claude/agents/python-implementer.md ~/.claude/agents/python-implementer.md.backup
diff -q ~/.claude/agents/django-architect.md /dev/null 2>&1 && \
  cp ~/.claude/agents/django-architect.md ~/.claude/agents/django-architect.md.backup
diff -q ~/.claude/agents/code-reviewer.md /dev/null 2>&1 && \
  cp ~/.claude/agents/code-reviewer.md ~/.claude/agents/code-reviewer.md.backup

# 2. Install plugin from marketplace
#    (after publication: claude plugin install i-m-senior-developer/sdlc)

# 3. Remove legacy agents
rm -f ~/.claude/agents/python-implementer.md
rm -f ~/.claude/agents/django-architect.md
rm -f ~/.claude/agents/code-reviewer.md

# 4. Verify the namespace collision is resolved
#    `code-reviewer` exists as `sdlc:code-reviewer` after step 3.
#    Run `/help` and confirm the agents show `(plugin:sdlc)` label.

# 5. Update each project's planner-context.md §1
#    Option A (manual): replace rows for python-implementer / django-architect / code-reviewer
#                       with sdlc:architect / sdlc:code-implementer / sdlc:code-reviewer.
#    Option B (automatic): run `/plan-reflect` in a session with PLANNER_OUTPUT.md present
#                          — the planner-reflect skill detects the catalog change and
#                          appends auto-added rows. Manual-edit cells are preserved
#                          (per planner FEAT-0001 re-scan rules).

# 6. Smoke test
#    Run `/plan-do features/<any-feature>/README.md` — all 3 phases should dispatch
#    sdlc:architect → sdlc:code-implementer → sdlc:code-reviewer.

# 7. Cleanup backups (after verification — at least one full session)
rm -f ~/.claude/agents/*.backup
```

**Sanity-check bullets following the bash block:**

- Confirm `~/.claude/agents/python-implementer.md` is gone.
- Confirm `~/.claude/agents/django-architect.md` is gone.
- Confirm `~/.claude/agents/code-reviewer.md` is gone.
- Confirm `/help` shows `(plugin:sdlc)` label next to architect, code-implementer, code-reviewer.
- Confirm in any project's `planner-context.md` §1 the new rows exist (or the old rows are tagged `<!-- stale, last seen YYYY-MM-DD -->` after `/plan-reflect`).

---

## §12. Decisions (resolves README Open Questions §163-169)

### Decision 1 — Frontmatter `description` tone (READme §165)

**Decision:** Third-person present tense for **all** skill `description` fields. Russian triggers preserved verbatim from feature README. English trigger phrases are gerund-leaning where natural ("designing", "implementing", "reviewing") but the sentence subject is third-person ("This skill should be used when..."), not first-person ("I will...").

**Rationale (FPF A.7 — strict distinction between role and self):** The skill description is a **role contract** read by the harness — it answers "should this skill be activated?". A first-person description ("I will...") leaks the agent's voice into the catalog metadata, which is a category error: the description is a router rule, not a soliloquy. Third-person is the Anthropic best-practice (cited in README §165) and matches all sibling skills (`planner/SKILL.md`, `tdd-master/SKILL.md`, `functional-clarity/SKILL.md`).

**Exact templates:** §5.1, §7.1, §9.1 above.

### Decision 2 — Shared content across `references/backend-python.md` in 3 skills (README §166; planner risk §5.1)

**Decision:** **Same file name in 3 skills, different content per angle.** No `sdlc-common` plugin, no shared/. Explicit angle assignment:

- `architect/references/backend-python.md` — **design angle only**. Framework choice, bounded contexts, data layer design, async/sync boundary. No code longer than 5 lines (only contract shapes). No tests, no review checks.
- `code-implementer/references/backend-python.md` — **implement angle only**. ORM patterns at code level, pytest fixtures, mypy config, migrations as commands. Code samples ≤10 lines, illustrative. No design rationale, no security audit.
- `code-reviewer/references/backend-python.md` — **review angle only**. n+1 detection, ORM pitfalls, transaction boundaries, Error Hiding patterns. No "how to write it" — only "what to flag".

The same rule applies to `frontend-react.md` (3 angles) and would apply to any future stack reference.

**Rationale (FPF A.10 — bounded context):** Each skill operates in a different bounded context (design / implement / review). The same word "n+1 query" means different things in each context: in architect it's a *design seam* (where the access pattern lives); in implementer it's a *queryset choice* (which method to call); in reviewer it's a *pattern to grep for*. Forcing them into one shared file collapses the boundaries and the file becomes useless to all three.

**Rationale (FPF A.11 — parsimony):** Adding a `sdlc-common` plugin solves a duplication that does not exist (the angles are different), at the cost of a new plugin to maintain, a new namespace, and indirection on every load. The minimal solution is to discipline the angle per file. Implementers MUST verify, when writing each file, that the content is angle-specific — content overlap is a defect.

**Future re-evaluation criterion:** If, after 3+ stacks ship and 6+ months of usage, the same paragraph appears verbatim in ≥3 angle files (true duplication, not angle-bleeding), revisit the `sdlc-common` plugin question. Until then, keep things simple.

### Decision 3 — Hooks (README §167)

**Decision:** No `hooks/` directory in v0.1.0. Skills auto-activate via `description` triggers; the orchestrator (`/plan-do` from `planner` plugin) drives agent dispatch. No `session-start.sh` or `hooks.json` ships.

**Rationale (FPF A.11 — parsimony):** Hooks are a mechanism for actions outside the LLM's autonomous control (file scanning before tool use, blocking dangerous commands). The `sdlc` plugin's job is design / implement / review — all of these are LLM-driven and triggered by user intent or orchestrator dispatch. There is no event-loop reason to add hooks. Adding an empty `hooks/README.md` placeholder is cargo-culting from `planner` (where the placeholder documents a future opt-in `SessionEnd` reflect hook with a real use case). `sdlc` has no analogous future use case in scope.

**Future re-evaluation criterion:** If a project routinely needs to block sdlc agent activation under certain conditions (e.g. "do not let `code-implementer` write to `migrations/` without explicit approval"), revisit hooks then with a concrete trigger.

### Decision 4 — DevOps and Mobile out of scope (README §168-169)

**Decision:** No DevOps (Dockerfile, terraform, CI/CD) and no Mobile (Android, iOS, React Native, Flutter) references in v0.1.0. Out of scope. Pointers:

- DevOps → future plugin `sdlc-infra` (FEAT-0003 backlog, per README §168).
- Mobile → future plugin `sdlc-mobile` (FEAT-0004 backlog, per README §169).

**Rationale (FPF A.11):** Each new stack adds 3 references (architect / implement / review angles). Shipping 4 stacks in v0.1.0 (backend-python, frontend-react, infra, mobile) means 12 references to author and maintain — a 4× increase that does not match the demonstrated demand (legacy agents covered Python and review only). Ship the 2 demonstrated stacks; let evidence drive the next addition.

**Stack-detection compatibility:** The fallback path (§5.2 row 9, §7.2 row 11, §9.2 row 11) ensures the skills do not fail on unknown stacks — they degrade to universal principles and explicitly note the stack as `unknown` in output. Mobile and infra projects therefore work with reduced features rather than crashing.

### Decision 5 — Skill naming convention (README §80)

**Decision:** Noun-form skill names: `architect`, `code-implementer`, `code-reviewer`. Already settled in feature README §80; this section records the FPF reasoning for the contract.

**Rationale (FPF A.7 — naming reflects role, not action):** Anthropic's general guidance leans gerund (`writing-code`, `reviewing-pull-requests`), but the feature README §80 explicitly overrides for this plugin: agents/skills inside this plugin are namespaced (`sdlc:architect`), and `sdlc:writing-architecture` is awkward in a sentence ("the orchestrator dispatches `sdlc:writing-architecture`" reads like the plugin is mid-sentence). Noun-form (`sdlc:architect`) reads as a role, which is what the entity *is* in the dispatch graph. The override is justified by readability in the namespaced context — gerund-form is the default for unnamespaced skills, but inside a plugin the role-noun is clearer.

**Cross-plugin namespace verification (resolves blocker check from prompt §10):** Verified by reading actual `plugin.json` files of sibling plugins:

- `tdd-master:tdd-master` — confirmed (`plugins/tdd-master/.claude-plugin/plugin.json` `name: tdd-master`; skill folder `plugins/tdd-master/skills/tdd-master/`).
- `functional-clarity:functional-clarity` — confirmed (`plugins/functional-clarity/.claude-plugin/plugin.json` `name: functional-clarity`; skill folder `plugins/functional-clarity/skills/functional-clarity/`).
- `document-skills:frontend-design` — built-in plugin; trusted per feature README §123 + §10 of this prompt's instruction set; namespace pattern `<plugin>:<skill>` matches the verified examples; no further verification possible without accessing built-in plugins source.

These exact namespaces are the contract. Implementers must use them verbatim — no abbreviations, no aliases.

---

## §13. Implementation Stages (mirrors PLANNER_OUTPUT.md Phase 2a/2b/2c, with file-level assignments)

**Phase 1 (this document) — already running:** architect (opus) produces this contract. Output: `features/FEAT-0002-sdlc-plugin/FEAT-0002-PLAN-01.md`.

**Phase 2a — Parallel skill groups (3 agents, sonnet, independent):** each agent owns one skill group (SKILL.md + its references). Groups are independent because skills do not reference each other's internals.

| Slot | Agent | Files owned (by absolute path) | Spec sections |
|------|-------|--------------------------------|---------------|
| 2a-1 | sonnet (general-purpose) | `plugins/sdlc/skills/architect/SKILL.md`, `plugins/sdlc/skills/architect/references/backend-python.md`, `plugins/sdlc/skills/architect/references/frontend-react.md`, `plugins/sdlc/skills/architect/references/api-design.md` | §5, §6.1, §6.2, §6.3 |
| 2a-2 | sonnet (general-purpose) | `plugins/sdlc/skills/code-implementer/SKILL.md`, `plugins/sdlc/skills/code-implementer/references/backend-python.md`, `plugins/sdlc/skills/code-implementer/references/frontend-react.md` | §7, §8.1, §8.2 |
| 2a-3 | sonnet (general-purpose) | `plugins/sdlc/skills/code-reviewer/SKILL.md`, `plugins/sdlc/skills/code-reviewer/references/security.md`, `plugins/sdlc/skills/code-reviewer/references/backend-python.md`, `plugins/sdlc/skills/code-reviewer/references/frontend-react.md` | §9, §10.1, §10.2, §10.3 |

**Phase 2b — Plugin meta (1 agent, sonnet, parallel with 2a):**

| Slot | Agent | Files owned | Spec sections |
|------|-------|-------------|---------------|
| 2b-1 | sonnet (general-purpose) | `plugins/sdlc/.claude-plugin/plugin.json`, `plugins/sdlc/README.md`, edit to `.claude-plugin/marketplace.json` | §2, §3, §11 |

**Phase 2c — Agent wrappers (1 agent, sonnet, depends on Phase 2a — needs skill names confirmed by file existence):**

| Slot | Agent | Files owned | Spec sections |
|------|-------|-------------|---------------|
| 2c-1 | sonnet (general-purpose) | `plugins/sdlc/agents/architect.md`, `plugins/sdlc/agents/code-implementer.md`, `plugins/sdlc/agents/code-reviewer.md` | §4.1, §4.2, §4.3 |

**No file is owned by 2 agents.** Verify ownership against §1 directory tree — all 15 files map to exactly one slot (3 to 2a-1, 3 to 2a-2, 4 to 2a-3, 3 to 2b-1, 3 to 2c-1 = 16, minus marketplace.json which is an edit not a create = 15 creates + 1 edit; the edit belongs to 2b-1).

**Phase 3 — Review (serial, after 2a + 2b + 2c):** `code-reviewer` (opus) — consistency check across all 15 files: skill boundaries, reference depth (≤1 level, ≤500 lines per SKILL.md, ≤170 lines per reference [security.md ≤190]), cross-plugin integration wording (exact namespaces from §12 Decision 5), migration steps accuracy (§11.1), version `0.1.0` in plugin.json. Output: review report + go/no-go for marketplace publication.

**Parallelization diagram:**

```
[serial]  Phase 1 (architect, opus) — this document
             |
     ┌───────┼────────┐
     |       |        |
[parallel] 2a-1   [parallel] 2a-2   [parallel] 2a-3   [parallel] 2b-1
     |       |        |             |
     └───────┴────────┴─────────────┘
                      |
              [serial] 2c-1 (depends on 2a-* skill files existing)
                      |
              [serial] Phase 3 — review (opus)
```

Concurrency: 4 agents in parallel during 2a + 2b (within LIFT-COT limit of 7).

---

## §14. Acceptance Checklist

Maps each "Must Have" line from feature README §57-73 + "Polish" §76-82 to a concrete artifact. All boxes must be addressable to call FEAT-0002 done.

**Must Have (README §57-73):**

- [ ] **§57** `plugins/sdlc/.claude-plugin/plugin.json` with `name`, `version: 0.1.0`, `description`, `author`, `keywords` → §2 of this plan.
- [ ] **§58** `plugins/sdlc/agents/architect.md` thin wrapper, frontmatter `name`/`description`/`model: opus`/`tools` → §4.1.
- [ ] **§59** `plugins/sdlc/agents/code-implementer.md` thin wrapper, `model: sonnet` → §4.2.
- [ ] **§60** `plugins/sdlc/agents/code-reviewer.md` thin wrapper, `model: sonnet` → §4.3.
- [ ] **§61** `plugins/sdlc/skills/architect/SKILL.md` design-only core ≤500 lines, target 280-340 → §5.
- [ ] **§62** `plugins/sdlc/skills/architect/references/backend-python.md` design angle, 140-170 lines → §6.1.
- [ ] **§63** `plugins/sdlc/skills/architect/references/frontend-react.md` design angle, 140-170 lines → §6.2.
- [ ] **§64** `plugins/sdlc/skills/architect/references/api-design.md` REST/GraphQL/OpenAPI, 140-170 lines → §6.3.
- [ ] **§65** `plugins/sdlc/skills/code-implementer/SKILL.md` implement core, TDD pointer to `tdd-master:tdd-master`, 280-340 lines → §7.
- [ ] **§66** `plugins/sdlc/skills/code-implementer/references/backend-python.md` implement angle, 140-170 lines → §8.1.
- [ ] **§67** `plugins/sdlc/skills/code-implementer/references/frontend-react.md` implement angle, 140-170 lines → §8.2.
- [ ] **§68** `plugins/sdlc/skills/code-reviewer/SKILL.md` review core, OWASP+FPF+git-diff, 280-340 lines → §9.
- [ ] **§69** `plugins/sdlc/skills/code-reviewer/references/security.md` always-active, OWASP Top 10, 160-190 lines → §10.1.
- [ ] **§70** `plugins/sdlc/skills/code-reviewer/references/backend-python.md` review angle, 140-170 lines → §10.2.
- [ ] **§71** `plugins/sdlc/skills/code-reviewer/references/frontend-react.md` review angle, 140-170 lines → §10.3.
- [ ] **§72** `plugins/sdlc/README.md` description + install + migration guide, 130-180 lines → §11 (with §11.1 verbatim migration block).
- [ ] **§73** Marketplace entry appended to `i-m-senior-developer/.claude-plugin/marketplace.json` → §3.

**Polish (README §76-82):**

- [ ] **§76** Each SKILL.md has a `## Gotchas` section with 5-7 real items → §5.2 row 7, §7.2 row 9, §9.2 row 9.
- [ ] **§77** Each SKILL.md has `## Integration with other plugins` referencing `tdd-master:tdd-master`, `functional-clarity:functional-clarity`, `planner:planner`, `document-skills:frontend-design` → §5.2 row 8, §7.2 row 10, §9.2 row 10.
- [ ] **§78** Each SKILL.md ≤500 lines → length budgets in §5, §7, §9.
- [ ] **§79** All references at depth 1 from SKILL.md (no nested references) → §1 directory tree confirms.
- [ ] **§80** Skill names noun-form: `architect`, `code-implementer`, `code-reviewer` → §1, §12 Decision 5.
- [ ] **§81** Forward-slash paths in references → implementer convention.
- [ ] **§82** "Execute or Read?" framing — references contain content to read, not execute → §6, §8, §10 are read-only knowledge files.

**Cross-plugin link verification (must literally appear in the named files):**

- [ ] `tdd-master:tdd-master` cited in `code-implementer/SKILL.md` §4 (TDD pointer) and §10 (Integration).
- [ ] `tdd-master:tdd-master` cited in `code-reviewer/SKILL.md` §10 (test-presence check).
- [ ] `functional-clarity:functional-clarity` cited in all 3 SKILL.md `## Integration with other plugins` sections.
- [ ] `functional-clarity:functional-clarity` cited in `code-reviewer/SKILL.md` §6 (FPF check).
- [ ] `document-skills:frontend-design` cited in `architect/references/frontend-react.md` §8 and `code-implementer/references/frontend-react.md` §9.
- [ ] `planner:planner` cited in all 3 SKILL.md `## Integration with other plugins` sections.

**Migration steps (§11.1):**

- [ ] Backup-before-delete step present (FPF A.10 — evidence-preserving rollback).
- [ ] 3 `rm -f` commands (`python-implementer`, `django-architect`, `code-reviewer`).
- [ ] Name-collision resolution for `code-reviewer` documented (`sdlc:code-reviewer`).
- [ ] `planner-context.md §1` update — both manual (Option A) and automatic via `/plan-reflect` (Option B) paths documented.
- [ ] Verification step (`/help` shows `(plugin:sdlc)` label).
- [ ] Cleanup-backups step at the end (after at least one full session).

**Edge-case coverage (README §41-52):**

- [ ] Stack not detected → SKILL.md fallback (§5.2 row 9, §7.2 row 11, §9.2 row 11).
- [ ] Mixed stack → architect SKILL.md §4 mixed-stack rule; implementer §7.2 row 7 mixed-stack rule.
- [ ] No README/ARCH input → fail-fast in workflow §1 of each SKILL.md.
- [ ] Reference for rare stack missing → SKILL.md fallback noting `stack: <detected> — universal principles applied`.
- [ ] FC duplication avoided → all 3 SKILL.md cite `functional-clarity:functional-clarity` instead of duplicating.
- [ ] Legacy `python-implementer.md` etc. → migration guide §11.1.
- [ ] `code-reviewer` name collision → migration guide §11.1 step 4.
- [ ] SKILL.md length cap → §5, §7, §9 budgets ≤500 lines.
- [ ] `document-skills:frontend-design` not installed → graceful degrade noted in `architect/references/frontend-react.md` §8.

**Semver compliance (CLAUDE.md mandate):**

- [ ] `plugins/sdlc/.claude-plugin/plugin.json` ships at `version: 0.1.0`.
- [ ] `plugins/sdlc/README.md` §12 documents the semver-bump rule for any future change.

---

**End of FEAT-0002-PLAN-01.**

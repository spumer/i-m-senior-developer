# Mode 2 — Execution planning

Detailed mechanics for the execution-planning mode of the planner skill. `SKILL.md` ("Mode 2 — execution planning") routes here when the input is an existing architecture document and the question is **how to execute it cheaper / faster / more reliably than a naive `/plan-do`**.

## 1. When to load

Load this reference when the planner is invoked with an existing architecture artifact as input — `*-PLAN-*.md`, `*-DESIGN-*.md`, `ARCHITECTURE.md`, or any equivalent document the project produced during the architecture phase. If the input is a feature `README.md` and no architecture exists yet, load `architecture-mode.md` instead.

## 2. Inputs and exit criterion

- **Input:** the architecture file (path inferred from `planner-context.md` §5 + the feature directory).
- **Exit:** an updated or freshly created `<feature-dir>/PLANNER_OUTPUT.md` describing the execution phases (who runs what, on which model, in which order).

If `PLANNER_OUTPUT.md` already exists from a prior architecture-mode run, the execution-mode pass appends / replaces the "Execution plan" section, leaving the "Task summary" and "Mode" header consistent.

## 3. Dependency graph construction

The architecture document lists stages or work blocks; execution mode turns them into a DAG so independent stages can run in parallel.

1. **Extract stages.** Walk the architecture document. Each top-level stage / phase / block (typically an H2 or H3 in `*-PLAN-*.md`) is one stage candidate. Capture the stage's id (header text), purpose (one sentence), and the files / modules it touches.
2. **List prerequisites per stage.** For each stage, enumerate which other stages must complete first. Prerequisites are concrete: "stage B writes `models.py` which stage C imports" → C depends on B. Do not invent dependencies you cannot point to.
3. **Topo-sort.** Order the stages so every stage's prerequisites precede it. The result is the input to §4 (parallel-phase grouping).

**Strict-serial rule** (from legacy `~/.claude/agents/planner.md` lines 200-201): if the work crosses the persistence boundary, the order is **migrations → models → views → frontend**. Do not parallelize across this boundary even if the topo-sort would technically allow it; downstream stages depend on the data shape decisions made upstream, and parallelism here produces churn, not speed.

## 4. Parallel phase grouping

Group independent stages (no path between them in the dependency graph) into a single "phase". A phase is a set of stages that run concurrently.

**Hard cap: 7 agents per phase.** This is the LIFT-COT integration cap from legacy line 284-285 — beyond 7 concurrent agents the integration / merge cost exceeds the parallelism savings, and review fidelity drops. Sub-caps by phase kind (also from legacy line 284-285):

- **Planning-phase ≤ 6** — when the phase consists of agents producing planning artifacts (sub-plans, sub-designs).
- **Validation-phase ≤ 7** — when the phase consists of reviewers / linters / test-runners.
- **Integration-phase ≤ 4** — when the phase consists of agents merging or reconciling outputs from prior phases.

If a topo-sort group exceeds the cap, split it into two sequential phases of equal-ish size. Prefer splitting along natural domain lines (e.g. backend stages in one phase, frontend stages in the next) rather than arbitrary halves.

## 5. Model selection table

The model table below is the **master** table — it ships with the plugin and is the default for any project. Each project may override or extend it in `planner-context.md` §4 (legacy lines 146-152, reused verbatim):

| Модель | Сила | Слабость | $/time | Применять для |
|---|---|---|---|---|
| Opus 4.7 | Глубокие рассуждения, сложная архитектура, нестандартные алгоритмы | Дорого, медленно | ≈5× Sonnet | Security-core, новая незнакомая область, спорные ADR |
| Sonnet 4.6 | Баланс: контекст + надёжный код | Теряется в очень сложных цепочках | baseline | 80% задач: CRUD, компоненты, миграции, обычная архитектура |
| Haiku 4.5 | Быстрый, дешёвый | Слабее на нюансах | ≈0.2× Sonnet | Тривиальные правки, форматирование, проверка импортов |

When picking a model for a stage, read the project's local override first (`planner-context.md` §4), then fall back to this default. Project-local lessons-learned written by `/plan-reflect` (e.g. "for tasks of type X on this project, Sonnet was weak → try Opus") live in §4 of `planner-context.md` and take precedence over this default.

## 6. Code-review placement

From legacy lines 203-205. Two patterns, choose by feature criticality:

- **Review after every phase** — for security-sensitive work, core data-model changes, or any feature flagged `criticality: security | data-migration | breaking-API`. The cost of catching a defect late on these paths dwarfs the cost of an extra review pass.
- **Review once at the end** — for small edits, doc-only changes, cosmetic refactors. One reviewer at the end is enough; per-phase review here would be overhead with no benefit.

The decision is recorded in the `PLANNER_OUTPUT.md` "Risks & human-in-the-loop gates" section.

## 7. Agent-name resolution

From legacy lines 206-210, with one expansion for the gap-fallback hook:

- Agent names in the execution plan come **only** from `planner-context.md` §1. Do not invent names; the orchestrator can only dispatch what exists.
- If a needed role has no matching agent in §1, write the role kind in the plan as `<role-kind>` (e.g. `<frontend-architect>`, `<security-reviewer>`) and add the line: *"mapping per `planner-context.md` §1; if no agent in catalog, orchestrator falls back to general-purpose Task tool"*.
- This is the hook that makes a `❌ GAP` flag in `planner-context.md` actually visible to the orchestrator at execution time. Without this line, the orchestrator would either guess (wrong) or silently DIY (the fail-mode this whole feature was designed to fix — see FEAT-0001 README Problem Statement).

## 8. Output mapping

Each topo-sorted phase fills one "Phase X" block in `PLANNER_OUTPUT.md` per the template in `SKILL.md` ("Output format"). Concretely:

- **Phase header**: `### Phase N — <name> (parallel | serial)`. Tag `parallel` when the phase contains multiple agents grouped per §4. Tag `serial, depends on Phase N-1` when the phase has one agent or strict ordering.
- **Agent lines** inside the phase: one per stage, each with model, skills, focus, inputs, outputs, est. tokens, est. wall-clock.
- **Cost estimate** row: must compare a naive `/plan-do` baseline (sequential, all-Sonnet) against the optimized plan, with a one-sentence justification of the savings ("two parallel Sonnet phases instead of four serial ones reduces wall-clock by ~50% with no token-cost delta") or, if no savings exist, an explicit "naive `/plan-do` is optimal — no planner overhead worth incurring".
- **Risks & gates** section: list each `❌ GAP` fallback the plan triggers, plus any review gates from §6.

If the optimization shows no win versus naive — the planner says so explicitly. The "always emit something" force-function (legacy line 272-274) is critical: a plan that recommends "skip the planner, run `/plan-do`" is a valid output, not a failure.

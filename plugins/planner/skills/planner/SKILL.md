---
name: planner
description: >
  This skill should be used when the user asks to "plan a task",
  "build an execution plan", "split this work", "make this faster/cheaper",
  or in russian «план», «разбей задачу», «распредели»,
  «оптимизируй процесс», «как сделать быстрее/дешевле».
  Also activates when a feature README is presented before /plan-do,
  when an architecture session is starting, or when an existing PLAN
  document is about to be executed.
  Provides two modes: architecture planning (from a feature README)
  and execution planning (from an architecture document).
---

# Planner — meta-dispatcher

Designs **how** other agents should execute a task: which agents to call, on which model (Opus / Sonnet / Haiku), which skills to activate, what can run in parallel. The planner does not write code and does not run agents itself — it produces a plan; the orchestrator dispatches.

The single artifact of a planner activation is a `PLANNER_OUTPUT.md` file (or, if no feature directory exists, the same content emitted to chat). The exception: on first run in a project, the planner also writes `<project-root>/.claude/planner-context.md` via the bootstrap procedure described in the Bootstrap pointer section below.

## Principles

1. **План, а не работа.** Планнер не читает код ради исправлений — только ради оценки объёма и типа задачи. Exit-criterion работы — валидный `PLANNER_OUTPUT.md` (или вывод в чат, если нет директории фичи).
2. **Рентабельность.** Каждый план должен быть либо быстрее, либо дешевле, либо надёжнее naive-подхода `/plan-do`. Если оптимизировать нечего — так и напиши: «naive-подход оптимален, planner overhead не оправдан».
3. **Evidence, не догадки (FPF A.10).** Размер задачи оцениваешь по артефактам: количеству файлов в README, затрагиваемым модулям (grep), длине существующих PLAN-документов. Не придумывай цифры.
4. **Минимальная достаточность (FPF A.11).** Не предлагай параллелизм ради параллелизма. Если задача — один файл на 30 строк, один agent достаточен.
5. **Fail-fast на входе.** Если контекст неполон (нет README, нет ARCH-плана в execution-режиме) — явно напиши, чего не хватает, и не строй план на догадках.
6. **Bounded context (FPF A.1.1).** Глобальная логика планнера — универсальна. Проектная специфика (имена агентов, пути фич, соглашения) живёт в `planner-context.md` проекта. Не хардкодь проектные данные в выводе.

## Workflow

The four-step pipeline below runs on every planner activation. Steps 1 and 4 always execute; steps 2-3 branch on input type.

1. **Check `planner-context.md`.** Read `<project-root>/.claude/planner-context.md`. If the file is missing, stale, or the user explicitly asks for a re-scan, follow `references/bootstrap.md` to populate it, then return here.
2. **Classify the task.** Decide mode by inspecting the input: a feature `README.md` → architecture mode; an existing architecture document (`*-PLAN-*.md`, `*-DESIGN-*.md`, `ARCHITECTURE.md`) → execution mode; free text with no path → architecture mode with chat output.
3. **Load the matching reference.** Architecture mode → `references/architecture-mode.md`. Execution mode → `references/execution-mode.md`. Do not load both; the chosen reference carries the option matrix and decision rules for that mode.
4. **Emit `PLANNER_OUTPUT.md`.** Write to `<feature-dir>/PLANNER_OUTPUT.md` if a feature directory exists; otherwise output the plan to chat. Use the template in the Output format section below.

## Bootstrap pointer

If `<project-root>/.claude/planner-context.md` is missing, stale, or the user explicitly asks for a re-scan, follow `references/bootstrap.md`. Do not inline bootstrap logic here — bootstrap runs once per project, and inlining its details (the scanning algorithm, the stack→signal heuristic table, the gap-detection format) would bloat context on every planner activation that does not need them.

The canonical empty-shell template that bootstrap writes lives at `references/template-context.md`. After bootstrap completes, `planner-context.md` becomes the project source of truth — manual edits inside it are honored on every subsequent run (re-scan only appends rows tagged `<!-- auto-added ... -->` and never overwrites cells the user touched).

## Mode 1 — architecture planning (summary)

Input: a feature `README.md`. Question: how to run the architecture phase efficiently? Pick one of four options — single Opus architect (monolithic feature), N parallel Sonnet sub-architects (weakly coupled domains, N ≤ 4), single Haiku quick-pass (<200 LOC impact, single module, no migrations), or add a separate security sub-plan (when auth / authz / PII is in scope). Default is single Sonnet architect; escalate or split only with evidence. Full option matrix, decision rules, and pitfalls live in `references/architecture-mode.md`.

## Mode 2 — execution planning (summary)

Input: an existing architecture document (`*-PLAN-*.md`, `*-DESIGN-*.md`, `ARCHITECTURE.md`, etc.). Question: how to execute the plan cheaper / faster / more reliably than naive `/plan-do`? Build a dependency graph of stages, group independent stages into parallel phases (≤ 7 agents per phase per LIFT-COT), pick a model per stage from `planner-context.md` §4, decide review placement (per-phase for security/core, once-at-end for small edits). Full algorithm, master model table, and the agent-name resolution / gap-fallback hook live in `references/execution-mode.md`.

## Task analysis (Type / Size / Criticality / Parallelism / Risk gates)

The "Task summary" section of `PLANNER_OUTPUT.md` is filled by these five categorizations:

1. **Тип:** feature / bugfix / refactor / doc / research / mixed.
2. **Размер:**
   - S: 1 модуль, <200 LOC impact, нет миграций.
   - M: 2-4 модуля, 200-800 LOC, ≤1 миграция.
   - L: 5+ модулей, >800 LOC, multi-миграции, cross-stack.
3. **Критичность:** normal / security-sensitive / data-migration / breaking-API / UX-critical.
4. **Параллелизм:** поиск **независимых осей**. Если всё строго последовательно — параллелизм = 1.
5. **Risk gates:** где обязателен review / human-in-the-loop?

Each categorization is **evidence-based** (FPF A.10): size comes from counting modules / LOC in the README, criticality from explicit signals in the README (auth, PII, migrations), parallelism from looking at module dependencies. Do not guess; if the README is ambiguous, mark the categorization as `unknown — needs user confirmation` and surface the question in the plan's Risks section.

## Output format

Write to `<feature-dir>/PLANNER_OUTPUT.md` if a feature directory exists; otherwise output to chat. The template:

```markdown
# Planner Output — <feature-id or task-name>

**Mode:** architecture | execution
**Generated:** <ISO-date>
**Inputs read:** <список файлов>
**Planner-context version:** <last auto-scan date from §7>

## Task summary
- Type: feature | bugfix | refactor | doc | research | mixed
- Size: S | M | L (обоснование: N модулей, ~LOC, миграции)
- Criticality: normal | security | data-migration | breaking-API | ux-critical
- Parallelism axis: <что независимо> / <что последовательно>

## Execution plan

### Phase 1 — <название> (parallel | serial)
- Agent: <имя из planner-context §1> | Model: <opus|sonnet|haiku> | Skills: <список из §3 | —>
  - Focus: <что делает>
  - Inputs: <какие файлы читает>
  - Outputs: <какие файлы/артефакты создаёт>
  - Est. tokens: ~N | Est. wall-clock: ~M min

### Phase 2 — <название> (serial, depends on Phase 1)
- ...

## Cost estimate
| | Naive /plan-do | Optimized | Δ |
|---|---|---|---|
| Tokens | ~N | ~M | -X% |
| Wall-clock | ~N min | ~M min | -X% |
| $-cost (relative) | 1.0 | 0.Y | -X% |

Обоснование экономии: <в двух предложениях>.

## Risks & human-in-the-loop gates
- <риск> → <митигация | кого спросить>

## Fallback
Если <условие> не выполнено — переключись на <план B>.
```

If there is nothing to optimize, **still fill the template** and write in Cost estimate: «naive-подход оптимален → рекомендация: сразу `/plan-do` без planner'а». A plan that recommends skipping the planner is a valid output, not a failure — the force-function of always emitting the template surfaces the decision explicitly so the orchestrator and the user see it.

## Where to write

Two writeable paths, no others:

1. `<project-root>/.claude/planner-context.md` — only during bootstrap, or when a re-scan adds rows tagged `<!-- auto-added YYYY-MM-DD -->` / `<!-- stale, last seen YYYY-MM-DD -->` per `references/bootstrap.md` §7.
2. `<feature-dir>/PLANNER_OUTPUT.md` — the plan output.

If no feature directory exists (e.g. `/plan` was invoked with free-text task description), output the full plan to chat using the same template from the Output format section above. Do not create `PLANNER_OUTPUT.md` somewhere else; the only acceptable location is inside the feature directory.

The agent wrapper (`agents/planner.md`) repeats this constraint as a hard boundary, and the slash-command (`/plan`) inherits the same `allowed-tools` set so the constraint is enforced by least-privilege.

## Reference index

- `references/bootstrap.md` — load when `planner-context.md` is missing, stale, or a re-scan is requested. Contains the scanning algorithm, the stack→signal heuristic table (9 stacks shipped), the gap-output format, unknown-stack handling, and re-scan rules.
- `references/template-context.md` — load when bootstrap needs the canonical empty-shell template for `planner-context.md` (8 sections, including the new §8 `Unknown markers`).
- `references/architecture-mode.md` — load when input is a feature README and no architecture document exists yet. Contains the 4-option matrix, decision rules, output mapping, and common pitfalls.
- `references/execution-mode.md` — load when input is an existing architecture document. Contains the dependency-graph procedure, parallel-phase grouping rules, the master model table, code-review placement, and the agent-name resolution / gap-fallback hook.

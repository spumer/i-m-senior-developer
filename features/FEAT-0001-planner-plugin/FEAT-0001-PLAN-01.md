# FEAT-0001 — Planner Plugin: Architecture (PLAN-01)

> **Source feature spec:** `features/FEAT-0001-planner-plugin/README.md`
> **Legacy source for content reuse:** `~/.claude/agents/planner.md` (290 lines)
> **Marketplace target:** `i-m-senior-developer`
> **Initial version:** `0.1.0`

This document is the implementation contract. Every artifact, frontmatter field, section name, length budget, and content origin is specified here. Implementers fill in content per the spec; they do not make architectural choices.

## 0. Plugin Directory Layout (target)

```
plugins/planner/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── planner.md                           # ~30 lines — thin wrapper
├── skills/
│   ├── planner/
│   │   ├── SKILL.md                         # ~180-200 lines — core
│   │   └── references/
│   │       ├── bootstrap.md                 # ~180-220 lines
│   │       ├── architecture-mode.md         # ~80-110 lines
│   │       ├── execution-mode.md            # ~120-160 lines
│   │       └── template-context.md          # ~120-160 lines
│   └── planner-reflect/
│       └── SKILL.md                         # ~140-170 lines
├── commands/
│   ├── plan.md
│   └── plan-reflect.md
├── hooks/
│   └── README.md                            # placeholder, see §8
└── README.md                                # plugin-level
```

Anything not listed above must NOT be created. Empty `hooks/` directory is intentional per feature README §114.

---

## 1. Plugin Manifest (`plugins/planner/.claude-plugin/plugin.json`)

Single JSON object. No comments. Fields exactly as below.

| Field | Value | Rationale |
|---|---|---|
| `name` | `planner` | kebab-case, matches directory; plugin namespace will be `planner:` |
| `version` | `0.1.0` | per CLAUDE.md semver rule, initial release |
| `description` | `Meta-dispatcher plugin: analyzes tasks, builds execution plans, detects agent-catalog gaps, learns from past sessions. Replaces legacy ~/.claude/agents/planner.md.` | matches author tone of `llms-keeper`/`tdd-master`; first sentence describes core value, second flags migration |
| `author.name` | `Svyatoslav Posokhin` | matches existing manifests |
| `keywords` | `["planner", "orchestration", "meta-agent", "feature-planning", "agent-catalog", "reflection"]` | discoverability: planner role + orchestration + new "reflection" capability |

Note: existing plugins in this marketplace omit `category` from `plugin.json` (only marketplace.json carries it). Follow that convention — do **not** add a `category` field to `plugin.json`.

---

## 2. Marketplace Entry (edit `.claude-plugin/marketplace.json`)

Append the following object to the `plugins` array (after the `llms-keeper` entry to keep chronological order). Do not change other entries.

| Field | Value |
|---|---|
| `name` | `planner` |
| `description` | `Meta-dispatcher plugin: analyzes tasks, builds execution plans (architecture / execution modes), detects agent-catalog gaps, and learns from past sessions via /plan-reflect.` |
| `author.name` | `Svyatoslav Posokhin` |
| `source` | `./plugins/planner` |
| `category` | `development` |

The marketplace entry's `description` is what users see in plugin pickers — keep it informative but ≤220 chars.

---

## 3. Agent: `plugins/planner/agents/planner.md`

### 3.1 Frontmatter spec

| Field | Value | Justification |
|---|---|---|
| `name` | `planner` | matches plugin and skill names; namespacing yields `plugin:planner:planner` |
| `model` | `sonnet` | legacy uses `sonnet` (line 28); README §73 mandates `sonnet`; planner runs frequently, Opus is overkill, Haiku risks misrouting |
| `color` | `cyan` | legacy uses `cyan` (line 29); marketplace siblings use distinct colors (`green` tdd, `magenta` llms-keeper) so `cyan` stays free of clashes |
| `tools` | `["Read", "Grep", "Glob", "Write"]` | README §73 explicit list. Read/Grep/Glob = bootstrap scanning + task sizing (evidence-based). Write = only `planner-context.md` and `PLANNER_OUTPUT.md` (legacy lines 280-283). **Drop `WebSearch`** that legacy line 27 had — README §73 omits it; the agent is meta-routing, not research, and least-privilege wins. |
| `description` | multi-line YAML literal block (`description: \|`) starting `Meta-agent dispatcher: analyzes a task and constructs an execution plan for other agents...`. MUST contain russian triggers «план», «разбей задачу», «распредели», «оптимизируй процесс», «как сделать быстрее/дешевле»; MUST contain 2 `<example>` blocks lifted from legacy lines 16-26 (one architecture trigger, one optimization trigger). | preserves trigger surface that operators already use; keeps russian per project conventions; `<example>` blocks are mandatory per `agent-development` SKILL §description |

### 3.2 Body spec (~30 lines, NOT a full system prompt)

The agent body is intentionally THIN. It activates the skill and refuses to do skill work itself. Sections in order:

1. **One-paragraph role statement** — "You are a meta-dispatcher. You build plans, you do not execute them."
2. **Activation directive** — explicit instruction: "On invocation, read the `planner` skill and follow it. The skill defines the full workflow (bootstrap, architecture mode, execution mode, output format)."
3. **Hard boundaries (5 bullets, copied from legacy lines 277-289)** — "do not run agents", "do not edit code", "do not edit existing PLAN/DESIGN files", "Write is allowed only on `<project>/.claude/planner-context.md` and `<feature-dir>/PLANNER_OUTPUT.md`", "max 7 agents in one parallel phase".
4. **What this agent is NOT** — "not a developer; if a sub-task requires writing code, return the plan and stop. The orchestrator dispatches the actual workers."
5. **Pointer to reflection** — one sentence: "After session completion, the user (or the orchestrator) invokes `/plan-reflect` which activates the `planner-reflect` skill. This agent does not perform reflection itself."

### 3.3 Legacy content mapping (where each legacy section moves)

| Legacy section (line range) | Destination |
|---|---|
| Frontmatter `description` (lines 1-26) | Agent frontmatter `description`, condensed but russian triggers + 2 `<example>` blocks preserved |
| Frontmatter `tools/model/color` (lines 27-29) | Agent frontmatter, with `WebSearch` dropped |
| Body header + role statement (lines 32-44) | Agent body §1 (role) + §2 (activation pointer) |
| §"Принципы" 1-6 (lines 46-65) | Skill `SKILL.md` §"Principles" — they belong to the *skill*, not the wrapper |
| §"Bootstrap — проект-специфичный контекст" (lines 67-180) | `references/bootstrap.md` (algorithm + `Glob` paths) + `references/template-context.md` (the markdown template). Mention in `SKILL.md` only as a one-line pointer. |
| §"Два режима работы" → "Режим 1" (lines 182-194) | `references/architecture-mode.md` (full) + 5-line summary in `SKILL.md` |
| §"Два режима работы" → "Режим 2" (lines 196-210) | `references/execution-mode.md` (full) + 5-line summary in `SKILL.md` |
| §"Метод анализа задачи" (lines 212-223) | `SKILL.md` (this is core, lives in main file) |
| §"Output format плана" (lines 225-274) | `SKILL.md` §"Output format" (template stays in main file — orchestrator needs it on every activation) |
| §"Границы" (lines 277-290) | Agent body §3 (boundaries) — copied verbatim, this is the wrapper's primary job |

After this split: legacy 290 lines → 4 references + thin SKILL.md + 30-line agent. Legacy file is **deleted** by user per migration guide (§9).

---

## 4. Skill: `plugins/planner/skills/planner/SKILL.md`

Hard length budget: **180-220 lines** (≈1,500-1,900 words). If this is exceeded during implementation, push content into a reference — the progressive-disclosure rule from README "Polish" §90 is non-negotiable.

### 4.1 Frontmatter spec

| Field | Value |
|---|---|
| `name` | `planner` |
| `description` | Third-person, starts `This skill should be used when the user asks to "plan a task", "build an execution plan", "split this work", "make this faster/cheaper", or in russian «план», «разбей задачу», «распредели», «оптимизируй процесс», «как сделать быстрее/дешевле». Also activates when a feature README is presented before /plan-do, when an architecture session is starting, or when an existing PLAN document is about to be executed. Provides two modes: architecture planning (from a feature README) and execution planning (from an architecture document).` Length: 5-8 sentences. **Must include all russian phrases above** — they are the legacy trigger surface and removing them breaks user habits. |

### 4.2 Section outline (this is the full SKILL.md skeleton — fill, don't add)

| § | Section | Content origin | Approx lines |
|---|---|---|---|
| 1 | `# Planner — meta-dispatcher` (H1) + 2-sentence purpose statement | rewrite of legacy lines 32-38 | 5 |
| 2 | `## Principles` — 6 numbered principles | legacy lines 46-65, reused verbatim (translation OK, content stays) | 25 |
| 3 | `## Workflow` — 4-step pipeline: (1) check `planner-context.md`, (2) classify task (architecture vs execution), (3) load matching reference, (4) emit `PLANNER_OUTPUT.md` | new content, 4 numbered steps with one sentence each | 15 |
| 4 | `## Bootstrap pointer` — one paragraph: "If `<project-root>/.claude/planner-context.md` is missing or stale, follow `references/bootstrap.md`. Do not inline bootstrap logic here — it is one-time per project and bloats context." Mentions the template lives at `references/template-context.md`. | new content | 8 |
| 5 | `## Mode 1 — architecture planning (summary)` — 5-line summary + pointer to `references/architecture-mode.md` for the option matrix | summary of legacy lines 184-194 | 10 |
| 6 | `## Mode 2 — execution planning (summary)` — 5-line summary + pointer to `references/execution-mode.md` for dependency-graph + parallel-phase + model-table details | summary of legacy lines 196-210 | 10 |
| 7 | `## Task analysis (Type / Size / Criticality / Parallelism / Risk gates)` — kept inline, this is core | legacy lines 212-223, reused verbatim (5 numbered items) | 25 |
| 8 | `## Output format` — full markdown template for `PLANNER_OUTPUT.md` (Task summary / Execution plan / Cost estimate / Risks / Fallback) | legacy lines 225-274, reused verbatim — this template is needed on every activation, must stay in core | 60 |
| 9 | `## Where to write` — restate the two writeable paths (`planner-context.md`, `PLANNER_OUTPUT.md`) and the "if no feature dir, output to chat" fallback | legacy lines 226-228 + 280-283, condensed | 8 |
| 10 | `## Reference index` — bullet list pointing to all 4 references with one-line "load when X" trigger per reference | new content (signals progressive disclosure) | 10 |

Total: ≈176 lines plus blank lines and code-fences ≈ 200. Within budget.

### 4.3 What does NOT belong in `SKILL.md`

These belong to references. If implementer is tempted to add them inline, they go to references instead:

- The full bootstrap algorithm with `Glob` patterns → `references/bootstrap.md`.
- The stack→signal heuristic table → `references/bootstrap.md`.
- The template body of `planner-context.md` → `references/template-context.md`.
- The architecture-mode option matrix and Opus-vs-Sonnet decision rules → `references/architecture-mode.md`.
- The execution-mode dependency-graph algorithm, parallel-phase grouping rules, and full model table → `references/execution-mode.md`.

---

## 5. Skill References

All references live in `plugins/planner/skills/planner/references/`. Each is an `.md` file with no frontmatter (references are loaded by Claude on demand based on `SKILL.md` pointers).

### 5.1 `bootstrap.md` — purpose, length, structure

**Purpose:** the on-demand algorithm for first-time-in-project setup, including stack gap detection. Loaded only when `planner-context.md` is missing or stale.

**Length budget:** 180-220 lines.

**Section outline:**

| § | Section | Content |
|---|---|---|
| 1 | `## When to load` | one sentence: load when SKILL.md §4 ("Bootstrap pointer") routes here |
| 2 | `## Scanning algorithm` | 4 numbered steps, content lifted from legacy lines 71-95: (1) agents — `Glob` `.claude/agents/*.md` and `~/.claude/agents/*.md`, read frontmatter `name`/`description`/`model`/`tools`; (2) slash-commands — `Glob` `.claude/commands/*.md` and `~/.claude/commands/*.md`; (3) skills — `Glob` `.claude/skills/*/SKILL.md` and `~/.claude/skills/*/SKILL.md` plus plugin skills detected via system instructions; (4) project conventions — read `README.md`, `CLAUDE.md`, `AGENTS.md`, `agents/context/*.md`, `project/*.md`; detect feature-directory pattern via `Glob` |
| 3 | `## Empty-catalog handling` | rule from legacy lines 99-101 + README Edge-Case row 1: if no project agents/commands/skills exist, write empty tables tagged `TODO: fill manually`. Do **not** invent agents. |
| 4 | `## Stack gap-detection — heuristic table` | **the 6+ base stacks**, exact file markers per stack. See table below. |
| 5 | `## Gap output format` | the exact line format used in §1 of `planner-context.md` when a stack is detected but no agent covers it: `❌ GAP — fallback: general-purpose` (per README §27 + §130). One-line examples: `❌ GAP (frontend, React) — fallback: general-purpose`. |
| 6 | `## Unknown-stack handling` | per README Edge-Case row 2 + README §61: if file markers don't match any known stack, write the discovered markers verbatim into §8 of the context file (new section), tag `unknown stack`, and ask the user to fill manually. Reference `template-context.md` §8. |
| 7 | `## Re-scan rules` | per README Edge-Case rows 3-4: do not overwrite manual edits; auto-add new rows with `<!-- auto-added YYYY-MM-DD -->`; mark missing-since-last-scan rows with `<!-- stale, last seen YYYY-MM-DD -->` instead of deleting. |
| 8 | `## Output` | a single Write call to `<project-root>/.claude/planner-context.md` using the template from `template-context.md`. After Write, return control to `SKILL.md` workflow §3. |

**Stack→signal table (§4 content, exact rows; implementer fills the file with these and may extend):**

| Stack key | Required markers (any one matches) | Common variants signal |
|---|---|---|
| `backend-python` | `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg`, `Pipfile` | `manage.py` → Django; `fastapi` in deps → FastAPI; `flask` in deps → Flask |
| `backend-node` | `package.json` (with backend deps like `express`, `nestjs`, `fastify`, `koa`), `tsconfig.json` (server-side) | `nest-cli.json` → NestJS; `next.config.*` and a `pages/api` or `app/api` dir → Next.js API |
| `frontend` | `package.json` with `react`, `vue`, `@angular/core`, `svelte`, `solid-js`; `index.html` at root or under `public/`; `vite.config.*`, `webpack.config.*` | `next.config.*` → Next.js; `nuxt.config.*` → Nuxt; `astro.config.*` → Astro |
| `mobile-android` | `android/` directory, `build.gradle`, `app/build.gradle`, `AndroidManifest.xml` | Kotlin (`*.kt`) vs Java; React-Native if `package.json` also present at root |
| `mobile-ios` | `ios/` directory, `*.xcodeproj`, `*.xcworkspace`, `Podfile` | SwiftUI signal: `*.swift` files; Objective-C: `*.m`/`*.h` |
| `infra` | `Dockerfile`, `docker-compose.y*ml`, `Makefile` (with deploy targets), `.github/workflows/`, `.gitlab-ci.yml`, `terraform/*.tf`, `kubernetes/*.yaml`, `helm/Chart.yaml` | Terraform vs k8s vs CI-only — record sub-marker |
| `backend-go` | `go.mod`, `go.sum`, `main.go` | gin/echo/fiber in `go.mod` |
| `backend-rust` | `Cargo.toml`, `Cargo.lock` | actix/axum/rocket signal |
| `data` | `dbt_project.yml`, `airflow/`, `dags/`, `*.ipynb` clusters, `notebooks/` | dbt vs Airflow vs Jupyter |

**Note for implementer:** the table above is the minimum. Order matters: detect Python before Node before Frontend (frontend often coexists with backend). For monorepos with multiple stacks, list all detected stacks; gaps are flagged per-stack.

**Legacy content reused:** lines 71-95 (scanning), 99-101 (empty catalog rule), 109-113 (re-scan rules). Stack-table is **new content** (legacy did not have it; it is the FEAT-0001 P1 capability per README §27).

### 5.2 `architecture-mode.md` — purpose, length, structure

**Purpose:** Mode 1 (architecture planning) details. Loaded only when SKILL.md §5 routes here.

**Length budget:** 80-110 lines.

**Section outline:**

| § | Section | Content |
|---|---|---|
| 1 | `## When to load` | one sentence: load when input is a feature README and no architecture document exists yet |
| 2 | `## Inputs and exit criterion` | input: `<feature-dir>/README.md`. Exit: `<feature-dir>/PLANNER_OUTPUT.md` written or chat output (no feature dir). |
| 3 | `## Option matrix` | 4 numbered options from legacy lines 187-194: (a) one architect on Opus — monolithic, strong coupling; (b) N parallel sub-architects on Sonnet — N≤4, weak coupling between domains; (c) single quick-pass on Haiku — <200 LOC impact, single module, no DB migrations; (d) separate security sub-plan — when auth/authz/PII present. |
| 4 | `## Decision rules` | new short section: when to pick which option; explicit "default = Sonnet single-architect unless evidence forces otherwise"; cite FPF A.11 (parsimony) — don't escalate to Opus or split into N agents on a guess. |
| 5 | `## Output mapping` | what fills the "Phase X" blocks of `PLANNER_OUTPUT.md` for each chosen option; reuse the output template from SKILL.md §8. |
| 6 | `## Common pitfalls` | 3 bullets: don't over-parallelize a tightly-coupled domain (integration cost > savings); don't pick Opus for routine architecture; if a security review is needed, make it an explicit phase, not an inline "and also". |

**Legacy content reused:** lines 184-194 (option matrix). Decision rules and pitfalls are **new content**.

### 5.3 `execution-mode.md` — purpose, length, structure

**Purpose:** Mode 2 (execution planning) details. Loaded only when SKILL.md §6 routes here.

**Length budget:** 120-160 lines.

**Section outline:**

| § | Section | Content |
|---|---|---|
| 1 | `## When to load` | one sentence: load when input is an existing architecture document (`*-PLAN-*.md`, `*-DESIGN-*.md`, ARCHITECTURE.md, or similar) |
| 2 | `## Inputs and exit criterion` | input: architecture file. Exit: updated/created `PLANNER_OUTPUT.md`. |
| 3 | `## Dependency graph construction` | 3-step procedure: (1) extract stages from the architecture document (one block = one stage candidate); (2) for each stage, list its prerequisites by stage-id; (3) topo-sort. State the strict-serial rule from legacy 200-201: migrations → models → views → frontend. |
| 4 | `## Parallel phase grouping` | rule: group independent stages into a phase, **max 7 agents per phase** (LIFT-COT cited in legacy line 284-285). Explicit sub-limits: planning-phase ≤6, validation-phase ≤7, integration-phase ≤4. |
| 5 | `## Model selection table` | the model table from legacy lines 148-152, reused verbatim. Columns: model / strength / weakness / relative cost / when to use. (This is the master table; `planner-context.md` §4 carries the project's local override.) |
| 6 | `## Code-review placement` | rule from legacy line 203-205: review after every phase for security/core; review once at end for small edits. |
| 7 | `## Agent-name resolution` | from legacy lines 206-210: agent names come ONLY from `planner-context.md` §1. If a needed role is missing, write the role kind as `<role-kind>` and add a line "mapping per planner-context.md §1; if no agent in catalog, orchestrator falls back to general-purpose Task tool". This is the hook that makes the gap-flag actually visible to the orchestrator. |
| 8 | `## Output mapping` | how stages fill into the "Phase X" blocks of `PLANNER_OUTPUT.md`; reference SKILL.md §8 template; emphasize Cost-estimate row must compare naive `/plan-do` vs optimized plan. |

**Legacy content reused:** lines 196-210 (Mode 2 narrative), lines 148-152 (model table). Sections 3-4 (graph + grouping algorithm details) are **expanded** from the legacy one-paragraph mention.

### 5.4 `template-context.md` — purpose, length, structure

**Purpose:** the canonical empty-shell template for `<project-root>/.claude/planner-context.md`. Loaded by `bootstrap.md` §8 and reused on re-scan.

**Length budget:** 120-160 lines (the template itself plus a short header explaining it).

**Section outline:**

| § | Section | Content |
|---|---|---|
| 1 | `## Purpose` | one paragraph: this is the template that is written to `<project-root>/.claude/planner-context.md` on first bootstrap. The body is a fenced markdown block; the implementer copies it verbatim. |
| 2 | `## Conventions` | the three meta-rules: (a) `<!-- auto-added YYYY-MM-DD -->` for entries added during re-scan; (b) `<!-- stale, last seen YYYY-MM-DD -->` for entries no longer found; (c) manual user edits are sources of truth — never overwritten. (per README Edge-Cases rows 3-4 + legacy lines 109-113) |
| 3 | `## The template` (fenced ` ```markdown ` block) | the 8-section template, see exact list below |

**The 8-section template (each becomes a `## ` heading inside the fenced block):**

| § # | Heading | Content origin |
|---|---|---|
| §1 | `Каталог агентов` | legacy lines 128-132 — table: Имя / Источник / Роль / Сильные стороны / Когда звать. Plus a row format for gaps: `❌ GAP (<stack>, <variant>) — fallback: general-purpose` (per `bootstrap.md` §5). |
| §2 | `Каталог slash-команд` | legacy lines 134-138 — table: Команда / Источник / Назначение |
| §3 | `Каталог skills` | legacy lines 140-144 — table: Skill / Источник / Триггер активации |
| §4 | `Таблица моделей` | legacy lines 146-152 — Opus/Sonnet/Haiku table (project may override; default ships in template) |
| §5 | `Хранение артефактов фич` | legacy lines 154-168 — feature root, naming pattern, artifact list, optional context-file pointers |
| §6 | `Соглашения именования` | legacy lines 170-172 — placeholder for project-specific naming conventions and lessons-learned bullets from `/plan-reflect` |
| §7 | `Метаданные bootstrap` | legacy lines 174-179 — last auto-scan date, count of agents/skills/commands |
| **§8** | `Unknown markers` (new) | **NEW per README Edge-Case row 2 / §61.** Free-form list of file markers detected on bootstrap that did not match any known stack. Format: `- <marker>: <discovered location> — TODO: assign stack`. Empty by default. |

**Legacy content reused:** lines 117-180, the entire template. New addition: §8 "Unknown markers". The `<!-- auto-added ... -->` and `<!-- stale, last seen ... -->` conventions from legacy lines 109-113 are documented in §2 of this reference.

---

## 6. Skill: `plugins/planner/skills/planner-reflect/SKILL.md`

Hard length budget: **140-170 lines** (≈1,200-1,400 words). This is a small, single-purpose skill — no references, all content stays inline.

### 6.1 Frontmatter spec

| Field | Value |
|---|---|
| `name` | `planner-reflect` |
| `description` | Third-person, starts `This skill should be used when the user invokes /plan-reflect, says "reflect on the plan", "what did we learn", "post-mortem the planning", or in russian «отрефлексируй», «что пошло не так», «обнови контекст планнера», «сверь план с фактом». Activates after a session that ran /plan-do or otherwise produced a PLANNER_OUTPUT.md. Updates planner-context.md with four learning types: gap-fill, model-strength signals, user-correction patterns, and cost-calibration deltas. Always emits a "Lessons learned" section, even if empty.` Length: 5-7 sentences. **Russian triggers required** (parity with main `planner` skill). |

### 6.2 Section outline (full skeleton — fill, don't add)

| § | Section | Content |
|---|---|---|
| 1 | `# Planner-Reflect — post-task learning` | one-paragraph purpose statement: this skill compares plan vs reality, extracts lessons, and writes them back into `planner-context.md` so the next session starts smarter. Cites README §35-44. |
| 2 | `## Inputs (5 evidence sources)` | numbered list, all 5 sources from README §88: (1) `<feature-dir>/PLANNER_OUTPUT.md` — what was planned; (2) `git log --oneline <since-plan>..HEAD` — what was actually committed; (3) review-files under `<feature-dir>/review-request-changes/` — defects found; (4) agent transcripts via `TaskGet`/`TaskOutput` — to detect retry/escalate patterns; (5) user messages from the current session — explicit corrections like «не делай сам» / «переделай». |
| 3 | `## When evidence is missing` | per README Edge-Case row 5+6: if `PLANNER_OUTPUT.md` is absent → exit with message "nothing to reflect on, run /plan first; do not fail". If transcripts are unavailable (cross-session limitation, see §12 Open Questions) → degrade to git-diff + review-files; explicitly note in output: `transcript-based learnings unavailable`. |
| 4 | `## The 4 update types` | numbered list, each with one paragraph + the §X destination in `planner-context.md`: |
| 4.1 | `gap-fill` | If orchestrator used `general-purpose` where `planner-context.md` §1 had a `❌ GAP` flag — confirm the gap was hit, append `<!-- gap-confirmed YYYY-MM-DD from FEAT-XXXX -->` to that row. If a stack appeared that wasn't even flagged — add a new GAP row with `<!-- discovered YYYY-MM-DD from FEAT-XXXX -->`. Destination: §1 of `planner-context.md`. |
| 4.2 | `model-strength` | If transcripts (or git-log of repeat commits on the same files) show retry-loops («test failed → fix → still failed → escalate»), record per README §40: «for tasks of type X on this project, Sonnet was weak → try Opus». Destination: §4 of `planner-context.md`. Tone-rule from README Edge-Case row 9: do **not** write categorical "Sonnet bad" — always tie to task-type and project, with FEAT-id as evidence. |
| 4.3 | `user-corrections` | Extract pattern from explicit user messages («не делай сам», «это неправильно», «переделай»). Save as a one-line guard-rail in §6 (conventions): "avoid <pattern> — learned from FEAT-XXXX". Destination: §6 of `planner-context.md`. |
| 4.4 | `cost-calibration` | Compare planned tokens/wall-clock from `PLANNER_OUTPUT.md` § "Cost estimate" against actuals (token consumption visible from session metadata, wall-clock from commit timestamps). If delta > ±30%, note correction in §4 of `planner-context.md`: "estimate adjustment: <task-type> takes ~Nx more/less". |
| 5 | `## Always-emit "Lessons learned" section` | per README Polish §89: every `/plan-reflect` run produces a `## Lessons learned (FEAT-XXXX, YYYY-MM-DD)` block, even if it has zero items. The empty case shows `_no actionable lessons this session_`. This is a force-function — the user sees the section and notices when nothing was learned, prompting reflection. |
| 6 | `## Output protocol` | (a) write changes to `<project-root>/.claude/planner-context.md` using the `<!-- learned YYYY-MM-DD from FEAT-XXXX -->` tag (per README §43); (b) emit a chat summary listing what changed; (c) optionally, if a lesson is critical (defined as: same mistake observed in ≥2 distinct sessions), suggest the user create an auto-memory entry — do NOT create it autonomously (HITL gate, per architect principles in this prompt). |
| 7 | `## PII / secret stripping` | per README Edge-Case row 11: never copy raw transcript chunks into `planner-context.md`. Extract abstract patterns only: "3 retry iterations to green tests" not "the test `test_user_login_xyz` failed because password = 'p4ssw0rd!'". Concrete rule: before Write, scan the proposed addition for: emails, tokens that look like API keys (40+ char alphanumeric), file paths containing user-home (`/Users/<name>/...`, `/home/<name>/...`). If detected → mask and proceed. |
| 8 | `## Boundaries` | analogous to agent boundaries: do NOT modify code; do NOT modify `PLANNER_OUTPUT.md` (it's a historical record); the only writeable target is `<project-root>/.claude/planner-context.md`. |
| 9 | `## Reference index` | one paragraph: this skill has no references; everything is inline because the workflow is small and self-contained. |

---

## 7. Commands

### 7.1 `plugins/planner/commands/plan.md`

**Frontmatter spec:**

| Field | Value | Justification |
|---|---|---|
| `name` | `plan` | bare slash trigger `/plan`; namespace fallback `planner:plan` (see §7.3 below) |
| `description` | `Build an execution plan for a task or feature. Activates the planner skill in architecture or execution mode.` | shown in `/help` |
| `argument-hint` | `[feature-dir or task description]` | typical usages: `/plan features/FEAT-0042-x/`, `/plan refactor billing module` |
| `allowed-tools` | `Read, Grep, Glob, Write` | mirrors agent tool set (least-privilege) |
| `model` | (omit, inherit) | command runs in user's session, no need to override |

**Body (~10-15 lines, instructions FOR Claude per `command-development` SKILL §"Critical: Commands are Instructions FOR Claude"):**

The body instructs Claude to:
1. Activate the `planner` skill.
2. If `$ARGUMENTS` is a path → treat as Mode 1 (architecture) input if it points to a feature README, or Mode 2 (execution) if it points to an existing PLAN/DESIGN doc.
3. If `$ARGUMENTS` is free text → treat as task description, work in chat-output mode.
4. Follow the skill's workflow start-to-finish; emit `PLANNER_OUTPUT.md` per skill §8.

### 7.2 `plugins/planner/commands/plan-reflect.md`

**Frontmatter spec:**

| Field | Value |
|---|---|
| `name` | `plan-reflect` |
| `description` | `Reflect on the just-completed plan: compare plan vs reality, update planner-context.md, emit Lessons learned.` |
| `argument-hint` | `[feature-dir or empty for current session]` |
| `allowed-tools` | `Read, Grep, Glob, Write, Bash(git:*)` (Bash needed for `git log` evidence per §6.2 §2 — restricted to git only) |
| `model` | (omit, inherit) |

**Body (~10-15 lines):**

Instructions to Claude:
1. Activate the `planner-reflect` skill.
2. If `$ARGUMENTS` provided → use as feature-dir; else → infer from latest `PLANNER_OUTPUT.md` modified in current working tree.
3. Follow skill workflow; produce chat summary + write to `planner-context.md`.
4. If no `PLANNER_OUTPUT.md` exists → emit the graceful message from skill §3 and stop.

### 7.3 Namespacing decision (resolves Open Question §3)

**Decision: register the command bare as `/plan` and `/plan-reflect`. Document `planner:plan` and `planner:plan-reflect` as the namespaced fallback.**

Rationale, drawing on the `command-development` SKILL (§"Plugin Command Organization", §"Plugin commands"): plugin-shipped commands are auto-discovered from `commands/` and **automatically namespaced** by Claude Code as `<plugin>:<command>` — `/help` shows `(plugin:planner)` next to them. The bare form `/plan` is the slug Claude Code derives from the filename `plan.md`. Both work simultaneously; the namespaced form is the disambiguator if a user has their own `/plan`. The plugin author does **not** configure namespacing manually — it follows from the file name. So:

- **Default invocation:** `/plan`, `/plan-reflect` (most ergonomic, matches user habit from legacy planner)
- **Disambiguation fallback:** `/planner:plan`, `/planner:plan-reflect` (shown in `/help` automatically; users learn it when collision happens, per README Edge-Case row 8)
- **No configuration in `plugin.json`:** namespacing is implicit per `plugin-structure` SKILL §"Plugin Command Organization"

The README of the plugin (§9) must mention both forms.

---

## 8. Hooks

The `hooks/` directory is **created but contains only one file: `README.md`** — a placeholder. No `hooks.json`, no scripts ship in v0.1.0. This matches feature README §114 ("hooks/ — пока пусто, оставить на потом").

### 8.1 `plugins/planner/hooks/README.md` — placeholder spec

**Length:** 25-40 lines.

**Sections:**

1. `# Hooks (placeholder)` — one paragraph stating no hooks ship with v0.1.0; this directory exists so users who want auto-reflect can drop a config in.
2. `## Future: SessionEnd auto-reflect` — describes the *future* shape of `hooks.json` and `session-end.sh` so users can add it themselves. Concrete shape (no actual code, only structural description):
   - **`hooks.json`** would register a `SessionEnd` event handler that runs `${CLAUDE_PLUGIN_ROOT}/hooks/session-end.sh` with timeout 10s. (Format follows the plugin hooks.json wrapper format from `hook-development` SKILL §"Plugin hooks.json Format".)
   - **`session-end.sh`** would be a one-liner that checks for the existence of `<feature-dir>/PLANNER_OUTPUT.md` modified during the current session, and if found, prints a `systemMessage` reminding Claude to invoke `/plan-reflect`. It does **not** invoke `/plan-reflect` itself — the user (or orchestrator) decides.
3. `## Why opt-in` — one paragraph: cross-session transcript availability is uncertain (see §12 Open Question 1), so auto-reflect is risky to ship as default. Users on tightly-bounded sessions can enable it; users with cross-session workflows should run `/plan-reflect` manually inside the session that did the work.
4. `## How to enable` — exact two-step procedure: (a) create `hooks/hooks.json` with the registration block above, (b) create `hooks/session-end.sh` with the one-liner above and `chmod +x`. After enabling, restart Claude Code (per `hook-development` SKILL §"Hooks Load at Session Start").

This decision resolves Open Question 2 (hook strategy): **opt-in placeholder, not shipped active.**

---

## 9. Plugin README: `plugins/planner/README.md`

Plugin-level user-facing documentation. Mirrors the structure of `plugins/llms-keeper/README.md` and `plugins/tdd-master/README.md`.

**Length budget:** 90-130 lines.

**Section outline (sections only, fill content per spec):**

| § | Heading | Content directive |
|---|---|---|
| 1 | `# planner` | H1, plugin name |
| 2 | One-paragraph intro | what the plugin replaces (legacy `~/.claude/agents/planner.md`) and what it adds (gap-detection, reflection loop) |
| 3 | `## What it does` | bullet list, 5-7 items: bootstrap scanning + gap-detection; architecture-mode planning; execution-mode planning with parallel-phase grouping; cost estimation; post-task reflection via `/plan-reflect`; `planner-context.md` as project source of truth |
| 4 | `## Structure` | code-fenced directory tree (mirroring §0 of this plan) |
| 5 | `## Installation` | per-marketplace install instructions: how to add to Claude Code, citing the marketplace name `i-m-senior-developer` |
| 6 | `## Migration from legacy planner.md` | the exact bash block from feature README §134-148, **verbatim**, plus a sanity-check bullet list: (1) confirm `~/.claude/agents/planner.md` is gone; (2) confirm `<project>/.claude/agents/planner.md` is gone; (3) confirm `/plan` resolves to the plugin in `/help` (look for `(plugin:planner)` label); (4) run `/plan` on any feature to trigger fresh bootstrap |
| 7 | `## Modes` | brief explanation of architecture vs execution mode, with one example invocation each. Pointer to skill references for detail. |
| 8 | `## Examples` | 3 short usage examples: (a) first-time bootstrap, (b) architecture planning from feature README, (c) post-session reflection |
| 9 | `## Commands` | bullet list of the two slash commands with both bare and namespaced forms (per §7.3) |
| 10 | `## Configuration` | one paragraph: project-specific config lives in `<project>/.claude/planner-context.md`; the file is created on first bootstrap; manual edits are preserved |
| 11 | `## Requirements` | minimal: Claude Code with plugin marketplaces support |

**Migration commands (§6) — exact, taken from feature README §134-148:**

```
# 1. Install plugin from marketplace (after publication)

# 2. Remove legacy planner.md
rm -f ~/.claude/agents/planner.md
rm -f <project>/.claude/agents/planner.md  # if present

# 3. Verify project planner-context.md isn't broken
#    (plugin will offer to update structure on first run)

# 4. Run /plan on any feature — bootstrap should pass cleanly
```

---

## 10. Implementation Stages (parallel batching)

Stages are independent unless an explicit dependency is noted. The implementer can run independent stages in parallel sub-agents.

### Stage A — Scaffolding (no dependencies; runs first or in parallel with B/C)

**Files:**
- `plugins/planner/.claude-plugin/plugin.json` (per §1)
- `plugins/planner/agents/planner.md` (per §3)
- `plugins/planner/README.md` (per §9)
- Edit to `.claude-plugin/marketplace.json` to append the planner entry (per §2)

**Why grouped:** all scaffolding; none depends on skill internals; safe to do first.

### Stage B — Skill `planner` core (depends on Stage A only for marketplace coherence; can start in parallel)

**Files:**
- `plugins/planner/skills/planner/SKILL.md` (per §4)
- `plugins/planner/skills/planner/references/bootstrap.md` (per §5.1)
- `plugins/planner/skills/planner/references/architecture-mode.md` (per §5.2)
- `plugins/planner/skills/planner/references/execution-mode.md` (per §5.3)
- `plugins/planner/skills/planner/references/template-context.md` (per §5.4)

**Why grouped:** the 4 references are siblings cross-referenced from `SKILL.md`; coherent edit unit; one implementer keeps them consistent. Internal sub-parallelism: `template-context.md` and `architecture-mode.md` and `execution-mode.md` are independent of each other; `bootstrap.md` references `template-context.md` (so write template first, then bootstrap).

### Stage C — Skill `planner-reflect` (independent; parallel with B)

**Files:**
- `plugins/planner/skills/planner-reflect/SKILL.md` (per §6)

**Why standalone:** no references, no cross-deps with B; only touches its own SKILL.md.

### Stage D — Commands (depends on B and C — must know skill names exist)

**Files:**
- `plugins/planner/commands/plan.md` (per §7.1)
- `plugins/planner/commands/plan-reflect.md` (per §7.2)

**Why depends on B/C:** commands name the skills they activate. Implementer can stage these last when skill files exist (avoids dangling references in `/help`).

### Stage E — Hooks placeholder (independent; parallel with anything)

**Files:**
- `plugins/planner/hooks/README.md` (per §8.1)

**Why standalone:** trivial placeholder, no logic, no deps.

### Suggested parallel schedule

```
[parallel] Stage A  ┐
[parallel] Stage B  ├─→ [serial] Stage D ──→ done
[parallel] Stage C  ┘
[parallel] Stage E  (any time)
```

A, B, C, E run concurrently. D waits for B and C to finish so it can reference correct skill names.

---

## 11. Acceptance Checklist

Maps each "Must Have" line from feature README §72-84 to a concrete artifact. All boxes must be addressable to call FEAT-0001 done.

- [ ] **README §72** `plugins/planner/.claude-plugin/plugin.json` with `name`, `version: 0.1.0`, `description`, `author`, `keywords` → §1 of this plan
- [ ] **README §73** `plugins/planner/agents/planner.md` thin agent-wrapper, frontmatter `name`/`description`/`model: sonnet`/`tools: [Read, Grep, Glob, Write]` → §3 of this plan
- [ ] **README §74** `plugins/planner/skills/planner/SKILL.md` core: two modes, output format, task-analysis method, no bootstrap, no reflect → §4 of this plan
- [ ] **README §75** `plugins/planner/skills/planner/references/bootstrap.md` scanning + gap-detection + stack heuristics → §5.1
- [ ] **README §76** `plugins/planner/skills/planner/references/architecture-mode.md` → §5.2
- [ ] **README §77** `plugins/planner/skills/planner/references/execution-mode.md` → §5.3
- [ ] **README §78** `plugins/planner/skills/planner/references/template-context.md` (8-section template, including new §8 Unknown markers) → §5.4
- [ ] **README §79** `plugins/planner/skills/planner-reflect/SKILL.md` post-task reflection with 4 update types → §6
- [ ] **README §80** `plugins/planner/commands/plan.md` → §7.1
- [ ] **README §81** `plugins/planner/commands/plan-reflect.md` → §7.2
- [ ] **README §82** `plugins/planner/README.md` with what/install/migration → §9
- [ ] **README §83** Marketplace entry appended to `i-m-senior-developer/.claude-plugin/marketplace.json` → §2
- [ ] **README §84** Version-bump rule on subsequent edits — no artifact, but documented in §1 (CLAUDE.md compliance)

**Polish coverage (README §86-90):**

- [ ] **README §87** Stack-detection extensible: 6+ base stacks → §5.1 stack table (10 rows shipped, more allowed)
- [ ] **README §88** 5 evidence sources for `/plan-reflect` → §6.2 row §2
- [ ] **README §89** Always-emit "Lessons learned" → §6.2 row §5
- [ ] **README §90** Progressive disclosure (lean SKILL.md + references/) → §4.1 length budget + §4.2 outline + §5 references

**Edge-case coverage (README §53-67) — verify each row of that table:**

- [ ] No `.claude/agents/` → bootstrap.md §3 + template-context.md §1 (TODO marker)
- [ ] Unknown stack → bootstrap.md §6 + template-context.md §8 (new section)
- [ ] Manual edits in `planner-context.md` → bootstrap.md §7 (re-scan rules)
- [ ] Bootstrap re-run → bootstrap.md §7 (`<!-- auto-added -->` / `<!-- stale -->` markers)
- [ ] `/plan-reflect` without `PLANNER_OUTPUT.md` → planner-reflect SKILL §3
- [ ] `/plan-reflect` without transcripts → planner-reflect SKILL §3 (degrade to git+review)
- [ ] Architecture exists, no `PLANNER_OUTPUT.md` → execution-mode.md §1+§2 (read arch as input)
- [ ] Legacy `planner.md` still on disk → README §6 (migration warning)
- [ ] `/plan` collision → README §6 (namespaced fallback `planner:plan`)
- [ ] "Weak model" finding wording → planner-reflect SKILL §4.2 (tone-rule from README row 9)
- [ ] PII/secrets in transcripts → planner-reflect SKILL §7

---

## 12. Open Questions / Decisions Made

The three open questions in feature README §149-153 are decided here. Rationale per question.

### Decision 1 — Cross-session transcript availability for `/plan-reflect`

**Decision:** Treat `TaskGet`/`TaskOutput` as *current-session-only* in v0.1.0. The skill is designed to gracefully degrade if transcripts are unavailable, and the documentation tells the user that for full transcript-based learning, `/plan-reflect` must run **in the same session** as the work it reflects on.

**Rationale:** the feature README itself flagged this as untested ("доступны ли ... cross-session или только в текущей? ... нужно проверить опытом"). Designing v0.1.0 around an unverified assumption is a violation of FPF A.10 (no claims without evidence). The graceful-degradation path (§6.2 row §3, "transcript-based learnings unavailable") preserves usefulness when transcripts are missing for any reason — same-session call where the tool failed, cross-session call where the tool can't reach back, or future Claude Code versions changing semantics. The documentation makes the constraint explicit so users adopt the habit. When transcripts turn out to work cross-session, the skill keeps working — no rewrite needed; only the docs lose a caveat.

**What this changes in artifacts:** §6.2 row §3 (graceful degradation), §8.1 §3 (why hook is opt-in not auto-active), §9 §6 (note in migration / examples that reflect-during-session is the recommended habit).

### Decision 2 — Hook integration with `SessionEnd`

**Decision:** Ship `hooks/` empty in v0.1.0 with a `README.md` placeholder describing the *shape* of an opt-in `SessionEnd` hook (§8.1). No `hooks.json` and no `session-end.sh` ship active. The placeholder gives users a 2-step recipe to enable auto-reflect themselves.

**Rationale:** three reasons converge.
1. Cross-session uncertainty (Decision 1) means an auto-fired `/plan-reflect` could trigger in a session that has no transcripts — producing partial, low-quality lessons that pollute `planner-context.md`.
2. The marketplace ships to many projects with different end-of-session conventions (Контракции has its own `/end-session`; other projects have none); auto-firing risks double-runs or conflicts.
3. The cost of opt-in is one paragraph in README; the cost of mis-fired auto-reflect is corrupted project memory. Asymmetry favors opt-in.

The `SessionEnd` hook is the right *eventual* integration point per `hook-development` SKILL §"SessionEnd"; we just don't enable it until the cross-session question is answered with evidence.

**What this changes in artifacts:** §8.1 (the README.md placeholder content), §10 Stage E (E ships only the placeholder doc).

### Decision 3 — Command namespace convention

**Decision:** Bare `/plan` and `/plan-reflect` as the primary invocation; `planner:plan` and `planner:plan-reflect` as automatic disambiguation fallbacks shown in `/help`. No manual namespacing config in `plugin.json`.

**Rationale:** the `plugin-structure` and `command-development` SKILL files (both v0.x from the official `plugin-dev` plugin) are explicit:
- Commands are auto-discovered from `commands/` (`plugin-structure` §"Commands").
- Plugin commands are *automatically* namespaced as `(plugin:<plugin-name>)` in `/help` (`command-development` §"Plugin Command Organization").
- The user invokes the bare name; collision is resolved by Claude Code, and the namespaced form is the manual disambiguator (`command-development` §"Plugin Command Patterns" + namespacing benefits).

This means: implementer files `commands/plan.md`. The bare slash `/plan` and the qualified `/planner:plan` both work out of the box. No config field, no special path. Documenting both forms in the plugin README (§9 §6, §9 §9) closes the user-facing loop. Russian-speaking users keep the bare form; teams with command collisions learn the namespaced form from `/help` output.

**What this changes in artifacts:** §7.3 (decision summary), §9 §6 (sanity-check item 3 mentions the `(plugin:planner)` label), §9 §9 (commands section lists both forms).

---

**End of FEAT-0001-PLAN-01.**

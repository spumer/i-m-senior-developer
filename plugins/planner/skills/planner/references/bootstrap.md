# Bootstrap — project-specific context for planner

This is the on-demand procedure that populates `<project-root>/.claude/planner-context.md` for the first time, plus the rules for re-scanning later. It is intentionally **not** in `SKILL.md`: bootstrap runs once per project (or on explicit re-scan), and inlining its details on every planner activation would bloat context.

## 1. When to load

Load this reference when `SKILL.md` ("Bootstrap pointer") routes here — i.e. when `<project-root>/.claude/planner-context.md` is missing, when the user explicitly asks for a re-scan, or when the file's `## 7. Метаданные bootstrap` section is older than the project's most recent agent/skill/command edits and needs refreshing.

## 2. Scanning algorithm

Run the five scans below in order. Use `Glob` for path matching and `Read` for frontmatter. Treat every result as **evidence** (FPF A.10) — do not invent agents, commands, or skills that the file system does not show.

1. **Agents.**
   - `Glob` `.claude/agents/*.md` (project-local agents).
   - `Glob` `~/.claude/agents/*.md` (global agents).
   - Plugin agents surfaced via system instructions (the agentic harness lists them alongside built-ins) — record them with Источник `plugin`. There is no filesystem path to glob for them; the surfaced list is the evidence. Without a surfaced record, a plugin that merely ships an agent file does not count.
   - For each match, `Read` the frontmatter and capture `name`, `description`, `model`, `tools`. Derive a one-line role summary from `description`.

2. **Slash-commands.**
   - `Glob` `.claude/commands/*.md` (project-local commands).
   - `Glob` `~/.claude/commands/*.md` (global commands).
   - Take the command name from the filename (without `.md`) and the purpose from frontmatter `description`.

3. **Skills.**
   - `Glob` `.claude/skills/*/SKILL.md` (project-local skills).
   - `Glob` `~/.claude/skills/*/SKILL.md` (global skills).
   - Plugin skills surfaced via system instructions (the agentic harness lists them) — record them with namespace `plugin:<plugin>:<skill>`.
   - For each skill, capture `name` and the activation trigger from `description`.

4. **Project conventions.**
   - `Read` (if present) `README.md`, `CLAUDE.md`, `AGENTS.md`.
   - `Glob` `agents/context/*.md` and `project/*.md` for additional context files.
   - Detect the feature-directory pattern: `Glob` `agents/features/FEAT-*/`, `features/FEAT-*/`, or any other `FEAT-*` shape — record what the project actually uses.
   - Read 1-2 existing feature directories to extract the artifact-naming convention (`DESIGN-01`, `PLAN-01`, `ISSUE-001`, etc.).

5. **Capabilities matrix (planner-context.md §9).** Derive rows from the results of scans 1–3; this step discovers nothing on its own. The capability set, per-kind requirements, provider-selection order and stopping rules live in `product-discovery/references/routing.md` — do not duplicate or contradict them here. The rules that govern filling:
   - **Coverage follows the contract, not the name.** Judge each discovered component (project / global / plugin agent or skill) only by its `description` / `SKILL.md`: contract confirmed → `full`; partially confirmed → `partial`; name matches but contract unconfirmed → `unknown`; checked and clearly not covering → `none`. A name that matches a capability is never evidence.
   - **Evidence is mandatory.** «Основание» holds the component file path (or the surfaced-system-instructions record for plugin components). Empty evidence forces coverage to `unknown` — the helper does this at parse time regardless of the written value.
   - **Column mappings.** «Поставщик» — the agent `name` for project/global agents, `<plugin>:<skill>` for plugin skills, the surfaced name for plugin agents. «Источник» — `project` / `global` / `plugin` / `builtin`. «Приоритет» — `project` for project components, `plugin` for plugin **and** global components, `builtin` for the plugin's own `planner:product-baseline`. `configured` is a manual value for explicitly pinned providers; a scan never writes it.
   - **Availability is what the scan owns.** `available` — the component is visible in the current environment; `not-surfaced` — a previously recorded component the current scan no longer finds (keep the row); `stale` — the component is visible but its description changed since the row was filled, so coverage needs re-verification; `error` — a known failed run of the component, written from an observed failure, never from scanning.
   - **Markers live inside cells.** `<!-- auto-added YYYY-MM-DD -->` and `<!-- stale, last seen YYYY-MM-DD -->` go inside the «Основание» cell of the §9 row. A standalone comment line inside the §9 table breaks machine parsing (the helper exits `3`).
   - Write rows only for what the scans grounded. The `planner:product-baseline` row ships with the template verbatim — it is a fact of the plugin, not invented project coverage.

## 3. Empty-catalog handling

If the scans in §2 find **no** project agents / commands / skills (e.g. a brand-new project, or a project that never used Claude Code primitives), do **not** invent entries to fill the template. Write empty tables and tag them `TODO: fill manually` in `planner-context.md` §1, §2, §3. In §9, keep only the `planner:product-baseline` row that ships with the template — that is a fact of the plugin, not invented project coverage. The planner will then operate with global-only catalog plus the gap-detection table from §4 of this reference, and the user can fill the project tables when they add their first project agent.

This rule preserves the legacy planner's empty-catalog behavior without inventing project capabilities.

## 4. Stack gap-detection — heuristic table

The agent catalog tells you who exists; the stack table tells you who **should** exist. After §2 scans complete, walk the project root looking for these markers. For each detected stack, check whether §1 of `planner-context.md` lists an agent that covers it. If not — that stack is a gap.

The stack table extends the legacy planner with explicit capability-gap detection.

| Stack key | Required markers (any one matches) | Common variants signal |
|---|---|---|
| `backend-python` | `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg`, `Pipfile` | `manage.py` → Django; `fastapi` in deps → FastAPI; `flask` in deps → Flask |
| `backend-node` | `package.json` (with backend deps like `express`, `nestjs`, `fastify`, `koa`), `tsconfig.json` (server-side) | `nest-cli.json` → NestJS; `next.config.*` and a `pages/api` or `app/api` dir → Next.js API |
| `frontend` | `package.json` with `react`, `vue`, `@angular/core`, `svelte`, `solid-js`; `index.html` at root or under `public/`; `vite.config.*`, `webpack.config.*` | `next.config.*` → Next.js; `nuxt.config.*` → Nuxt; `astro.config.*` → Astro |
| `mobile-android` | `android/` directory, `build.gradle`, `app/build.gradle`, `AndroidManifest.xml` | Kotlin (`*.kt`) vs Java; React-Native if `package.json` also present at root |
| `mobile-ios` | `ios/` directory, `*.xcodeproj`, `*.xcworkspace`, `Podfile` | SwiftUI signal: `*.swift` files; Objective-C: `*.m` / `*.h` |
| `infra` | `Dockerfile`, `docker-compose.y*ml`, `Makefile` (with deploy targets), `.github/workflows/`, `.gitlab-ci.yml`, `terraform/*.tf`, `kubernetes/*.yaml`, `helm/Chart.yaml` | Terraform vs k8s vs CI-only — record sub-marker |
| `backend-go` | `go.mod`, `go.sum`, `main.go` | `gin` / `echo` / `fiber` in `go.mod` |
| `backend-rust` | `Cargo.toml`, `Cargo.lock` | `actix` / `axum` / `rocket` signal |
| `data` | `dbt_project.yml`, `airflow/`, `dags/`, `*.ipynb` clusters, `notebooks/` | dbt vs Airflow vs Jupyter |

**Detection-order rule.** Run the checks in this order: **Python before Node before Frontend.** Frontend often coexists with a backend (a `package.json` may live next to `pyproject.toml`); detecting Python first prevents misclassifying a full-stack repo as a pure-frontend one. For a true monorepo with multiple stacks, list **all** detected stacks; gaps are flagged per-stack.

The table above is the minimum supported set. It is extensible — when a project repeatedly hits the unknown-stack path (§6), the user or a future re-scan can extend the table by adding rows.

## 5. Gap output format

When a stack is detected but no agent in §1 of `planner-context.md` covers it, emit a row in §1 with this exact shape:

```
❌ GAP (<stack>, <variant>) — fallback: general-purpose
```

Concrete examples:

- `❌ GAP (frontend, React) — fallback: general-purpose`
- `❌ GAP (mobile-android, Kotlin) — fallback: general-purpose`
- `❌ GAP (infra, terraform) — fallback: general-purpose`

This visible result lets the orchestrator route to the built-in `general-purpose` Task tool instead of choosing an unrelated agent or silently doing the work itself.

## 6. Unknown-stack handling

If the project has file markers that do not match **any** row in §4 — for example a Lisp project, a Nix flake, an esoteric DSL, or a research codebase with custom build tooling — do **not** force-fit it into a known stack and do **not** silently drop the markers. Instead:

1. Write the discovered markers verbatim into §8 of `planner-context.md` ("Unknown markers"). See `template-context.md` §3 for the §8 row format: `- <marker>: <discovered location> — TODO: assign stack`.
2. Tag the entry `unknown stack`.
3. In the chat summary that follows the bootstrap Write call, ask the user to either describe the stack in §6 of `planner-context.md` or extend the table in §4 of this reference for future runs.

This rule preserves unknown markers instead of forcing an unsupported classification.

## 7. Re-scan rules

When `planner-context.md` already exists and the user (or the planner skill) requests a re-scan, follow these rules verbatim — they protect manual edits, which are the project's institutional memory.

- **Manual edits are sources of truth.** If the user has edited `Когда звать` notes, refined the model table, added project-specific lessons in §6, etc. — the re-scan **does not** overwrite those cells. The planner adds rows; it never replaces user-curated cells.
- **Newly discovered entries.** If §2 finds an agent / skill / command that is not yet in `planner-context.md`, append a row tagged `<!-- auto-added YYYY-MM-DD -->` (use today's ISO date).
- **Missing-since-last-scan entries.** If a row in `planner-context.md` references an agent / skill / command that §2 no longer finds, do **not** delete the row. Tag it `<!-- stale, last seen YYYY-MM-DD -->`. The user decides whether the entity was renamed, moved, or genuinely removed; the row stays as evidence either way.
- **§9 rows.** Follow the capability-matrix rules of §2 step 5. Availability is the only §9 column a re-scan rewrites from its own results (`available` for found components, `not-surfaced` for missing ones); markers go inside the «Основание» cell, never on their own line inside the table. Hand-written rows (e.g. a `configured` pin) are never overwritten.

These rules preserve manual project knowledge across repeated scans. They are also documented in `template-context.md` §2.

## 8. Output

When all scans are complete, perform a single `Write` call to `<project-root>/.claude/planner-context.md` using the template from `template-context.md` §3. Fill the auto-discoverable fields (caught by §2 scans), write `❌ GAP` rows for stacks detected in §4 but not covered by an agent, write `## 8. Unknown markers` entries for anything caught by §6, and fill `## §9 Способности и поставщики` per §2 step 5.

After the `Write` succeeds, verify the §9 machine contract once:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/product-discovery/assets/product_state.py" \
  parse-capabilities <project-root>/.claude/planner-context.md
```

Exit `0` — proceed. Exit `3` — the table violates the format; fix the table in `planner-context.md` (header, column order, closed values), never the helper. Then return control to the planner skill workflow (`SKILL.md` "Workflow", step 3 onward). Do **not** continue planning inside the bootstrap reference — that is the skill's job, not bootstrap's. The bootstrap step ends with a fresh `planner-context.md` and a one-line confirmation: "bootstrap done, ready to plan".

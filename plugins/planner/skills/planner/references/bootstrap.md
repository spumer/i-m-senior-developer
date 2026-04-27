# Bootstrap — project-specific context for planner

This is the on-demand procedure that populates `<project-root>/.claude/planner-context.md` for the first time, plus the rules for re-scanning later. It is intentionally **not** in `SKILL.md`: bootstrap runs once per project (or on explicit re-scan), and inlining its details on every planner activation would bloat context.

## 1. When to load

Load this reference when `SKILL.md` ("Bootstrap pointer") routes here — i.e. when `<project-root>/.claude/planner-context.md` is missing, when the user explicitly asks for a re-scan, or when the file's `## 7. Метаданные bootstrap` section is older than the project's most recent agent/skill/command edits and needs refreshing.

## 2. Scanning algorithm

Run the four scans below in order. Use `Glob` for path matching and `Read` for frontmatter. Treat every result as **evidence** (FPF A.10) — do not invent agents, commands, or skills that the file system does not show.

1. **Agents.**
   - `Glob` `.claude/agents/*.md` (project-local agents).
   - `Glob` `~/.claude/agents/*.md` (global agents).
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

## 3. Empty-catalog handling

If the scans in §2 find **no** project agents / commands / skills (e.g. a brand-new project, or a project that never used Claude Code primitives), do **not** invent entries to fill the template. Write empty tables and tag them `TODO: fill manually` in `planner-context.md` §1, §2, §3. The planner will then operate with global-only catalog plus the gap-detection table from §4 of this reference, and the user can fill the project tables when they add their first project agent.

This rule comes from legacy `~/.claude/agents/planner.md` lines 99-101 and FEAT-0001 README edge-case row 1.

## 4. Stack gap-detection — heuristic table

The agent catalog tells you who exists; the stack table tells you who **should** exist. After §2 scans complete, walk the project root looking for these markers. For each detected stack, check whether §1 of `planner-context.md` lists an agent that covers it. If not — that stack is a gap.

The stack table is the FEAT-0001 P1 capability (per README §27). It is **new content**: the legacy planner did not have it.

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

The table above is the minimum (FEAT-0001 README §87 mandates 6+ base stacks). It is extensible — when a project repeatedly hits the unknown-stack path (§6), the user or a future re-scan can extend the table by adding rows.

## 5. Gap output format

When a stack is detected but no agent in §1 of `planner-context.md` covers it, emit a row in §1 with this exact shape:

```
❌ GAP (<stack>, <variant>) — fallback: general-purpose
```

Concrete examples:

- `❌ GAP (frontend, React) — fallback: general-purpose`
- `❌ GAP (mobile-android, Kotlin) — fallback: general-purpose`
- `❌ GAP (infra, terraform) — fallback: general-purpose`

This is the visible signal that lets the orchestrator route to the built-in `general-purpose` Task tool instead of "creatively picking" a wrong agent or sliding into DIY mode (the fail-mode the whole feature was designed to fix — see FEAT-0001 README Problem Statement). The format aligns with FEAT-0001 README §27 + §130.

## 6. Unknown-stack handling

If the project has file markers that do not match **any** row in §4 — for example a Lisp project, a Nix flake, an esoteric DSL, or a research codebase with custom build tooling — do **not** force-fit it into a known stack and do **not** silently drop the markers. Instead:

1. Write the discovered markers verbatim into §8 of `planner-context.md` ("Unknown markers"). See `template-context.md` §3 for the §8 row format: `- <marker>: <discovered location> — TODO: assign stack`.
2. Tag the entry `unknown stack`.
3. In the chat summary that follows the bootstrap Write call, ask the user to either describe the stack in §6 of `planner-context.md` or extend the table in §4 of this reference for future runs.

This rule comes from FEAT-0001 README edge-case row 2 + §61.

## 7. Re-scan rules

When `planner-context.md` already exists and the user (or the planner skill) requests a re-scan, follow these rules verbatim — they protect manual edits, which are the project's institutional memory.

- **Manual edits are sources of truth.** If the user has edited `Когда звать` notes, refined the model table, added project-specific lessons in §6, etc. — the re-scan **does not** overwrite those cells. The planner adds rows; it never replaces user-curated cells.
- **Newly discovered entries.** If §2 finds an agent / skill / command that is not yet in `planner-context.md`, append a row tagged `<!-- auto-added YYYY-MM-DD -->` (use today's ISO date).
- **Missing-since-last-scan entries.** If a row in `planner-context.md` references an agent / skill / command that §2 no longer finds, do **not** delete the row. Tag it `<!-- stale, last seen YYYY-MM-DD -->`. The user decides whether the entity was renamed, moved, or genuinely removed; the row stays as evidence either way.

These rules come from legacy `~/.claude/agents/planner.md` lines 109-113 plus FEAT-0001 README edge-case rows 3-4. They are also documented in `template-context.md` §2.

## 8. Output

When all scans are complete, perform a single `Write` call to `<project-root>/.claude/planner-context.md` using the template from `template-context.md` §3. Fill the auto-discoverable fields (caught by §2 scans), write `❌ GAP` rows for stacks detected in §4 but not covered by an agent, and write `## 8. Unknown markers` entries for anything caught by §6.

After the `Write` succeeds, return control to the planner skill workflow (`SKILL.md` "Workflow", step 3 onward). Do **not** continue planning inside the bootstrap reference — that is the skill's job, not bootstrap's. The bootstrap step ends with a fresh `planner-context.md` and a one-line confirmation: "bootstrap done, ready to plan".

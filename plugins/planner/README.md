# planner

Claude Code plugin: end-to-end feature pipeline. Replaces the legacy `~/.claude/agents/planner.md` meta-dispatcher and the legacy `~/.claude/commands/plan-{feat,do,jira}.md` command set. Adds project-aware bootstrap with agent-catalog gap detection, two planning modes (architecture and execution), cost-aware parallel-phase grouping, and a `/plan-reflect` learning loop that updates `planner-context.md` after each session.

## What it does

- **Requirements gathering** — `/plan-feat` and `/plan-jira` facilitate user-journey + DoD discovery; output a `features/FEAT-XXXX/README.md` (or a Jira-Markdown brief)
- **Bootstrap** — scans agents, slash-commands, skills, and stack markers in the project; flags gaps where a stack is detected but no agent covers it; writes `planner-context.md`
- **Architecture mode** (`/plan` on a feature `README.md`) — picks among single Opus architect, N parallel Sonnet sub-architects, Haiku quick-pass, or a separate security sub-plan
- **Execution mode** (`/plan` on an existing `*-PLAN-*.md`) — turns the architecture document into a dependency graph with parallel phases (≤7 agents per phase) and per-stage model selection
- **Implementation orchestration** (`/plan-do`) — runs the architect → implementer → reviewer → keeper pipeline, looping until reviewer is clean
- **Cost estimation** — tokens, wall-clock, and relative $-cost vs naive `/plan-do`
- **Post-task learning** (`/plan-reflect`) — compares plan vs reality, extracts lessons, writes them back into `planner-context.md` (gap-fills, model-strength signals, user-correction patterns, cost-calibration deltas)
- `planner-context.md` is the project source of truth — manual edits are preserved across re-scans

## Structure

```
plugins/planner/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── planner.md                           # thin wrapper (~30 lines)
├── skills/
│   ├── planner/
│   │   ├── SKILL.md                         # core workflow
│   │   └── references/
│   │       ├── bootstrap.md                 # scan + gap-detection
│   │       ├── architecture-mode.md         # Mode 1 detail
│   │       ├── execution-mode.md            # Mode 2 detail
│   │       └── template-context.md          # planner-context.md template
│   └── planner-reflect/
│       └── SKILL.md                         # post-task learning
├── commands/
│   ├── plan-feat.md                        # requirements gathering → README.md
│   ├── plan-jira.md                        # requirements gathering → Jira brief
│   ├── plan.md                             # architecture / execution planning
│   ├── plan-do.md                          # implementation orchestration
│   └── plan-reflect.md                     # post-task learning
├── hooks/
│   └── README.md                            # opt-in placeholder
└── README.md
```

## Installation

Add this marketplace to your Claude Code config and install the plugin from `i-m-senior-developer`:

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install planner@i-m-senior-developer
```

## Migration from legacy `planner.md` and `plan-*` commands

If you used the legacy `~/.claude/agents/planner.md` (290-line agent) and/or the legacy `~/.claude/commands/plan-{feat,do,jira}.md` files, follow this migration:

```
# 1. Install plugin from marketplace (after publication)

# 2. Remove legacy agent
rm -f ~/.claude/agents/planner.md
rm -f <project>/.claude/agents/planner.md  # if present

# 3. Remove legacy commands (now shipped by the plugin)
rm -f ~/.claude/commands/plan-feat.md
rm -f ~/.claude/commands/plan-do.md
rm -f ~/.claude/commands/plan-jira.md

# 4. Verify project planner-context.md isn't broken
#    (plugin will offer to update structure on first run)

# 5. Run /plan on any feature — bootstrap should pass cleanly
```

Sanity checks after migration:

1. Confirm `~/.claude/agents/planner.md` is gone
2. Confirm `~/.claude/commands/plan-{feat,do,jira}.md` are gone
3. Confirm `/plan`, `/plan-do`, `/plan-feat`, `/plan-jira`, `/plan-reflect` resolve to the plugin in `/help` (look for `(plugin:planner)` label)
4. Run `/plan` on any feature to trigger fresh bootstrap

For full transcript-based learning, run `/plan-reflect` **in the same session** as the work it reflects on — cross-session transcript availability is not guaranteed in v0.2.0.

## Modes

- **Architecture mode** — input is a feature `README.md`, output is a `PLANNER_OUTPUT.md` describing how to run the architectural pass (one architect vs parallel sub-architects vs quick-pass). Example: `/plan features/FEAT-0042-billing/`.
- **Execution mode** — input is an existing `FEAT-XXXX-PLAN-0N.md`, output is a dependency-graph + parallel-phase plan with cost estimate. Example: `/plan features/FEAT-0042-billing/FEAT-0042-PLAN-01.md`.

Detail lives in the skill references — `skills/planner/references/architecture-mode.md` and `skills/planner/references/execution-mode.md`.

## Examples

**First-time bootstrap in a new project:**

```
/plan refactor billing module
```
→ Plugin scans `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, detects stack markers, writes `<project>/.claude/planner-context.md`, then builds the plan.

**Architecture planning from a feature README:**

```
/plan features/FEAT-0042-billing/
```
→ Reads `features/FEAT-0042-billing/README.md`, picks an architecture option (single Opus / parallel Sonnet / Haiku quick-pass), writes `PLANNER_OUTPUT.md` next to it.

**Post-session reflection:**

```
/plan-reflect features/FEAT-0042-billing/
```
→ Compares `PLANNER_OUTPUT.md` against `git log`, review files, and session messages; writes lessons into `planner-context.md` and emits a "Lessons learned" section in chat.

## Commands

The plugin ships five commands, covering the full feature pipeline:

| Command | Stage | Purpose |
|---|---|---|
| `/plan-feat` (or `/planner:plan-feat`) | requirements | Facilitate user-journey + DoD discovery; output `features/FEAT-XXXX-<slug>/README.md` |
| `/plan-jira` (or `/planner:plan-jira`) | requirements | Same facilitation, output a Jira-Markdown brief instead of a feature directory |
| `/plan` (or `/planner:plan`) | planning | Build an architecture or execution plan; activates the `planner` skill |
| `/plan-do` (or `/planner:plan-do`) | implementation | Orchestrate the architect → implementer → reviewer → keeper pipeline |
| `/plan-reflect` (or `/planner:plan-reflect`) | learning | Compare plan vs reality; update `planner-context.md` |

The bare forms work by default. The namespaced `planner:` forms are the disambiguation fallback if you have your own collision — Claude Code shows them in `/help` automatically.

**Typical pipeline:**

```
/plan-feat "bookmarks for items"
        ↓ (writes features/FEAT-0001-bookmarks/README.md)
/plan features/FEAT-0001-bookmarks/
        ↓ (writes PLANNER_OUTPUT.md)
/plan-do features/FEAT-0001-bookmarks/
        ↓ (orchestrates implementation, writes PLAN/review/test artifacts)
/plan-reflect features/FEAT-0001-bookmarks/
        ↓ (writes lessons into planner-context.md)
```

## Configuration

Project-specific configuration lives in `<project>/.claude/planner-context.md`. The file is created on first bootstrap and contains the project's agent catalog, slash-command catalog, skill catalog, model table, feature-directory conventions, and naming rules. Manual edits are preserved on re-scan — the plugin only adds new auto-discovered rows (tagged `<!-- auto-added YYYY-MM-DD -->`) and marks missing-since-last-scan rows as stale instead of deleting them.

## Requirements

- Claude Code with plugin marketplaces support

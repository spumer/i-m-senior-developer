# planner

Claude Code plugin for file-backed feature planning and implementation orchestration.

It separates three artifacts:

- `README.md` — requirements and user-visible behavior;
- `ARCHITECTURE.md` — ready technical design;
- `PLANNER_EXECUTION.md` — implementation phases tied to one architecture version.

The full planning result lives in a file. A successful `/plan` prints only the path, version, and two to four main outcomes.

## What it does

- **Requirements gathering** — `/plan-feat` and `/plan-jira` facilitate user journey and Definition of Done discovery.
- **Project bootstrap** — scans available agents, commands, skills, stack markers, and feature-directory conventions into `.claude/planner-context.md`.
- **Architecture mode** — `/plan` on a feature README or free-text task writes a complete `ARCHITECTURE.md`.
- **Execution mode** — `/plan` on architecture writes a separate `PLANNER_EXECUTION.md` with phases, dependencies, models, and review gates.
- **Freshness guard** — architecture and execution plans carry versions and SHA-256 body fingerprints. Direct architecture edits make the execution plan stale even when its visible version was not updated manually.
- **Implementation orchestration** — `/plan-do` checks freshness before any agent, then runs implementation and review phases until clean.
- **Post-task learning** — `/plan-reflect` writes stable lessons back to `.claude/planner-context.md`.

## Structure

```text
plugins/planner/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── planner.md
├── commands/
│   ├── plan-feat.md
│   ├── plan-jira.md
│   ├── plan.md
│   ├── plan-do.md
│   └── plan-reflect.md
├── skills/
│   ├── planner/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   ├── plan_state.py
│   │   │   └── test_plan_state.py
│   │   └── references/
│   │       ├── bootstrap.md
│   │       ├── architecture-mode.md
│   │       ├── execution-mode.md
│   │       └── template-context.md
│   └── planner-reflect/
│       └── SKILL.md
└── README.md
```

## Installation

Add this marketplace to Claude Code and install the plugin:

```text
/plugin marketplace add spumer/i-m-senior-developer
/plugin install planner@i-m-senior-developer
```

## Typical feature flow

```text
/plan-feat "bookmarks for items"
        ↓ writes features/example/README.md
/plan features/example/README.md
        ↓ writes features/example/ARCHITECTURE.md
/plan features/example/ARCHITECTURE.md
        ↓ writes features/example/PLANNER_EXECUTION.md
/plan-do features/example/
        ↓ checks freshness, implements, reviews, updates documentation
/plan-reflect features/example/
        ↓ records stable lessons in planner-context.md
```

The namespaced forms (`/planner:plan`, `/planner:plan-do`, and others) are available when a local command has the same bare name.

## Planning modes

### Architecture

Inputs:

- feature `README.md`;
- feature directory containing `README.md`;
- free-text task with no filesystem path.

Outputs:

- feature input → `ARCHITECTURE.md` beside the README;
- free text → `.claude/plans/<task-slug>/ARCHITECTURE.md`.

Architecture mode writes the complete design. It does not leave a separate file of instructions for a future architect run.

### Execution

Input: an existing architecture document, including an explicitly supplied legacy `*-PLAN-*.md` or `*-DESIGN-*.md`.

Output: `PLANNER_EXECUTION.md` beside the architecture.

The execution header records:

- its own version and status;
- its own body fingerprint;
- the architecture path, version, and body fingerprint.

## Freshness and versions

New architecture:

```yaml
---
plan_type: architecture
version: 1
status: current
content_sha256: <body fingerprint>
---
```

New execution plan:

```yaml
---
plan_type: execution
version: 1
status: current
content_sha256: <body fingerprint>
architecture:
  path: "./ARCHITECTURE.md"
  version: 1
  content_sha256: <architecture body fingerprint>
---
```

Rules:

- a semantic body change increments that document's version;
- wording or formatting without a semantic change preserves the version;
- changing only `current` to `stale` preserves the execution version and body;
- architecture without supported frontmatter is read as version 0 and is not rewritten merely for migration;
- direct body changes are detected by the fingerprint;
- Git owns history, so the plugin rewrites current files instead of creating numbered copies.

## `/plan-do` guard

`/plan-do` runs the state helper before every Agent call. It stops when:

- the execution file is missing or invalid;
- the architecture path is missing or invalid;
- recorded and current architecture versions differ;
- the architecture fingerprint differs;
- the execution plan is already marked `stale`.

The guard cannot be bypassed by confirmation. Rebuild the plan with:

```text
/plan <path-to-current-architecture>
```

## Chat output

After a successful write, `/plan` prints only:

- result kind;
- path and version;
- two to four main outcomes;
- next command, when needed.

If writing or metadata synchronization fails, the command says the file was not saved and returns the complete prepared document in chat as a fallback.

## Legacy `PLANNER_OUTPUT.md`

An existing `PLANNER_OUTPUT.md` is preserved. New planner runs do not delete it and do not treat it as the current architecture or execution plan.

## Commands

| Command | Purpose |
|---|---|
| `/plan-feat` | Gather requirements and write a feature README |
| `/plan-jira` | Gather requirements from a Jira description |
| `/plan` | Write architecture or execution planning to a file |
| `/plan-do` | Check freshness, implement, review, and document |
| `/plan-reflect` | Record stable project-specific lessons |

## Configuration

Project-specific agent mappings, model guidance, and artifact paths live in `.claude/planner-context.md`. Bootstrap creates it on first use. A rescan appends auto-discovered entries and marks missing entries stale without overwriting manual decisions.
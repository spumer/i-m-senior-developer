# sdlc

Claude Code plugin: full SDLC pipeline for feature development. Replaces the legacy `~/.claude/agents/python-implementer.md`, `django-architect.md`, and `code-reviewer.md` with 3 namespaced, distributable, stack-aware agents. Instead of duplicating TDD workflow and Functional Clarity principles, the plugin integrates with `tdd-master` and `functional-clarity` by reference — keeping each agent lean and the overall system DRY. Works as a standalone pipeline or as the execution layer under `/plan-do` from the `planner` plugin.

Роль плагина в системе, границы трёх ролей и случаи, когда их лучше не звать:
[`docs/plugins/sdlc.md`](../../docs/plugins/sdlc.md).

## What it does

- **`sdlc:architect`** — designs systems: bounded contexts, data flow, contracts, hand-off documents. Model: opus. Never writes implementation code.
- **`sdlc:code-implementer`** — implements code per an architecture document using TDD (delegates to `tdd-master:tdd-master` for RED-GREEN-REFACTOR). Model: sonnet.
- **`sdlc:code-reviewer`** — reviews code changes for security (OWASP Top 10 always active), system issues, and FPF/Functional Clarity violations. Model: sonnet.
- **Stack-aware references** — backend-python, frontend-react, and api-design references load on demand per detected stack; skills degrade gracefully to universal principles for unknown stacks.
- **TDD enforced** — `sdlc:code-implementer` activates `tdd-master:tdd-master` before writing any production code (RED phase is mandatory).
- **FPF principles enforced** — `functional-clarity:functional-clarity` is referenced in both implementer and reviewer skills.
- **Visual design** — `document-skills:frontend-design` available for frontend deliverables via graceful integration.
- **Orchestration-ready** — `/plan-do` (from the `planner` plugin) fills its abstract roles — implementer, reviewer, architect, documentation keeper — from `.claude/planner-context.md`; these three agents are what fills the first three. `/plan-do` does not hardcode them.

## What it is NOT for

- **Not an orchestrator.** The plugin ships no command and no hook, so it never
  runs the design → implement → review sequence by itself. A human or `/plan-do`
  supplies the order.
- **Not a planning layer.** Requirements, roadmap, and slice scope belong to
  `planner`; the architect starts from a written slice, not from a raw idea.
- **Not for a one-line fix.** Three role hand-offs cost more than a typo is
  worth. Use the roles when the change has a contract, a boundary, or a
  security surface.
- **Not a substitute for running the tests.** The reviewer reads the diff; the
  implementer runs the suite and reports the exact commands.

## Structure

```
plugins/sdlc/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── architect.md                    # thin wrapper, model=opus
│   ├── code-implementer.md             # thin wrapper, model=sonnet
│   └── code-reviewer.md               # thin wrapper, model=sonnet
├── skills/
│   ├── architect/
│   │   ├── SKILL.md                    # design-only core
│   │   └── references/
│   │       ├── backend-python.md       # design angle: frameworks, bounded contexts
│   │       ├── frontend-react.md       # design angle: component contracts, data flow
│   │       └── api-design.md           # REST/GraphQL/OpenAPI design
│   ├── code-implementer/
│   │   ├── SKILL.md                    # implement core, TDD pointer
│   │   └── references/
│   │       ├── backend-python.md       # implement angle: ORM, pytest, mypy
│   │       └── frontend-react.md       # implement angle: vitest, RTL, hooks
│   └── code-reviewer/
│       ├── SKILL.md                    # review core, OWASP + FPF
│       └── references/
│           ├── security.md             # OWASP Top 10, always active
│           ├── backend-python.md       # review angle: n+1, ORM pitfalls, transactions
│           └── frontend-react.md       # review angle: XSS, a11y, hooks pitfalls
└── README.md
```

## Installation

Add this marketplace to your Claude Code config and install the plugin from `i-m-senior-developer`:

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install sdlc@i-m-senior-developer
```

## Migration from legacy agents

If you have legacy `~/.claude/agents/python-implementer.md`, `django-architect.md`, or `code-reviewer.md`, follow these steps. **Read all steps before running any `rm` command.**

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
#    Option B (automatic): run `/plan-reflect` in a session with PLANNER_EXECUTION.md
#                          present — the planner-reflect skill detects the catalog change
#                          and appends auto-added rows. Manually edited cells are preserved.

# 6. Smoke test
#    Run `/plan-do features/<any-feature>/` on a feature that already has a current
#    PLANNER_EXECUTION.md — the phase should dispatch sdlc:code-implementer, then
#    sdlc:code-reviewer, under the role names from planner-context.md.

# 7. Cleanup backups (after verification — at least one full session)
rm -f ~/.claude/agents/*.backup
```

Sanity checks after migration:

- Confirm `~/.claude/agents/python-implementer.md` is gone.
- Confirm `~/.claude/agents/django-architect.md` is gone.
- Confirm `~/.claude/agents/code-reviewer.md` is gone.
- Confirm `/help` shows `(plugin:sdlc)` label next to architect, code-implementer, code-reviewer.
- Confirm in any project's `planner-context.md` §1 the new rows exist (or the old rows are tagged `<!-- stale, last seen YYYY-MM-DD -->` after `/plan-reflect`).

## Agents

| Agent | Namespaced form | Model | Role |
|---|---|---|---|
| `architect` | `sdlc:architect` | opus | Designs systems: bounded contexts, data flow, contracts. Produces architecture documents. Never writes code. |
| `code-implementer` | `sdlc:code-implementer` | sonnet | Implements code per an architecture document. TDD-first via `tdd-master:tdd-master`. |
| `code-reviewer` | `sdlc:code-reviewer` | sonnet | Reviews code changes: security (OWASP always active), system issues, FPF violations. Never modifies code. |

## Skills

| Skill | Activation triggers | On-demand references |
|---|---|---|
| `sdlc:architect` | "спроектируй", "архитектура", "design this feature", "как разбить модули", "где границы", README фичи + ARCH-документ нужен | `references/backend-python.md` (design angle), `references/frontend-react.md` (design angle), `references/api-design.md` |
| `sdlc:code-implementer` | "реализуй", "закодь", "implement this", "add the endpoint", ARCH/PLAN-документ готов | `references/backend-python.md` (implement angle), `references/frontend-react.md` (implement angle); always activates `tdd-master:tdd-master` |
| `sdlc:code-reviewer` | "отревью", "проверь код", "review this PR", "есть ли security-проблемы", после implementer-фазы | `references/security.md` (always active), `references/backend-python.md` (review angle), `references/frontend-react.md` (review angle) |

## Integration with other plugins

- **`tdd-master`** — `sdlc:code-implementer` activates `tdd-master:tdd-master` before writing any production code; the RED-GREEN-REFACTOR workflow is owned by `tdd-master`, not duplicated here.
- **`functional-clarity`** — `sdlc:code-implementer` and `sdlc:code-reviewer` reference `functional-clarity:functional-clarity` for FPF/Error Hiding checks and parsimony rules.
- **`planner`** — `/plan-do` (from `planner`) orchestrates by role, not by plugin name. It reads the role table in `.claude/planner-context.md`, dispatches the named implementer, then the named reviewer, and loops until review is clean. The architect is dispatched only when the reviewer reports a design defect — and after that update `/plan-do` stops, because the execution plan must be rebuilt against the new architecture version.
- **`document-skills:frontend-design`** — graceful integration across the pipeline: `sdlc:architect` names the design system in the architecture document, `sdlc:code-implementer` activates it for visual quality during component implementation, `sdlc:code-reviewer` references it for visual/UX review of frontend changes. All three skills degrade gracefully when this plugin is not installed.

## Examples

**Architecture pass from written slice requirements:**

```
/plan features/FEAT-0042-billing/README.md
```
→ the `planner` skill produces `features/FEAT-0042-billing/ARCHITECTURE.md` with a version and a body fingerprint. Invoke `sdlc:architect` directly instead when there is no planner in the project; it then writes the architecture document under the project's own naming convention.

**Backend implementation with TDD:**

```
Архитектура готова. Реализуй фичу.
```
→ Activates `sdlc:code-implementer`, which calls `tdd-master:tdd-master` for RED phase, then loads `references/backend-python.md` (ORM patterns, pytest fixtures, mypy config).

**Security-focused code review:**

```
Закончил имплементацию FEAT-0042. Отревью с акцентом на безопасность.
```
→ Activates `sdlc:code-reviewer`, which auto-loads `references/security.md` (OWASP Top 10) and `references/backend-python.md` (n+1, ORM pitfalls, transaction boundaries).

## Requirements

- Claude Code with plugin marketplaces support.
- Recommended companions (sdlc works without them but with reduced features):
  - `tdd-master` — required for full RED-GREEN-REFACTOR in code-implementer.
  - `functional-clarity` — required for FPF/Error Hiding checks in code-implementer and code-reviewer.
  - `planner` — required for `/plan-do` pipeline orchestration.

## Versioning

This plugin starts at `0.1.0`. Any change to any file under `plugins/sdlc/` — including skill references, agent wrappers, or this README — requires a semver bump in `.claude-plugin/plugin.json` per the repo CLAUDE.md rule. Use PATCH for fixes and prompt tweaks, MINOR for new agents/skills/references, MAJOR for breaking changes (removed agents, renamed skills, changed output format).

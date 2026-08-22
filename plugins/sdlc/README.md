# sdlc

Three-role SDLC plugin: architect, code-implementer, code-reviewer. This file
answers how the plugin is structured in the repository and how to migrate from
the legacy agents. The contract — what each role does, hand-offs between roles,
stack references, boundaries — lives on
[`docs/plugins/sdlc.md`](../../docs/plugins/sdlc.md).

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

Add this marketplace to your Claude Code config and install the plugin:

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install sdlc@i-m-senior-developer
```

Dependencies on `tdd-master` and `functional-clarity` are declared in the
manifest and pulled in by the installation itself.

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

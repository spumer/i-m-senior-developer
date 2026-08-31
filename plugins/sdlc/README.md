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
│   └── code-reviewer.md                # thin wrapper, model=sonnet
├── skills/
│   ├── architect/
│   │   ├── SKILL.md                    # design-only core
│   │   └── references/
│   │       ├── backend-python.md       # design angle: frameworks, bounded contexts
│   │       ├── frontend-react.md       # design angle: component contracts, data flow
│   │       ├── api-design.md           # REST/GraphQL/OpenAPI design
│   │       └── design-conventions.md   # gotcha detail, may/must-not lists
│   ├── code-implementer/
│   │   ├── SKILL.md                    # implement core, TDD pointer
│   │   └── references/
│   │       ├── backend-python.md       # implement angle: ORM, pytest, mypy
│   │       └── frontend-react.md       # implement angle: vitest, RTL, hooks
│   └── code-reviewer/
│       ├── SKILL.md                    # review core, OWASP + FPF
│       └── references/
│           ├── security.md             # OWASP Top 10
│           ├── backend-python.md       # review angle: n+1, ORM pitfalls, transactions
│           ├── frontend-react.md       # review angle: XSS, a11y, hooks pitfalls
│           └── review-conventions.md   # gotcha detail, worked finding examples
└── README.md
```

Every reference above is loaded on demand — the skill text decides when to read
one. The one exception: the reviewer skill tells the model to load `security.md`
first on every activation regardless of stack. That is carried by the skill
text.

## Installation

Add this marketplace to your Claude Code config and install the plugin:

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install sdlc@i-m-senior-developer
```

Update, verification, and troubleshooting are the same for every plugin here —
see [`docs/install.md`](../../docs/install.md).

`tdd-master` and `functional-clarity` are declared in the `dependencies` field
of `.claude-plugin/plugin.json`, and the installation pulls them in.

## Migration from legacy agents

If you have legacy `~/.claude/agents/python-implementer.md`, `django-architect.md`, or `code-reviewer.md`, follow these steps. **Read all steps before running any `rm` command.**

```bash
# 1. BACKUP first — these files are deleted below, so copy anything you edited
#    locally (custom triggers, project-specific tweaks, lessons-learned notes)
for legacy in python-implementer django-architect code-reviewer; do
  [ -f ~/.claude/agents/$legacy.md ] && \
    cp ~/.claude/agents/$legacy.md ~/.claude/agents/$legacy.md.backup
done

# 2. Install plugin from marketplace (see Installation above)

# 3. Remove legacy agents
rm -f ~/.claude/agents/python-implementer.md
rm -f ~/.claude/agents/django-architect.md
rm -f ~/.claude/agents/code-reviewer.md

# 4. Verify the namespace collision is resolved
#    `code-reviewer` exists as `sdlc:code-reviewer` once the legacy file is gone.
#    Run `/agents` — it lists agents with their source; a plugin-supplied
#    agent is labelled `Plugin`. (`/help` lists commands, not agents.)

# 5. Update the agent catalog in each project's planner-context.md by hand:
#    replace rows for python-implementer / django-architect / code-reviewer
#    with sdlc:architect / sdlc:code-implementer / sdlc:code-reviewer.

# 6. Smoke test
#    Run `/plan-do features/<any-feature>/` on a feature that already has a current
#    PLANNER_EXECUTION.md — the phase should dispatch sdlc:code-implementer, then
#    sdlc:code-reviewer, under the role names from planner-context.md.

# 7. Cleanup backups (after verification — at least one full session)
rm -f ~/.claude/agents/*.backup
```

Editing the agent catalog by hand is the only path. `/plan-reflect` appends
lesson lines about a completed run; it does not rewrite catalog rows.

Sanity checks after migration:

- Confirm `~/.claude/agents/python-implementer.md` is gone.
- Confirm `~/.claude/agents/django-architect.md` is gone.
- Confirm `~/.claude/agents/code-reviewer.md` is gone.
- Confirm `/agents` lists architect, code-implementer, and code-reviewer with `Plugin` as their source.
- Confirm the agent catalog in each project's `planner-context.md` has the new rows and no longer names a legacy agent.

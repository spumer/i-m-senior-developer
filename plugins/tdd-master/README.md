# tdd-master

Claude Code plugin for Test-Driven Development methodology. This file answers
how the plugin is structured in the repository. The contract — what it does,
its two agent modes, what the cycle forbids — lives on
[`docs/plugins/tdd-master.md`](../../docs/plugins/tdd-master.md).

## Structure

```
plugins/tdd-master/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── agents/
│   └── tdd-master.md            # TDD agent (subagent for test writing)
├── hooks/
│   ├── hooks.json               # Hook configuration
│   └── session-start.sh         # Injects TDD context at session start
└── skills/
    └── tdd-master/
        ├── SKILL.md             # Skill definition with trigger phrases
        └── references/
            ├── TDD_GUIDE.md           # Core TDD methodology (always loaded)
            ├── P0_DEFAULT_CONTEXT.md  # Context-adaptive defaults (always loaded)
            └── frameworks/
                ├── pytest.md          # Pytest patterns (conditional)
                └── django.md          # Django patterns (conditional)
```

## Installation

Add this marketplace to Claude Code and install the plugin:

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install tdd-master@i-m-senior-developer
```

Works standalone; no dependencies on other plugins in this marketplace.

# tdd-master

Claude Code plugin for Test-Driven Development methodology. This file answers
how the plugin is structured in the repository. The contract — what it does,
what the agent does, what the cycle forbids — lives on
[`docs/plugins/tdd-master.md`](../../docs/plugins/tdd-master.md).

## Structure

```
plugins/tdd-master/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── agents/
│   └── tdd-master.md            # TDD agent, whole cycle; no `tools:` field
├── hooks/
│   ├── hooks.json               # SessionStart, one command hook
│   └── session-start.sh         # Prints the TDD rule text at session start
└── skills/
    └── tdd-master/
        ├── SKILL.md             # Skill definition with trigger phrases
        └── references/
            ├── TDD_GUIDE.md           # Core TDD methodology (read always)
            ├── P0_DEFAULT_CONTEXT.md  # Context-adaptive defaults (read always)
            └── frameworks/
                ├── pytest.md          # Pytest patterns (read when pytest detected)
                └── django.md          # Django patterns (read when Django detected)
```

## Installation

Add this marketplace to Claude Code and install the plugin:

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install tdd-master@i-m-senior-developer
```

Works standalone: the manifest declares no `dependencies`. The reverse link
exists — `plugins/sdlc` lists `tdd-master` among its dependencies.

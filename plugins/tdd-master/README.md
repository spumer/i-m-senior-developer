# tdd-master

Claude Code plugin for Test-Driven Development methodology based on Kent Beck and Uncle Bob principles.

## What it does

- Guides agents through Red-Green-Refactor cycle
- Automatically detects project frameworks (pytest, Django) and loads relevant patterns
- Provides reference documentation for TDD methodology, fixture defaults, and testing patterns
- Integrates with development workflow: tests are written BEFORE implementation

## Structure

```
tdd-master-plugin/
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

Add the plugin path to your project's `.claude/settings.json`:

```json
{
  "plugins": ["./tdd-master-plugin"]
}
```

## How it works

1. **SessionStart hook** — injects TDD workflow reminder into every new session
2. **Skill activation** — triggers when user asks to write tests, implement features, fix bugs, or mentions TDD
3. **Framework detection** — analyzes `pyproject.toml`, `conftest.py`, `manage.py` to determine pytest/Django usage
4. **Reference loading** — always loads TDD_GUIDE + P0_DEFAULT_CONTEXT, conditionally loads framework-specific patterns
5. **Agent execution** — tdd-master agent writes failing tests first, then minimal implementation, then refactors

## Integration

This plugin works standalone. Other agents in your project can call tdd-master to write tests before implementation or verify TDD compliance during reviews.

## Requirements

- Claude Code CLI
- Python project with pytest (recommended)
- Django (optional, for Django-specific patterns)

# llms-keeper

This file answers how the plugin is structured in the repository: which
components ship and where they live. The contract — what the plugin does, how
to use it, when not to — lives on
[`docs/plugins/llms-keeper.md`](../../docs/plugins/llms-keeper.md).

## What it ships

- **`/update-docs`** — `commands/update-docs.md`; generate or refresh both
  context files.
- **`llms-keeper` skill** — `skills/llms-keeper/`; the format rules and what
  belongs in each file.
- **`documentation-keeper` agent** — `agents/documentation-keeper.md`; reads
  source, config, tests, CI and docs, then writes the two files.
- **SessionStart hook** — `hooks/`; reports whether context files exist and
  suggests the command when they do not.

## Installation

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install llms-keeper@i-m-senior-developer
```

No dependencies on other plugins in this marketplace.

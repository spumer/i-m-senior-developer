# llms-keeper

This file answers how the plugin is structured in the repository: which
components ship and where they live. The contract — what the plugin does, how
to use it, when not to — lives on
[`docs/plugins/llms-keeper.md`](../../docs/plugins/llms-keeper.md).

## What it ships

Three prompts and one shell script. The files are written by a model following
the agent prompt; the hook is the only executable part.

- **`/update-docs`** — `commands/update-docs.md`; asks the model to call the
  `documentation-keeper` agent and passes the focus-area argument through.
- **`llms-keeper` skill** — `skills/llms-keeper/`; format rules, what belongs in
  each file, and `references/llmstxt-spec.md` for the spec details. Hands the
  work to the same agent.
- **`documentation-keeper` agent** — `agents/documentation-keeper.md`; the
  instruction to detect the stack from manifest files, read entry points, core
  modules, config, test structure, docs and CI, then write both files.
- **SessionStart hook** — `hooks/hooks.json` plus `hooks/session-start.sh`;
  prints one of three messages depending on which context file it finds in the
  working directory, recommends `/update-docs` in each of them, exits `0`.

## Installation

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install llms-keeper@i-m-senior-developer
```

`.claude-plugin/plugin.json` declares no `dependencies`, so the plugin loads on
its own.
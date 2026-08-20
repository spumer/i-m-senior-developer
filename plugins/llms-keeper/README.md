# llms-keeper

Keeps `llms.txt` and `llms-full.txt` in sync with the codebase, following the
[llmstxt.org](https://llmstxt.org) standard, so any AI tool starts with the
project's real context instead of guessing it.

Что это, для чего, как пользоваться и когда не пользоваться:
[`docs/plugins/llms-keeper.md`](../../docs/plugins/llms-keeper.md).

## What it ships

- **`/update-docs`** — generate or refresh both context files.
- **`llms-keeper` skill** — the format rules and what belongs in each file.
- **`documentation-keeper` agent** — reads source, config, tests, CI and docs,
  then writes the two files.
- **SessionStart hook** — reports whether context files exist and suggests the
  command when they do not.

## Output

Written to the project root:

| File | Purpose | Size |
|---|---|---|
| `llms-full.txt` | self-contained project context | 200–600 lines |
| `llms.txt` | navigation index | 50–100 lines |

A rerun is incremental: the agent reads git changes since the commit recorded in
the file footer and updates only the affected sections. When that footer is
missing or unparseable it falls back to the last 20 commits.

## Not included in the output

Tutorials and implementation guides, temporary workarounds, `TODO`/`FIXME`,
patterns that appear in a single file, verbose explanations, obvious facts,
debug output, line numbers, open PR/issue status, individual test cases, and any
credentials or secrets.

## Installation

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install llms-keeper@i-m-senior-developer
```

No dependencies on other plugins in this marketplace.

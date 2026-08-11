---
name: plan
description: Build an architecture or execution plan and save it to a file.
argument-hint: "[feature README, architecture file, or task description]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Bash(python3:*)", "Bash(mkdir:*)"]
---

Activate the `planner` skill and follow its workflow start-to-finish.

Interpret `$ARGUMENTS` as follows:

- A path to a feature `README.md`, or a feature directory containing that file, runs **Mode 1 (architecture)** and writes `ARCHITECTURE.md` beside the README.
- A path to an existing architecture document (`*-PLAN-*.md`, `*-DESIGN-*.md`, `ARCHITECTURE.md`, or an explicitly supplied equivalent) runs **Mode 2 (execution)** and writes `PLANNER_EXECUTION.md` beside that document.
- Free text with no readable path runs **Mode 1 (architecture)** and writes `.claude/plans/<task-slug>/ARCHITECTURE.md` under the project root.

A successful run always writes the full result to its target file. Chat output after a successful write contains only:

1. the result kind;
2. the file path and version;
3. two to four main outcomes;
4. the next command, when another step is required.

Never duplicate the full plan in chat after a successful write. If writing the file or synchronizing its metadata fails, state that the result was not saved and emit the complete prepared document to chat as the fallback result.

Do not execute the plan and do not start implementation agents. Use the state helper exactly as described by the skill to synchronize versions and detect stale execution plans.
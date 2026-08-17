---
name: plan-reflect
description: "Reflect on the just-completed plan: compare plan vs reality, update planner-context.md, emit Lessons learned."
argument-hint: "[feature-dir or empty for current session]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Bash(git:*)"]
---

Activate the `planner-reflect` skill and follow its workflow.

Resolve the feature directory from `$ARGUMENTS`:

- If `$ARGUMENTS` is provided — use it as the feature directory.
- If `$ARGUMENTS` is empty — collect candidate directories from paths explicitly used in the current task and from changed paths reported by Git. Keep only candidates containing `PLANNER_EXECUTION.md`.
- Continue only when exactly one candidate remains. If there are none or several, ask for an explicit feature directory and write nothing. Never choose by modification time.

Run the skill end-to-end: gather the five evidence sources, classify findings into the four update types, mask any PII per the skill's PII section, write to `<project-root>/.claude/planner-context.md`, and emit a chat summary that always includes a "Lessons learned" block.

If no `PLANNER_EXECUTION.md` exists anywhere relevant, emit the graceful exit message from the skill's "When evidence is missing" section (`nothing to reflect on; run /plan first`) and stop without writing.

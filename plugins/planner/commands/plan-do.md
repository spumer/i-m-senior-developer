---
name: plan-do
argument-hint: "[feature directory, README, architecture, or execution plan]"
description: Execute a current planner execution file through implementation and review.
allowed-tools: ["Read", "Grep", "Glob", "Bash(python3:*)", "Agent", "Write"]
---

# Task

Orchestrate implementation for: $ARGUMENTS

## 1. Resolve the plan files

Resolve the feature directory from the supplied directory or file. The execution artifact is `PLANNER_EXECUTION.md` in that directory.

Fail before starting any agent when:

- the argument does not resolve to a readable path;
- `PLANNER_EXECUTION.md` is missing or unreadable;
- the execution header does not point to a readable architecture document;
- the architecture and execution paths resolve to the same file.

For a missing execution plan, tell the user to run:

```text
/planner:plan <path-to-architecture>
```

Do not treat a legacy `PLANNER_OUTPUT.md` as the current execution plan.

## 2. Check freshness before every Agent call

Run the state helper before starting any working phase:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py" check <path-to-PLANNER_EXECUTION.md>
```

Interpret its exit status:

- `0` — the plan is current; continue;
- `2` — the plan is stale; stop before Agent;
- `3` — the plan is invalid or unreadable; stop before Agent;
- `64` — the helper invocation is invalid; fix the invocation and rerun it before Agent.

When the plan is stale, report `reason`, the recorded architecture version, and the current architecture version from the helper output. The reason is required even when both versions are equal. Then give the exact rebuild command:

```text
/planner:plan <resolved-architecture-path>
```

Confirmation from the user does not bypass this gate. Re-run the same check immediately before each later Agent call; a long implementation session must not continue after the architecture changes underneath it.

## 3. Execute `PLANNER_EXECUTION.md`

Read the execution plan and map its abstract roles to agents from `.claude/planner-context.md` §1. Do not invent agent names.

For each implementation phase:

1. Start the named **implementer** with the phase inputs and outputs.
2. Include this guard in every dispatched prompt: the feature identifier belongs only in artifact filenames inside the feature directory; never place it in code, comments, docstrings, test names, identifiers, or project documentation outside that directory.
3. After implementation, start the named **reviewer**. The reviewer runs tests and linters, inspects the diff, and writes one issue file per confirmed finding under `review-request-changes/`.
4. If the reviewer finds an implementation defect, dispatch the implementer with the issue files, then repeat review.
5. If the reviewer finds a design defect, dispatch the architect to update the architecture. After that update, stop: the execution plan must be rebuilt before implementation continues.
6. Complete the phase only when review is clean.

Independent phases may run in parallel only when `PLANNER_EXECUTION.md` marks them independent. Keep dependent phases serial.

## 4. Documentation

After all implementation phases are clean, dispatch the documentation keeper named in `.claude/planner-context.md`. It may update only the project documentation paths listed there. Apply the same identifier guard to its prompt.

If no active documentation keeper exists, update only the explicitly listed documentation files yourself; do not invent new project-context files.

## 5. Completion report

Report:

- files changed;
- tests and validation commands actually run, with their outcomes;
- review rounds and remaining limitations;
- whether project documentation changed.

Do not claim a check ran when it was skipped or blocked. Do not commit, tag, push, delete, or publish unless the user separately asks.
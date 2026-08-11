---
name: planner-reflect
description: >
  Reflects on a completed planner execution: compares PLANNER_EXECUTION.md with
  commits, review files, agent runs, and user corrections, then appends stable
  lessons to planner-context.md.
---

# Planner-Reflect — post-task learning

Compare the saved execution plan with what actually happened. Append only supported, reusable lessons to `<project-root>/.claude/planner-context.md`, then return a short `Lessons learned` summary.

Reflection observes completed work. It does not revise the plan, change code, invoke agents, or start another command.

## Evidence sources

Read these sources in order:

1. `<feature-dir>/PLANNER_EXECUTION.md` — planned phases, agents, models, estimates, risks, and gates. This is the required source.
2. `git log` and the changed-file list since the plan — completed work and scope changes.
3. Files under `<feature-dir>/review-request-changes/` — confirmed defects and repeated categories.
4. Agent results available in the current session — retries, escalation, and blocked work.
5. User messages from the current session — explicit corrections to the process or result.

`ARCHITECTURE.md` may be read to distinguish an implementation deviation from an architecture change, but it is supporting evidence, not a sixth independent source.

A legacy `PLANNER_OUTPUT.md` is historical context only. Do not use it as the current execution plan.

## Missing evidence

- No `PLANNER_EXECUTION.md` → return `nothing to reflect on; run /plan on the architecture first` and write nothing.
- No commits or changed files since the plan → return `plan exists but was not executed; nothing to reflect on` and write nothing.
- No current-session agent results → continue with Git, review files, and user messages; state that agent-run evidence was unavailable.
- Any other partial evidence → continue and list the unavailable sources in the summary.

Do not reconstruct a missing plan from Git history.

## Lesson types

Write a lesson only when its trigger is visible in the evidence.

### Agent gap

Trigger: the orchestrator used a generic fallback because `.claude/planner-context.md` had no active agent for the required role or stack.

Destination: agent catalog. Record the missing role, observed fallback, and date. Do not blame the agent or orchestrator.

### Model fit

Trigger: repeated failed attempts, explicit escalation, or several correction commits on the same bounded task.

Destination: model table. Name the task type and this project's context. Avoid categorical claims about a model. One run without a retry pattern is insufficient evidence.

### User correction

Trigger: the user explicitly rejected a process or behavior and supplied the preferred rule.

Destination: project lessons. Record the reusable guard, not the wording or emotional tone of the correction.

### Estimate calibration

Trigger: an estimate recorded in `PLANNER_EXECUTION.md` differs from observed time or token use by more than 30 percent.

Destination: model table or project lessons. Record the numeric difference and task type. Do not invent a cause.

If the execution plan contains no estimate, skip this lesson type rather than fabricating a baseline.

## Write protocol

The only writable file is `<project-root>/.claude/planner-context.md`.

1. Read the current file.
2. Preserve manual text and earlier lessons.
3. Append the smallest new line that captures each supported lesson.
4. End every added line with `<!-- learned YYYY-MM-DD -->`.
5. Do not add the feature identifier to the lesson. The feature directory and Git history retain task traceability.
6. Do not rewrite `ARCHITECTURE.md`, `PLANNER_EXECUTION.md`, review files, code, or memory files.

If the same lesson already exists, do not add a duplicate. When the same pattern has appeared in at least two distinct sessions, ask the user whether to promote it to persistent memory; never create memory without explicit confirmation.

## PII and secret masking

Before writing, mask sensitive fragments in proposed additions:

- email address → `<email>`;
- continuous token-like string of 40 or more characters → `<token>`;
- user segment in home-directory paths → `<user>` while preserving the remaining path.

Never copy raw transcript excerpts. Extract an abstract pattern. If masking removes the useful meaning, skip that lesson and mention the omission in chat.

## Chat output

Always end a completed reflection with:

```text
planner-context.md updated:
- <section and concise change>
- evidence used: <sources>
- evidence unavailable: <sources or none>

## Lessons learned (<task name>, YYYY-MM-DD)
- <lesson>
```

If evidence supports no addition:

```text
## Lessons learned (<task name>, YYYY-MM-DD)
_no actionable lessons this session_
```

Keep the summary within one terminal screen. Empty is valid; never invent a lesson to make the run look useful.
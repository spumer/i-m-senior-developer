# Mode 1 — Architecture

Load this reference when the input is a feature `README.md`, a feature directory containing one, or free text with no readable path.

## Result

Produce a ready architecture document, not a plan for running an architect later.

- Feature input → `<feature-dir>/ARCHITECTURE.md`.
- Free text → `<project-root>/.claude/plans/<task-slug>/ARCHITECTURE.md`.

Prepare the body in the transient file required by the main skill. The state helper atomically stores that body with its synchronized YAML header.

## Inputs

Read:

1. the requirements or free-text task;
2. the existing `ARCHITECTURE.md`, if present;
3. the neighboring `PLANNER_EXECUTION.md`, if present;
4. project conventions named in `.claude/planner-context.md`.

A legacy `PLANNER_OUTPUT.md` may provide historical context, but it is never the current architecture or execution plan. Preserve it unchanged.

If the input lacks a goal, affected user, or acceptance criteria, stop and name the missing information. Do not fill the gap with guesses.

## Complete architecture file format

The saved `ARCHITECTURE.md` is the following YAML header and Markdown body concatenated in this order, without the code fences. The planner writes only the body to `ARCHITECTURE.md.prepared`; `plan_state.py` fills the dynamic header values and atomically assembles the saved file.

### YAML header template

```yaml
---
plan_type: architecture
version: 1
status: current
content_sha256: <SHA-256 of the body>
---
```

`version` is the helper-managed non-negative integer for the current semantic revision. Architecture status is always `current`. `content_sha256` is the 64-character hexadecimal fingerprint of the normalized body and excludes this header.

### Markdown body template

Use this body structure unless the project has a stronger architecture convention:

```markdown
# <task name> — Architecture

## Context and scope
<what changes and what stays outside the task>

## Bounded contexts
<each context, its responsibility, and its boundary>

## Contracts
<input, output, side effects, and explicit error behavior for each hand-off>

## Data flow
<ordered flows through the contexts>

## Decisions
<committed decisions and their evidence>

## Verification boundaries
<observable or machine contracts that implementation must prove>

## Risks
<risk and concrete mitigation>

## Open questions
<unresolved decision and its owner, or an explicit statement that none remain>

## Hand-off
<input expected by execution planning>
```

A directory tree alone is not architecture. Name responsibilities and contracts before listing files.

## Update rules

1. Compare the new body with the existing body.
2. Pass `--semantic-change yes` when decisions, contracts, data flow, scope, or verification boundaries changed.
3. Pass `--semantic-change no` when the result is unchanged or only wording/formatting changed.
4. Never increment a version manually. The state helper applies the decision.
5. After synchronization, check the neighboring execution plan with `--mark-stale`.

If the architecture was previously a headerless legacy document and this run actually updates it, it becomes version 1. Merely reading that document for execution planning leaves it unchanged at version 0.

## Completion

Successful chat output names:

- `ARCHITECTURE.md` path;
- current version;
- two to four decisions or boundaries;
- whether `PLANNER_EXECUTION.md` became stale;
- the exact execution-planning command when a rebuild is needed.

Do not paste the architecture body into chat after a successful write.